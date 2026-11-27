Constructing and selecting a market
===================================

Index names in strings use a tag and a colon: ``EQ:SPX``, ``FX:EURUSD``,
``CREDIT:ACME``, ``COLL:EUR/USD``, and ``OTHER:MyCurve``. Built-in rate index
names such as ``SOFR`` are case insensitive. Custom names without a tag, and
names in parentheses, are rejected. Use the tagged names in quote identifiers,
for example ``ZeroRate_USD_OTHER:MyCurve_1Y``. Typed Python constructors and
tagged dictionaries use their own documented formats.

From observations to curves
-------------------------------

Building a curve turns observed prices and rates into discount factors and
forward rates. You need two inputs:

- a quote store, which holds the observed quotes and the reference date;
- a curve configuration, which chooses the calibration instruments and the
  numerical conventions.

You can then query the built curve or use it for valuation.

The inputs you choose also decide what sensitivities are reported against. A
bootstrapped curve reports sensitivities to its OIS quotes. A curve given
directly as zero rates reports sensitivities to those rates.

The example below bootstraps a USD SOFR curve from a deposit quote and OIS
quotes. Each identifier encodes the instrument and its market conventions, so
it must follow the library's quote format. It is not a free-form label.

.. code-block:: python
   :name: guide-python-bootstrap

   import quantsupport as qs

   observations = [
       ("FixedRateDeposit_USD_SOFR_1D", 0.04500),
       ("OIS_USD_SOFR_1Y", 0.04837),
       ("OIS_USD_SOFR_2Y", 0.04528),
       ("OIS_USD_SOFR_5Y", 0.04077),
   ]
   bootstrap_quotes = qs.QuoteStore.from_dict({
       "reference_date": "2026-02-24",
       "quotes": [{"identifier": key, "mid": value}
                  for key, value in observations],
   })
   bootstrap_spec = qs.CurveConfiguration(
       market_index="SOFR", quotes=[key for key, _ in observations],
       day_counter="Actual360", interpolator="LogLinear",
       enable_extrapolation=False,
   )
   bootstrap_context = qs.PricingContext(
       bootstrap_quotes, [bootstrap_spec],
       csa_policy=qs.SingleCurveCSADiscountPolicy("USD", "SOFR"),
   )
   with bootstrap_context:
       curve = bootstrap_context.curve("SOFR")
       print(curve.nodes())
       print(curve.pillars())
       forward = curve.forward_rate(
           "2027-02-24", "2028-02-24",
           qs.Compounding.Simple, qs.Frequency.Annual,
       )
       print(forward)

``nodes()`` returns the interpolation dates and their discount factors.
``pillars()`` returns the labeled market inputs, where available. Together they
show how the curve is stored and which inputs drive its sensitivities.

Building a curve may also need other projection or collateral curves. Supply
those curves under the market indices named in the configuration.

The simple forward rate between :math:`T_1` and :math:`T_2`, using the curve's
time basis, is

.. math::

   F(t;T_1,T_2)
   = \frac{D(t,T_1)/D(t,T_2)-1}{\tau(T_1,T_2)}.

The same number means a different rate under a different day counter,
compounding convention, or coupon schedule. Log-linear interpolation of
discount factors gives a different curve shape from linear interpolation of
zero rates. Extrapolation is a modeling choice; set it explicitly and record it.

The bootstrap uses OIS calibration instruments with compounded overnight
coupons. The Python ``Swap`` class uses ordinary coupons with one fixing per
period. Python has no standalone ``OvernightIndexSwap`` class.

Direct curve quotes
-------------------

You can also put discount factors or zero rates directly in a ``QuoteStore``.
List their identifiers in ``CurveConfiguration.quotes`` and keep the default
construction rule:

.. code-block:: python

   direct_quotes = qs.QuoteStore.from_dict({
       "reference_date": "2026-02-24",
       "quotes": [
           {"identifier": "DiscountFactor_USD_SOFR_1Y", "mid": 0.96},
           {"identifier": "DiscountFactor_USD_SOFR_2028-02-24", "mid": 0.91},
       ],
   })
   direct_spec = qs.CurveConfiguration(
       market_index="SOFR", quotes=direct_quotes.identifiers(),
       day_counter="Actual365", interpolator="LogLinear",
   )
   with qs.PricingContext(direct_quotes, [direct_spec]) as context:
       print(context.curve("SOFR").discount_factor("2027-02-24"))

Identifier formats:

- ``DiscountFactor_CCY_Index_Pillar`` for discount factors, which have no units.
- ``ZeroRate_CCY_Index_Pillar[_Compounding[_Frequency]]`` for zero rates, as
  annual decimals.

``Pillar`` is a tenor such as ``1Y`` or an ISO date. Zero rates use
``Continuous`` compounding and ``Annual`` frequency unless the identifier says
otherwise. For example, ``ZeroRate_USD_SOFR_1Y_Compounded_Semiannual`` is an
annual rate with semiannual compounding. The curve configuration sets the day
counter, interpolator, and extrapolation. Discount-factor curves interpolate
the factors; zero-rate curves interpolate the rates.

Rules for direct quotes:

- Pillars are sorted by date.
- Each curve uses one kind of direct quote, one currency, and one rate
  convention. Identifiers must match the curve's market index.
- Do not mix direct quotes and calibration instruments in one curve.
- Dates must be different from each other and on or after the reference date.
- Discount factors must be finite and positive.
- The discount factor at the reference date is one and is added for you. If
  you supply it, it must equal one.
- A discount curve needs at least one pillar after the reference date.

Direct quotes use the selected quote level (Mid, Bid, or Ask). They keep their
identifiers, so scenarios and sensitivities refer to them by name. A direct
curve can be a component of a composite curve or an input to a calibrated
curve. All quote values stay in the ``QuoteStore``; the configuration holds only
identifiers and conventions.

Composite curves and standalone term structures
-----------------------------------------------

``ZeroRateTermStructure`` and ``TenorBasedZeroRateTermStructure`` are
standalone zero-rate curves that you can use on their own. Their defaults are
Actual365, Continuous, Annual, Linear, and no extrapolation. A curve
configuration has different defaults: Actual360, LogLinear, and extrapolation
enabled. Set the conventions explicitly when you move a number between these
APIs. A tenor-based curve can be saved as the equivalent curve with dates.

A composite curve multiplies two component discount factors:

.. math::

   D_{\mathrm{composite}}(t,T)
   =D_{\mathrm{base}}(t,T)D_{\mathrm{spread}}(t,T).

When both components use the same time basis, their continuous zero rates
add. The curves are combined through discount factors; quoted yields are not
averaged.

Configure a composite curve with
``CurveConfiguration.composite(market_index=..., base_index=..., spread_index=...)``
and also supply the configurations of both components. The components are
built first. A circular dependency or a missing component raises an error.

For example, to test loan funding, configure a benchmark curve, a quoted spread
curve identified by ``MarketIndex.other("FUNDINGSPREAD")``, and their
composite. Select the composite through the fixed-income discount policy. Do
not add a discount index to the loan contract.

Quotes, fixings, FX, and policies
-------------------------------------

**Quote levels.** Choose the quote side with ``quote_level=Level.Mid``,
``Bid``, or ``Ask``. The default is Mid. Every quote used to build or calibrate
the market must have the selected side. A missing Bid or Ask value is an error;
Mid is not used instead.

Quote units depend on the instrument. Decimal rates, futures prices, and
volatility quotes are each used in their own units; they are not converted to
a common percentage.

**Fixings.** Past fixings are stored separately from quotes.
``FixingStore.add(index, date, value)`` records a published fixing. A forward
curve projects future resets that have not been observed. If a contract needs
a past fixing that is missing, valuation fails; a zero fixing is not used
instead. A product's fixing calendar and lag are separate from its payment
schedule.

Supply checked historical fixings. If your source has gaps, fill them with a
method you have validated before loading them. Python does not offer the
native ``fill_missing_fixings`` routine, which uses reversed interpolation
coordinates.

**FX rates.** ``FxStore`` holds each rate as units of the quote currency per one
unit of the base currency. For example,
``{"base": "EUR", "quote": "USD", "rate": 1.1}`` means 1 EUR = 1.1 USD. Spot
lookups work directly, inversely, and through a third currency.

Built-in pricers use this store to convert PVs and sensitivities to
``context.base_currency``, and they include the FX conversion risk.
``PricingContext.evaluate`` returns these converted results. Cashflow reports
keep the original payment currencies. If a valuation needs a conversion that
the store cannot provide, it raises an error.

**Discount policies.** Three settings answer different questions:

- ``SingleCurveCSADiscountPolicy`` sets the collateral currency and the index
  that pays interest on collateral. It is used to build curves and value
  derivatives. Cashflows in another currency may need that currency's
  collateral-adjusted curve.
- ``FixedIncomeDiscountPolicy`` maps each currency to a discount curve for bonds
  and loans. It also controls whether an instrument's own index takes
  precedence.
- ``CsaTerms`` describes the credit, funding, and collateral terms of one
  netting agreement.

To compare two valuations, use the same pricers, discount policies, and
reporting currency. Sharing a base currency is not enough.

Volatility and calibration inputs
---------------------------------

A volatility configuration lists the input quotes, the smile coordinates,
and how to build the surface. A built ``VolatilitySurface`` or
``VolatilityCube`` is a read-only object you can query inside the context. It
does not replace the quote store. Rate strikes are annual decimal rates.
Equity and FX strikes are prices in their own currency.

Check the volatility type. A Black (lognormal) volatility, a normal volatility,
and an absolute short-rate sigma are different quantities. Read
``volatility_type`` and ``smile_type`` before you use a surface value. In a
cube, expiry and underlying tenor are separate coordinates.

Surfaces and cubes can have sparse slices and axes with a single point. The
default extrapolation policy is ``Reject``, so every query must fall within the
available slices. An at-the-money calibration strike can fall outside a smile
even when its expiry is covered. Either choose a calibration basket inside the
surface, or set the ``Flat`` policy if that boundary behavior is what you want.

``PricerConfiguration`` chooses the pricing method for an instrument type and
the model for each index. ``SimulationConfiguration`` describes a simulation.
Calibrated Hull–White and LGM models use the selected quote side and the
configured volatility source. A calibrated sigma schedule is a result of the
fit. A fixed ``sigma`` is an input in absolute short-rate units, not an option
volatility percentage.

Native serialization
--------------------

Configurations and products use different dictionary formats:

- For a configuration, ``from_dict`` returns one configuration.
  ``from_dict_list`` returns a list. Where documented, it accepts a single
  object, a list, or a list wrapped in an object with one key.
- For a product, ``from_dict`` calls the product constructor with the
  dictionary's keys as keyword arguments.

Read files with Python's ``json.load`` and pass the data to the matching
``from_dict`` method:

.. code-block:: python

   import json

   with open("quotes.json", encoding="utf-8") as stream:
       quotes = qs.QuoteStore.from_dict(json.load(stream))
   with open("curve_specs.json", encoding="utf-8") as stream:
       curves = qs.CurveConfiguration.from_dict_list(json.load(stream))

In dictionaries, indices with parameters use tagged objects such as
``{"Equity": "SPX"}``, ``{"Credit": "ACME"}``, or ``{"FxPair": ["EUR", "USD"]}``.
In Python code, prefer the typed factories, such as ``MarketIndex.equity("SPX")``,
over display labels.

Historical repricing without look-ahead
---------------------------------------

A historical snapshot records one complete market: its quotes and the curve,
volatility, simulation, and pricer configurations. You select a snapshot by the
time it was recorded. Its valuation date is the reference date of its quotes.
The example below shows the difference; it does not depend on earlier examples.

.. code-block:: python
   :name: guide-python-history

   import quantsupport as qs

   def recorded_market(day, rate):
       observations = qs.QuoteStore.from_dict({
           "reference_date": f"2026-02-{day:02d}", "quotes": [
               {"identifier": f"ZeroRate_USD_SOFR_{tenor}", "mid": rate}
               for tenor in ["0D", "10Y"]
           ],
       })
       specification = qs.CurveConfiguration(
           market_index="SOFR", day_counter="Actual360",
           interpolator="Linear",
           quotes=observations.identifiers(),
       )
       return qs.PricingContext(observations, [specification])

   archive = qs.MarketSnapshotStore()
   for day, rate in [(23, 0.03), (24, 0.031)]:
       snapshot = qs.MarketSnapshot.from_context(
           f"2026-02-{day:02d}T16:00:00Z", recorded_market(day, rate),
       )
       archive.insert(snapshot)
   selector = qs.SnapshotSelector(
       "2026-02-25T08:00:00+00:00",
       rule=qs.SnapshotSelectionRule.Previous, level=qs.Level.Mid,
   )
   selected = archive.select(selector)
   with archive.pricing_context(selector) as historical:
       assert str(historical.evaluation_date) == "2026-02-24"
       assert historical.snapshot_timestamp == selected.timestamp

Selection rules:

- ``Previous`` (the default) picks the latest snapshot at or before the
  requested time. It never picks a later one.
- ``Exact`` requires the times to match.
- ``Closest`` can pick a later snapshot. On a tie it picks the earlier one.

Two snapshots at the same UTC time are an error, even if their time strings use
different offsets. Report the time of the selected snapshot, not the time you
asked for.

A snapshot stores the inputs and rebuilds the market from them when you use
it. Zero rates and discount factors use the selected quote side, like
calibration instruments. FX spots are the same on every side.

Pass fixings separately with ``archive.pricing_context(selector, fixings=...)``.
They are not filtered by publication date. For a historical backtest, supply
only the fixings that were known at each snapshot time.

Next, read :doc:`valuation` to choose requests and models for each product,
or open the :doc:`curve notebook <../studies/notebooks/curves>` for a larger
calibration example.

Forward market contexts
-----------------------

You can create an ordinary pricing context for a future date from today's
market. State how the market should move forward::

    assumptions = qs.ForwardMarketConfiguration(
        "2027-01-05", volatility_roll="ConstantTenor", fixing_roll="Project"
    )
    future = context.advance_to(assumptions)
    with future:
        result = future.evaluate(trade, requests=["Value", "Sensitivities"])

The new context has its own generated quotes, forward FX spots, and projected
fixings for the dates in between. Its evaluation date is the horizon date. Its
curves, volatility grids, models, and simulations are built the usual way. If a
``Scenario`` is active on the source context, the generated quotes include it.
A scenario entered on ``future`` shocks the horizon market instead.

Options:

- ``curve_roll``: ``ImpliedForward`` or ``ConstantTenor``.
- ``volatility_roll``: ``ConstantTenor`` or ``ForwardVariance``.
  ``ForwardVariance`` removes the variance that has elapsed, at the same smile
  coordinate. It raises an error if a forward variance increment is negative.
- ``fixing_roll``: ``Project`` or ``Preserve``.

``from_dict()`` and ``to_dict()`` also give access to per-index overrides,
replacement quotes for given dates, and export grids.
``future.market_advancement_details`` shows the source market and the
assumptions used.

Sensitivities in the future context are with respect to its generated horizon
inputs. To measure sensitivity to today's inputs, shock the source context and
create the future context again. FX spots move to the horizon even when
fixings use ``Preserve``.

To replay a future market later, save its fixings with
``future.fixings.to_dict()`` next to a saved market snapshot, and load them
with ``qs.FixingStore.from_dict()``.

Dividend curves are optional. Pass direct curve configurations as the
context's ``dividend_curves`` input. For example,
``DividendDiscountFactor_USD_EQ:AAPL_1Y`` is a dividend discount-factor quote
for an equity. Its prefix keeps it apart from financing discount factors.
