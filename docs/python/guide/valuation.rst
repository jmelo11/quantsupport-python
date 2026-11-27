Valuation, quotation, and model choice
==========================================

Each product has its own quotation conventions and supported measures.
``Value`` gives the PV in money. ``FairRate`` gives the product's breakeven rate
or price. Bond valuations also need a price or spread anchor.

The examples below reuse ``reference`` and ``context`` from
:doc:`first-valuation`. Enter the context again for each calculation; it
rebuilds market objects as needed.

Build products explicitly
-------------------------

A maker stores the parameters for a product and builds it with ``build()`` or
``build_using(context)``. Both return the same product type.

- ``maker.is_resolved()`` tells you whether all dates and required market
  observations are known.
- ``build()`` checks this first. If something is missing, it raises
  ``UnresolvedProductErr``. The message names the missing input and explains
  how to supply it or to call ``build_using(context)`` instead. When nothing is
  missing, the contract terms are then validated as usual.
- Use ``build_using(context)`` when dates are given as tenors, including a
  maturity tenor with an explicit start date.

.. code-block:: python

   maker = qs.MakeSwap(
       identifier="spot-5y", start_tenor="0D", tenor="5Y",
       notional=1_000_000, fixed_rate=0.03, currency="USD", market_index="SOFR",
   )
   with context:
       instrument = maker.build_using(context)
       trade = qs.Trade(instrument, context.evaluation_date)
       result = context.evaluate(trade)

You can reuse the maker. The built instrument keeps its dates and contractual
principal across valuations and scenarios. ``evaluate`` takes built trades; it
does not build products or choose trade dates. To set a trade date relative to
the context date, use ``MakeTrade(..., trade_tenor="0D").build_using(context)``.

Tenor parameters by product:

- scheduled products: ``start_tenor`` and ``tenor``;
- options: ``expiry_tenor``;
- forwards: ``delivery_tenor``;
- swaptions: ``expiry_tenor`` and the underlying ``tenor``.

Give either a date or a tenor for a field, not both.

With ``PricingContext(anchor_fixings=True, ...)``, every index fixing strictly
before the evaluation date must be stored. Fixings from today onward are
projected from the curve, even if today's fixing is stored. Set
``context.anchor_fixings = False`` to project all fixings; the curve must then
cover those observation dates.

A floating-rate amortizing loan needs an explicit ``amortization_rate``, or it
must be built with ``MakeLoan(...).build_using(context)``. During the build, the
first index fixing, spread, and payoff set the principal schedule. A missing
past fixing makes the build fail. A saved Python loan keeps this first
amortization rate, so it can be rebuilt without a context.

Rates and direction
-------------------

Vanilla swaps, basis swaps, both kinds of cross-currency swap, deposits, and
floating-rate notes take contractual schedules and rate conventions. To project
their coupons, the context needs the index curves and any past fixings. Each
constructor documents its leg order and what the receive and pay sides mean.
Use that to set the position's direction.

Position size:

- ``Trade.notional`` sets the position size without changing the instrument,
  which other trades may share.
- Cross-currency trades have separate domestic and foreign overrides.
- Futures trades use ``num_contracts``.
- Sizes must be finite and not negative.
- FX forwards, equity forwards, options, CDS, and caplets have no notional in
  their Python product terms. The trade sets their size, which usually defaults
  to one.

For rate futures, a price of 95.25 means an annual decimal rate of 0.0475.
``contract_size`` is in currency per **price point**, not per basis point. The
default of 2500 means 25 currency units for a 0.01 price change, before
applying the number of contracts and the side. Do not pass a futures price to
an argument that expects a decimal interest rate.

An ``InterestRate`` holds one rate and its quotation conventions. It is not a
curve. Use its compound and discount factor methods for that rate, and a
curve's forward-rate query for market forward rates.

Straight bonds: price is a quotation convention
---------------------------------------------------

The bond instrument holds the coupon, principal, schedule, and currency. The
trade holds the observed quote and the valuation choices: ``pricing_anchor``,
``settlement_date``, and ``spread_day_counter``. The anchor is required. A
missing anchor is not treated as a zero spread.

The next example finds the continuously compounded Z-spread that matches a
clean price of 99.25. Clean and dirty prices are in the bond's quotation units,
normally per 100. The returned ``price`` is the PV in money. The dirty price
includes accrued interest; the clean price does not.

.. code-block:: python
   :name: guide-python-bond

   bond = qs.FixedRateBond(
       "USD-BOND", reference, reference + "5Y", 1_000_000,
       0.04, "USD", day_counter="Actual360",
       compounding="Simple", rate_frequency="Annual",
       payment_frequency="Semiannual",
   )
   bond_trade = qs.Trade(
       bond, reference,
       pricing_anchor=qs.BondPricingAnchor.clean_price(99.25),
       settlement_date=reference,
   )
   with context:
       bond_result = context.evaluate(bond_trade, [
           "Value", "YieldToMaturity", "ModifiedDuration",
           "ZSpread", "Sensitivities",
       ])
       print(bond_result.price, bond_result.z_spread)
       print(bond_result.yield_to_maturity, bond_result.modified_duration)

Other anchors:

- ``BondPricingAnchor.z_spread(0.0)`` values the bond on the curve with no
  spread.
- ``dirty_price(...)`` anchors to a price that includes accrued interest.

``with_pricing_anchor`` returns a new trade; the bond's cashflows do not change.
Curve sensitivities and the ``<identifier>.ZSpread`` sensitivity are separate
risk factors. A spread implied from a price is a calibration result, not a
second market quote.

The context's fixed-income discount policy maps each currency to a curve. With
``prefer_instrument_index=True``, a straight product whose contract names a
discount index uses that index instead. With ``False``, the currency mapping
always applies. A payment currency without a mapping raises an error.

Issuer-callable stepped bonds
---------------------------------

Use ``SteppedCouponBond`` for stepped coupons, amortization, and issuer calls.

- Coupon templates and outstanding-notional percentages apply to periods in
  order. The last entry repeats for all later periods.
- ``PayoffOps`` builds coupon formulas, for example a geared floating coupon
  with a floor and a cap. Saved coupons keep the formula.
- Each call has a strike and either a single date or a date window that
  includes both ends.
- On an exercise date, the coupon and amortization due that day are paid, and
  the call strike caps the remaining value.
- Call strikes are in the bond's price units, not decimal interest rates.

Choose ``TreeBased`` or ``BackwardFourierEvolution`` in a
``PricerConfiguration`` with a Hull–White model. The configuration below uses a
tree with fixed mean reversion and short-rate volatility.

.. code-block:: python

   tree_configuration = qs.PricerConfiguration.from_dict({
       "instrument_type": "SteppedCouponBond",
       "pricer": {"TreeBased": {"time_grid": {
           "steps_per_year": 48, "max_steps": 4096,
           "day_counter": "Actual365",
       }}},
       "models": [{"market_index": "SOFR", "model": {"HullWhite": {
           "alpha": 0.05, "parameter_source": {"Fixed": {"sigma": 0.01}},
       }}}],
   })

Anchors for this bond:

- With calls, use ``BondPricingAnchor.OAS(0.0)`` for the model value at zero
  OAS, or a clean or dirty price anchor to solve for the OAS.
- Without calls, use a Z-spread anchor.

Yield to maturity and modified duration are not available for this product.
The tree or Fourier grid and the model are numerical assumptions. Record their
convergence and calibration checks with the valuation. The
:doc:`callable-bond notebook <../studies/notebooks/callable-bond>` works
through these choices.

Loans: contractual principal and expected receipts
------------------------------------------------------

A loan keeps its contractual repayment schedule separate from the valuation
of prepayment and default.

- Specify a ``LoanRepaymentStructure`` and one or more coupon templates.
- Choose the discount curve with the context's discount policy. Loans have no
  ``discount_index`` field.
- French amortization sets the principal schedule from the first amortization
  rate. Later changes in floating coupons do not change that schedule.

Set the day count on each coupon. A floating coupon uses its ``day_counter``,
or the index convention if you leave it out. A fixed coupon uses the day
counter of its ``InterestRate``. The loan uses the same convention to amortize
principal. ``Loan`` has no ``day_counter`` argument.

French payments stay level until the first reset if ``amortization_rate``
equals that reset's all-in rate, including spread and payoff bounds. Later
resets can change payments without changing principal.

.. code-block:: python
   :name: guide-python-loan

   loan = qs.Loan(
       "USD-LOAN", reference, reference + "2Y", 100_000,
       [qs.FixedRateCoupon(rate=qs.InterestRate(
           rate=0.06, day_counter="Actual360",
       ))],
       "USD", repayment=qs.LoanRepaymentStructure.bullet(),
       payment_frequency="Quarterly",
       prepayment=qs.PrepaymentModelConfiguration.constant_annual_cpr(0.10),
   )
   original_terms = loan.to_dict()
   with context:
       loan_result = context.evaluate(
           qs.Trade(loan, reference),
           ["Value", "Cashflows", "Sensitivities"],
       )
       print(loan_result.price)
   assert loan.to_dict() == original_terms

``Value`` is the signed PV of future expected receipts, **excluding the
initial advance**. To get a lender's NPV at origination, account for the
advance separately.

The loan cashflow report has its own layout. Scheduled receipts are leg 0,
prepayment receipts leg 1, and recovery receipts leg 2. Do not read it like
the generic swap cashflow table.

Prepayment can be none, a constant annual CPR, or driven by the refinancing
incentive. The refinancing model needs ``refinancing_benchmark_index`` in the
context's ``PricerConfiguration.loan(...)``. The benchmark is an index rate;
it does not include the spreads or fees of a replacement loan.

Payment frequency, reset frequency, fixing lag, and observation tenor are
separate contract inputs. ``coupon_fixing_requests()`` lists the past fixings
the loan needs. You must supply them; they are not projected.

``Request.FairRate(index)`` solves for the rate or spread of one coupon
segment and returns it in ``fair_rate``:

- ``index`` is the zero-based position of a continuous segment of coupons or
  spreads.
- Earlier segments are solved first. For each, the loan is cut short at the
  segment end and the remaining capital is repaid. Their solved rates are then
  kept fixed while the requested segment is solved.
- Mixed and stepped schedules follow the same rule.
- The original contract does not change.
- Each evaluation solves one segment. An invalid index, or a coupon with a cap
  or floor, raises an error.
- Each segment's rate is searched between -5% and 50%.

``rebuild_amortization_for_fair_rate`` controls principal during the search:

- ``False`` keeps the principal schedule fixed for each trial rate.
- ``True`` rebuilds the amortization for each trial rate. The original contract
  still does not change.

Choose ``True`` if the new coupon should also change the principal repayments.
Set these options in the pricer configuration and value the loan with
``context.evaluate(...)`` as usual:

.. code-block:: python

   context.pricer_configurations = [qs.PricerConfiguration.loan(
       rebuild_amortization_for_fair_rate=True,
       refinancing_benchmark_index=qs.MarketIndex.SOFR,
   )]
   with context:
       par = context.evaluate(qs.Trade(loan, reference), [qs.Request.FairRate(0)])

Loan trades are valued with ``LoanPricer``, also inside portfolios and
scenarios. Discounting follows ``context.fixed_income_policy``. Without a loan
configuration, the defaults are no refinancing benchmark and a fixed principal
schedule during fair-rate solves. The :doc:`loan notebook <../studies/notebooks/loans>`
compares these settings.

Options, calibration, and simulation
------------------------------------

Each option type has its own pricer and market inputs:

- caps, floors, caplets, and floorlets use Black pricing;
- a European equity option needs its spot fixing and its forward and dividend
  conventions;
- a European swaption needs an explicit ``EuropeanSwaption`` and
  ``HullWhiteClosedForm`` pricer configuration.

This swaption example reuses the simple curve market with a fixed absolute
short-rate sigma. It illustrates the model; it is not calibrated to a
volatility surface.

.. code-block:: python
   :name: guide-python-swaption

   model_configuration = qs.PricerConfiguration.from_dict({
       "instrument_type": "EuropeanSwaption",
       "pricer": "HullWhiteClosedForm",
       "models": [{"market_index": "SOFR", "model": {"HullWhite": {
           "alpha": 0.1, "parameter_source": {"Fixed": {"sigma": 0.01}},
       }}}],
   })
   context.pricer_configurations = [model_configuration]
   swaption = qs.EuropeanSwaption(
       "PAYER-1Y5Y", reference + "1Y", reference + "6Y",
       0.03, 1_000_000, "USD", "SOFR", swaption_type="Payer",
   )
   with context:
       option_result = context.evaluate(
           qs.Trade(swaption, reference), ["Value", "Sensitivities"],
       )
       print(option_result.price)

To calibrate instead, replace the fixed parameter source with
``Calibrated``. Choose ``Surface`` or ``Cube`` and an explicit calibration
basket, and give the context that surface's or cube's quotes and configuration.
A cube basket selects one tenor per expiry. The quote side and strike-range
policies apply during calibration and to later volatility lookups.

Use absolute numeric strikes, as in the example. A ``Relative`` strike in a
dictionary means different things in different places:

- the generic ``Strike.resolve`` helper uses :math:`K=F+\mathrm{offset}`;
- Black and Hull–White cap and caplet pricers use :math:`K=F(1+\mathrm{pct})`.

So a caplet given ``{"Relative": 0.10}`` turns a 4% forward into a 4.4% strike,
not a 14% strike. Do not apply the equity and FX helper's rule to rate options.
The coordinates used to look up volatility can also differ from the payoff
strike. Check both before comparing valuations.

A built Hull–White simulation can report calibration diagnostics: identifier,
expiry, times ``t`` and ``big_t``, market volatility, market and model prices,
calibrated sigma, forward, strike, and the signed ``price_error`` (model minus
market). Simulations with fixed parameters or other models may report none.

Simulated paths are stored as plain numbers. They do not keep the calibration
inputs and carry no sensitivities to spot or volatility. This differs from
the ``LgmMarketModel`` calculations used by scripting and XVA. The
standalone Hull–White path generator uses Euler steps and requires a positive
alpha. To check discretization error, refine the time grid. To check sampling
error, compare different path counts and seeds. The LGM model also supports a
zero lambda.

Coupon interest between two dates
----------------------------------

``Request.AccruedAmount(start, end)`` calculates the interest earned between
two dates. The amount is signed and undiscounted.

- The loan, bond, and linear cashflow pricers look up the fixings they need and
  limit the window to each coupon's accrual period.
- Principal advances and repayments are excluded.
- Amounts are in the context's base currency. A portfolio adds up its members'
  amounts.
- An accrual request does not calculate PV or sensitivities. Valuation and
  sensitivity requests use the full pricing path.

Bond accrual is the contractual coupon interest in currency units. It does not
depend on clean or dirty prices, settlement, or spread calibration. For a
callable bond, accrual assumes all scheduled coupons are paid; it does not
weight them by the chance of an issuer call. An accrual-only request does not
need a callable-bond model.

.. code-block:: python
   :name: guide-python-accrual

   accrual_deposit = qs.FixedRateDeposit(
       identifier="ACCRUAL", start_date=reference,
       maturity_date=reference + qs.Period(1, "Years"),
       notional=1_000_000, rate=0.04, currency="USD", discount_index="SOFR",
       day_counter="Actual360", compounding="Simple",
   )
   accrual_portfolio = qs.Portfolio("ACCRUAL", [qs.Trade(accrual_deposit, reference)])
   with context:
       earned = context.evaluate(
           accrual_portfolio,
           [qs.Request.AccruedAmount(reference, reference + qs.Period(1, "Months"))],
       ).accrued_amount

Window rules:

- Each evaluation takes one window.
- If start equals end, the result is zero.
- If end is before start, the request raises an error.
- For loans, the window must start on or after the context's evaluation date.
  Loan projection does not rebuild past prepayments or coupons that were
  already paid.
- Partial accrual of overnight coupons needs daily fixings and is not
  supported.

For one coupon, ``coupon.accrued_amount(start, end)`` uses the same window
rules. Floating and option-embedded coupons need a known fixing to accrue a
nonzero amount. Each window's amount is the difference in total accrual
measured from the coupon start. As a result, amounts for adjacent windows add
up correctly under 30/360 as well as Actual/360 and Actual/365. Cashflow and
accrual requests do not need to discount past principal advances.

FX, equity, and credit
--------------------------

Use ``MarketIndex.equity("SPX")`` for an equity index and
``MarketIndex.fx_pair("EUR", "USD")`` for a currency pair. A plain string works
only where the API documents a string form.

An equity forward needs a spot fixing on the evaluation date and a forward
curve. Without a dividend curve, dividends are zero.

FX rates are quoted as units of the quote currency per one unit of the base
currency. A market-implied forward and a contracted forward rate are different
values. The FX-forward pricer uses ``spot * df_quote / df_base``. The FX-option
pricer uses its own base and quote carry convention. Do not assume the two
formulas match when checking parity. Before you build a hedge, check the
pricer, the discount policy, and the currency of the result.

A CDS also needs a survival (credit) curve and a recovery rate.
``CreditCurveConfiguration`` bootstraps a credit curve from credit quotes; pass
it to the context as ``credit_curves``. Recovery and spreads are explicit
inputs with their own units. A hazard rate approximated from a flat spread is a
different model from a bootstrapped survival curve.

Scripted payoffs
--------------------

A script describes a payoff as a list of dated events. Variables keep their
values from one event to the next, and payments are discounted with the
script's market model. The example below pays 100 USD in two years under a
zero-volatility model and checks the value against the context curve.

.. code-block:: python
   :name: guide-python-script

   script = {
       "name": "SCRIPTED-PAYMENT", "currency": "USD",
       "result_variable": "note",
       "events": [{
           "date": str(reference),
           "code": 'note = 0; note pays 100 on "2028-02-24";',
       }],
       "models": [{"market_index": "SOFR", "model": {"Lgm": {
           "lambda": 0.05, "parameter_source": {"Fixed": {"sigma": 0.0}},
       }}}],
   }
   with context:
       scripted_values = context.evaluate_script(script, n_paths=8, seed=42)
       expected = 100 * context.curve("SOFR").discount_factor("2028-02-24")
       assert abs(scripted_values["note"] - expected) < 1e-8

``evaluate_script`` returns a dictionary with the average value of each
numeric variable. It does not return sensitivity or cashflow tables.

- Configure a model for the discount index and for each forward index the
  script uses. A missing model is an error; it is not treated as zero
  volatility.
- Model assignments are taken from the context's pricer configurations. The
  simulation configuration overrides them, and models defined in the script
  override both.
- A script in a currency other than the base currency needs an explicit
  discount index.
- Scripts support rate models only. Correlated FX and equity factors are not
  available.

With stochastic models, results also depend on the estimator. A martingale
control can adjust the selected result variable, while the cashflow
diagnostics keep the raw simulated payment PVs. With a finite number of paths,
their sum can differ from the adjusted result. Choose a result variable that
adds up the payments you care about, and judge differences against the
sampling error and your tolerance.

Next, read :doc:`risk` for checks against full revaluation and for exposure, or
open the :doc:`example notebooks <../studies/index>` for larger product and
calibration examples.
