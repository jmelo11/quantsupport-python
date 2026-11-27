Risk, netting, and extensibility
================================

Sensitivity labels define the experiment
----------------------------------------

A sensitivity measures how a value changes for a small move in one market
input. In a bootstrapped market, the input can be a deposit, swap, or
volatility quote. In a curve given directly as zero rates, it is the zero-rate
quote. A bond spread can also be an input of its own.

The pillar label names the input. The input's units tell you how to turn the
derivative into a change in money. Check those units, and the valuation
currency, before you add up a portfolio risk report.

For a small move in the inputs,

.. math::

   \Delta V \simeq \sum_k \frac{\partial V}{\partial q_k}\Delta q_k.

Scaling depends on the input:

- For a decimal rate, multiply the derivative by :math:`10^{-4}` to get the
  approximate change in money for +1 bp.
- For a lognormal volatility quoted as a decimal, one volatility point is
  usually a move of 0.01.
- A futures price moves in price points.

Do not apply one scaling to every row. Curve sensitivities also include the
derivatives of the curve calibration. Compare selected sensitivities with full
revaluation to check how good the linear approximation is.

The next check reuses ``context`` and ``trade`` from :doc:`first-valuation`.
It shifts both SOFR zero-rate quotes up and down, revalues the trade, and
compares the central difference with the sum of the two sensitivities.

.. code-block:: python
   :name: guide-python-scenario

   import math

   h = 0.00001
   up = qs.Scenario(shocks=[qs.Shock(
       target="SOFR", value=h, shock_type=qs.ScenarioType.Absolute,
   )])
   down = qs.Scenario(shocks=[qs.Shock(
       target="SOFR", value=-h, shock_type=qs.ScenarioType.Absolute,
   )])
   with context:
       base_result = context.evaluate(trade, ["Value", "Sensitivities"])
       parallel_derivative = base_result.sensitivities["value"].sum()
       with up:
           up_value = context.evaluate(trade).price
       with down:
           down_value = context.evaluate(trade).price
       restored_value = context.evaluate(trade).price
   finite_difference = (up_value - down_value) / (2 * h)
   assert math.isclose(parallel_derivative, finite_difference, rel_tol=2e-5)
   assert math.isclose(restored_value, base_result.price, abs_tol=1e-8)
   print("Approximate +1bp change:", parallel_derivative * 0.0001)

How scenarios work:

- Enter the context first, then the ``Scenario``. The innermost active context
  provides the base market.
- Shocked curves and other objects are built separately, so the base market is
  not changed.
- Nested scenarios apply in the order you enter them.
- When a scenario exits, even because of an exception, the previous market
  comes back.
- You can reuse a scenario that is not active with another context.
- Do not keep curves or other market objects from a scenario after it ends.

An Absolute shock adds a value in the target's units. A Relative shock
multiplies by ``1 + value``.

A target selects quotes as follows. If it equals a quote identifier, that quote
matches. Otherwise the target is split at underscores, and a quote matches if
its identifier contains all of those parts (set membership, ignoring case,
order, and repeats). So a full identifier is **not an exact-only selector**.
Because repeated tenor or expiry parts are ignored, one full caplet identifier
can also select a caplet with another expiry. Overlapping shocks are all
applied in order, without deduplication, so one quote can move twice.

To move a whole family once, use one target for the family, for example
``CapletFloorlet_USD_SOFR`` instead of one shock per caplet. For a quoted
funding spread curve, ``OTHER:FUNDINGSPREAD`` selects its zero-rate quotes.
Adding a pillar narrows the match but still does not make it exact.

Inspect every transformed quote, including unexpected matches. Check that each
intended input moves exactly once before you treat a stress as a parallel
market move. A change in total NPV alone cannot show a quote that moved twice
or moved by mistake.

Changing the curve risk basis
-----------------------------

You can report curve risk against different inputs from the ones used to
build the curve:

- ``PricingContext.reproject_risk(instruments)`` reports risk against the
  implied quotes of another set of calibration instruments.
- ``with_zero_rate_risk(grids)`` reports risk against zero rates implied by the
  curve's discount factors.

Both return a ``RiskContext``. It has the usual ``evaluate()``, portfolio, and
curve query methods. Pricing still uses the original curves and interpolation,
so values do not change.

This example reuses ``context``, ``reference``, and ``trade`` from
:doc:`first-valuation`. Its zero-rate dates cover both original zero-rate
inputs, including the rate at the start of the curve.

.. code-block:: python
   :name: guide-python-risk-basis

   requests = [qs.Request.Value, qs.Request.Sensitivities]
   with context:
       original = context.evaluate(trade, requests)
       projected = context.reproject_risk([
           "OIS_USD_SOFR_1Y", "OIS_USD_SOFR_10Y",
       ])
       zero_context = context.with_zero_rate_risk([qs.ZeroRateRisk(
           "SOFR", dates=[reference + "1Y", reference + "10Y"],
           day_counter="Actual365", compounding="Continuous", frequency="Annual",
       )])

   for view in [projected, zero_context]:
       with view:
           result = view.evaluate(trade, requests)
           assert result.price == original.price
           assert set(result.sensitivities["pillar"]) == set(view.target_labels)
           print(list(zip(view.target_labels, view.target_values)))
           print(result.sensitivities)

A ``RiskContext`` keeps its own copy of its inputs and registered Python
pricers, so you can use it after the original context's ``with`` block ends.

- You cannot assign market inputs on a ``RiskContext``; that raises an error.
  Change the original context and create a new ``RiskContext``.
- A ``Scenario`` entered on a ``RiskContext`` shocks its source market and
  recalculates the new risk inputs. Both are restored when the scenario exits.
- A ``RiskContext`` created inside a scenario keeps that scenario's quotes.

The target instruments need no quotes in the quote store; their quotes are
solved from the original curves. Read ``source_labels``, ``target_labels``, and
``target_values`` to see the mapping.

Coverage rules:

- Target instruments must cover all discount and forward curve risk.
- Zero-rate grids must cover their selected curves and the curves those depend
  on.
- If the targets do not cover the risk, or the mapping is singular, an error
  is raised.
- If there are more targets than needed, risk is spread across them with the
  smallest Euclidean norm, in the target quote units.

``ZeroRateRisk`` defaults to Actual365, Continuous compounding, Annual
frequency, and the future nodes of the selected curve. Its optional ``dates``
accept ``Date``, ``datetime.date``, or ISO date strings. Multiply a decimal
zero-rate derivative by ``1e-4`` to estimate the P&L of +1 bp. Other risk
factors are reported as before. The mapping is linear and local. It does not
add model or simulation dependencies that the original pricer does not have.

This also works for a curve built from ``DiscountFactor`` quotes. The default
grid uses the curve's future nodes, so you need no extra zero-rate curve or
quotes:

.. code-block:: python

   with context:
       zeros = context.with_zero_rate_risk([qs.ZeroRateRisk(
           "ESTR", day_counter="Actual365", compounding="Continuous",
           frequency="Annual",
       )])
   with zeros:
       result = zeros.evaluate(portfolio, [qs.Request.Value, qs.Request.Sensitivities])
       report = result.sensitivities
       zero_rows = report["pillar"].str.startswith("ZeroRateRisk_")
       report.loc[zero_rows, "pv01"] = report.loc[zero_rows, "value"] * 1e-4

Use the index of the discount curve that the pricing policy selects. For a
composite curve, or a curve without nodes, pass future ``dates`` to
``ZeroRateRisk``. Custom dates must cover the curve's risk. If they do not, an
error is raised; no exposure is dropped.

A complete example is in ``examples/sensitivity/risk_reprojection.py``. Run it
from the repository root with a package built from this checkout:

.. code-block:: sh

   python examples/sensitivity/risk_reprojection.py

Portfolio aggregation
---------------------

Two notebooks cover portfolios:

- :doc:`How a portfolio works <../studies/notebooks/portfolio>` covers which
  trades a portfolio holds, position sizes, which requests it supports, and
  currency conversion. It checks the portfolio's PV, sensitivities, and
  payments against the individual trades, and checks rate risk by full
  revaluation.
- The :doc:`portfolio aggregation notebook <../studies/notebooks/portfolio-aggregation>`
  values a six-position deposit and swap book with
  ``context.evaluate(qs.Portfolio("PORTFOLIO", trades), requests)``, which
  returns a standard ``EvaluationResults``. It checks the PV, every
  sensitivity, and the totals per payment date against individual valuations.
  It can also export five tables as CSV files.

A ``Portfolio`` is an ordered list of trades. The context values it with
``PortfolioPricer``, which supports Value, Sensitivities, and Cashflows and
values each trade with that trade's own pricer.

Built-in pricers convert values and sensitivities to the context's base
currency with its FX store, including FX sensitivities, before adding them up.
Cashflow reports keep the original currencies.

``result.cashflows`` keeps coupon types, accrual dates, contractual and
effective fixing indices, and signed notionals. Compatible coupons are merged
with weighted rates or spreads. In the notebook, the two deposits combine into
400,000 at 5.5%. SOFR and TermSOFR3m coupons, and coupons with opposite
directions, stay separate. ``result.cashflow_summary`` gives interest, capital,
other, and total amounts per payment date. It does not spread interest over
accrual periods. Sensitivities are calculated trade by trade and then added.

To combine results, value each ``Trade`` under the same market assumptions,
then add up values and risk labels that are compatible. Two opposite positions
in the same contract cancel only after side and size are applied; their
unsigned cashflow amounts need not cancel. Adding cashflows in different
currencies does not give a portfolio PV in the reporting currency.

``EvaluationResults.sensitivities`` adds up rows with the same label and sorts
known tenors and pillar dates from shortest to longest, so 2Y comes before 10Y.
Labels without a known maturity come after the dated pillars.
``raw_sensitivities`` keeps the original rows in their original order.

For a portfolio risk report:

- Keep the trade identifier next to each trade's table before grouping by
  pillar.
- Keep the model and input units in the report.
- Compare the summed linear prediction with a full revaluation under the same
  scenario. Large shocks, options, calibration changes, and exercise boundaries
  make the linear prediction less reliable.

Exposure profiles and netting
-----------------------------

``NettingSet`` groups trades under one client's ``CsaTerms``. XVA supports
these products:

- ``Swap``
- ``CrossCurrencySwap``
- ``BasisSwap``
- ``FixFloatCrossCurrencySwap``
- ``FixedRateBond``
- ``FloatingRateNote``
- ``FixedRateDeposit``

Other products that the context can value, such as loans, callable bonds,
options, and trades with custom Python pricers, are not supported in XVA.

For the value :math:`V_p(t_i)` on path :math:`p` at date :math:`t_i`, the
stored profiles are averages at each date:

.. math::

   \operatorname{EPE}(t_i)&=\frac{1}{P}\sum_p\max(V_p(t_i),0),\\
   \operatorname{ENE}(t_i)&=\frac{1}{P}\sum_p\min(V_p(t_i),0),\\
   \operatorname{EE}(t_i)&=\operatorname{EPE}(t_i)+\operatorname{ENE}(t_i).

ENE is signed and never positive. The profiles are not PFE quantiles or
averages over time. Each value is in the engine's base currency at its future
simulation date, before variation margin. The profiles are not discounted and
are not adjustment PVs.

The example below puts the swap in a netting set and runs an XVA calculation
with variation margin. It uses only eight paths so that it runs quickly. For a
real study, increase the path count and compare different seeds.

.. code-block:: python
   :name: guide-python-xva

   xva_configuration = qs.XvaConfig.from_dict({
       "model_configs": [{
           "market_index": "SOFR", "lambda": 0.05,
           "parameter_source": {"Fixed": {"sigma": 0.005}},
       }],
       "n_paths": 8, "seed": 42, "frequency": "Quarterly",
   })
   terms = qs.CsaTerms(
       collateral_index="SOFR", collateral_currency="USD",
       credit_spread=0.01, recovery=0.40, funding_spread=0.005,
       variation_margin=True, counterparty_threshold=1000,
       own_threshold=1000, minimum_transfer_amount=500,
   )
   agreement = qs.NettingSet("CLIENT-A", [trade], terms)
   with context:
       adjustments = context.run_xva(xva_configuration, [agreement])
   print(adjustments.xva_values)
   profile = adjustments.exposures[0].to_dataframe()
   assert (profile["ee"] - profile["epe"] - profile["ene"]).abs().max() < 1e-8

``run_xva`` calculates CVA and FVA. It does not return DVA.

With a flat credit spread :math:`s_c` and recovery :math:`R`, the hazard rate is
approximated as :math:`\lambda=s_c/(1-R)`, not :math:`\lambda=s_c`. A
configured credit curve instead gives a bootstrapped survival curve.

FVA uses the signed path value, not only EPE. Each time step is measured in
ACT/365 and uses the value at the end of the step. Optional system discounting
and the variation margin are applied in the FVA calculation. In outline,

.. math::

   \operatorname{FVA}
   \simeq \mathbb{E}\left[\sum_i
   D_{\mathrm{sys}}(0,t_i)\,s_f(t_i)\,
   \widetilde V_p(t_i)\,\Delta_i\right],

where :math:`\widetilde V` is the value after the margin is applied.
Variation margin changes the CVA and FVA, not the stored exposure profiles,
which are before margin. Where configured, a funding-spread zero curve can be
added on top of a funding index. There is no separate ``FundingSpreadCurve``
class.

Read XVA sensitivity labels carefully:

- With ``credit_index``, CVA sensitivities are with respect to the survival
  probabilities at the credit curve's nodes. A ``CVA.<label>`` row is
  :math:`\partial\mathrm{XVA}/\partial S(T_k)`, even when the label looks like a
  CDS quote. It is not a sensitivity to the CDS spread, because the credit
  curve's calibration is not included.
- With a funding curve, FVA sensitivities (prefixed ``FVA.``) are with respect
  to the derived funding-spread pillars, not the original funding quotes. The
  funding curve's calibration is not included either.
- Flat ``credit_spread`` and ``funding_spread`` parameters keep their decimal
  rate units.

Do not scale a survival-probability sensitivity as if it were a CDS-spread
DV01. Ordinary CDS pricing calculates its sensitivities separately; read them
on their own terms.

System/base discount factors used in the XVA calculation are numerical
snapshots held fixed, so they contribute no system-curve risk.
Calibrated sigma also omits curve/strike recalibration terms.
Treat the returned sensitivities as partial risks. Check a proposed hedge with a full market revaluation; do not
treat a quote-like label as a full derivative with respect to that market
quote.

Thresholds, minimum transfer amount, recovery, credit and funding indices, and
the model, path, and date grid are all economic or numerical assumptions.
Netting-set names must be unique within one run. Fixed seeds make comparisons
reproducible. Vary the path count and seed to check whether a change for a
client is larger than the sampling noise. The
:doc:`XVA notebook <../studies/notebooks/xva>` works through such a comparison.

Extending valuation in Python
-----------------------------

You can add your own products and pricers in Python:

- ``Instrument`` holds the contract terms.
- ``Trade`` holds a position.
- ``Pricer`` implements the valuation.
- ``MarketDataProvider`` supplies the market data the pricer needs.
- ``Evaluator`` picks the pricer for a trade.

Ordinary Python classes and dataclasses with the right methods also work. Your
implementation is responsible for side, position size, requests, units, and
which cashflows it includes.

This example prices a fixed USD receipt with the market from the first
valuation.

.. code-block:: python
   :name: guide-python-extension

   class Receipt(qs.Instrument):
       def __init__(self, identifier, maturity, amount):
           super().__init__(identifier)
           self.maturity = maturity
           self.amount = amount

   class ReceiptTrade(qs.Trade):
       pass

   class ReceiptPricer(qs.Pricer):
       def evaluate(self, trade, requests, context):
           instrument = trade.instrument
           size = trade.notional if trade.notional is not None else 1.0
           value = (
               instrument.amount * size * trade.side.sign()
               * context.curve("SOFR").discount_factor(instrument.maturity)
           )
           return qs.EvaluationResults(
               context.evaluation_date, instrument.identifier,
               price=value if qs.Request.Value in requests else None,
           )

   receipt = Receipt("RECEIPT", reference + "1Y", 100)
   receipt_trade = ReceiptTrade(receipt, reference)
   context.register_pricer(ReceiptTrade, ReceiptPricer())
   with context:
       custom_result = context.evaluate(receipt_trade, ["Value"])
       print(custom_result.price)
   context.unregister_pricer(ReceiptTrade)

How registered pricers are chosen:

- The context looks for a pricer registered for the exact trade type, then for
  its base classes.
- Pricers registered in Python take precedence over built-in pricers.
- Register the trade type, not the instrument class.
- A trade subclass that is not registered and holds a built-in instrument is
  priced by the built-in pricer.

A standalone ``Evaluator`` can use your own market data provider. You do not
need to subclass every base interface.

This pricer returns only Value. Any other measure needs its own implementation
and testing. Sensitivities are not calculated automatically for Python code,
and XVA supports only the built-in products listed above.
