# Working in Python

The Python package gives you QuantSupport's instruments, market building,
valuation, and risk calculations. The basic workflow is:

1. Build a contract and a trade (your position in it).
2. Configure the market.
3. Value the trade inside a pricing context.

Results are returned as numbers and pandas tables.

You can import classes from their domain package or from the package root.
Both give the same class:

```python
import quantsupport as qs
from quantsupport.pricing import PricingContext, Trade

assert Trade is qs.Trade
```

## A complete market and valuation

This example uses a small set of zero-rate quotes, so it needs no data files.
The rates are continuously compounded annual decimals. The curve configuration
only describes the curve; the curve itself is built when a valuation needs it.

```python
import quantsupport as qs

quotes = qs.QuoteStore.from_dict({
    "reference_date": "2026-01-02",
    "quotes": [
        {"identifier": f"ZeroRate_USD_SOFR_{tenor}", "mid": 0.03}
        for tenor in ["1Y", "5Y", "10Y"]
    ],
})
curve = qs.CurveConfiguration(
    market_index=qs.MarketIndex.SOFR,
    quotes=quotes.identifiers(),
    enable_extrapolation=True,
)
swap = qs.Swap(
    "USD_IRS_5Y", "2026-01-02", "2031-01-02",
    1_000_000.0, 0.035, "USD", "SOFR",
)
position = qs.Trade(swap, "2026-01-02", qs.Side.LongReceive)
context = qs.PricingContext(quotes=quotes, curves=[curve])
with context:
    result = position.evaluate([
        qs.Request.Value, qs.Request.Cashflows(), qs.Request.Sensitivities,
    ])
    print(result.price)
    print(result.cashflows)
    print(result.sensitivities)
```

- An instrument holds the contract terms.
- A `Trade` adds the trade date, the direction, and optional notional
  overrides. Bond trades also need a `BondPricingAnchor`.
- The context picks a suitable built-in pricer for each trade. When the choice
  depends on a model, set it with the context's pricer configurations.
- You can also register pricers written in Python.

## Context lifetime and mutability

Entering `with context:` checks the configuration and makes the context
active. It does not build the whole market at once. Each calculation builds and
caches only the curves and other objects it needs. Call `context.initialize()`
if you want to build everything up front.

`position.evaluate()` uses the innermost active context:

- By default it requests `Value`. Pass a list of requests to get other measures.
- It applies the context's scenarios, registered pricers, and risk views.
- Calling it with no active context raises `RuntimeError`.
- Nested `with` blocks restore the previous context when they exit.

You can also call `context.evaluate(position, requests)` directly.

When the outermost `with` block exits, the context releases the market objects
it built. This also happens when an exception is raised. Keep the returned
results for reporting, but do not use curves or other market objects from the
context after the block ends.

Context inputs have setters. Properties that return collections return copies,
so changing the copy does not change the context. Edit the copy and assign it
back; the context then rebuilds whatever depends on that input.

Contract and result properties are generally read-only. Calculations such as
evaluation, curve queries, and serialization are methods. Date arguments
usually accept `qs.Date`, `datetime.date`, or an ISO date string; each
signature lists the accepted forms. Where an argument accepts an enum name as
a string, use one of the documented names. A string cannot define a new
market index.

## Scenarios and historical markets

Apply temporary market shocks inside a scenario block:

```python
scenario = qs.Scenario(shocks=[
    qs.Shock(target="SOFR", value=0.0001, shock_type=qs.ScenarioType.Absolute),
])
with context, scenario:
    stressed = position.evaluate([qs.Request.Value])
```

The base inputs are not changed. Nested scenarios apply in the order they are
entered. Only the affected objects that a calculation needs are rebuilt.

To value a position against a past market, select a complete snapshot from a
market archive:

```python
archive = qs.MarketSnapshotStore()
archive.insert(qs.MarketSnapshot.from_context(
    qs.DateTime(2026, 1, 2, 16, 30), context,
))
selector = qs.SnapshotSelector(
    qs.DateTime(2026, 1, 2, 17),
    rule=qs.SnapshotSelectionRule.Previous,
    level=qs.Level.Mid,
)
with archive.pricing_context(selector) as historical:
    print(historical.snapshot_timestamp, historical.evaluation_date)
    print(historical.evaluate(position, [qs.Request.Value]).price)
```

The time the snapshot was recorded and the market's valuation date are
different values. Selecting a snapshot does not roll its curves forward to the
requested time.

An archive stores the inputs needed to rebuild each market. It does not store
fixing publication dates, custom Python pricers, or policies registered only in
Python. Supply those separately when you need them.

## Scripts and portfolio workflows

`context.evaluate_script` runs a `ScriptedProduct`, or the equivalent
dictionary, with rate models and returns the average value of each script
variable.

- Call it inside an active context, or after `context.initialize()`.
- Use a positive number of paths.
- Configure a rate model for every discount and forward index the script uses.
  A missing model is an error; it is not treated as zero volatility.
- `result_variable` names the variable used for derivatives and control-variate
  adjustment. It does not limit which variables are returned.
- Models are taken from the pricer configuration, then from the simulation
  configuration. Models defined in the script override both.
- Hull–White settings are converted to the equivalent LGM model.
- The discount index needs a configured model and built curves. A script in a
  currency other than the base currency needs an explicit discount index.

Script evaluation supports rate models only. It does not provide FX or equity
factors, custom correlations, raw paths, or cashflow and sensitivity tables.
For exposure and XVA on built-in trades, use the context's XVA workflow. For
the other features, use the Rust library.

Library failures raise `QuantSupportError`. Invalid Python inputs can also
raise `TypeError` or `ValueError`.

Next steps:

- The [user guide](guide/index.rst) explains each workflow.
- The [example notebooks](studies/index.rst) build complete applications.
- The [API reference](../autoapi/quantsupport/index.rst) lists every class and
  method.
