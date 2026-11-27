# QuantSupport for Python

QuantSupport for Python is a package for pricing financial instruments and
measuring their risk. It is a Python interface to the QuantSupport Rust library.

With it you can:

- build yield curves and volatility surfaces from market quotes;
- value swaps, bonds, loans, deposits, options, and other instruments;
- compute sensitivities, cashflow reports, scenarios, and exposure and XVA.

Results are returned as numbers and pandas tables.

## Install

QuantSupport requires Python 3.9 or later. Installing it also installs pandas.

```sh
python -m pip install quantsupport
```

Released wheels include the compiled library, so you do not need Rust. For
optional editor typing dependencies, install `quantsupport[typing]`.

You can also download packages by hand from the
[Python downloads page](https://jmelo11.github.io/quantsupport-python/python/downloads.html).
It offers a package for each supported Python version, operating system, and
architecture. The folder ZIPs contain only QuantSupport, so install pandas
separately.

To build the package from this repository, see
[Build from source](#build-from-source).

## Quick example

This example values a five-year USD swap that receives a fixed 3% coupon and
pays SOFR. The market is a flat 3% zero-rate curve built from in-memory
quotes, so no data files are needed.

```python
import quantsupport as qs

reference = qs.Date(2026, 2, 24)
quotes = qs.QuoteStore.from_dict({
    "reference_date": str(reference), "quotes": [
        {"identifier": f"ZeroRate_USD_SOFR_{tenor}", "mid": 0.03}
        for tenor in ["0D", "10Y"]
    ],
})
curve = qs.CurveConfiguration(
    market_index="SOFR", day_counter="Actual360", interpolator="Linear",
    quotes=quotes.identifiers(),
)
context = qs.PricingContext(
    quotes, [curve], csa_policy=qs.SingleCurveCSADiscountPolicy("USD", "SOFR"),
)
swap = qs.Swap(
    "USD-IRS", reference, reference + "5Y",
    10_000_000, 0.03, "USD", "SOFR",
    fixed_leg_frequency="Semiannual", floating_leg_frequency="Quarterly",
)
position = qs.Trade(swap, reference, qs.Side.LongReceive)
with context:
    result = position.evaluate(["Value", "FairRate", "Sensitivities"])
    print(result.price, result.fair_rate)
    print(result.sensitivities)
```

How to read the output:

- The swap has a small negative value. The curve's zero rates are
  continuously compounded, so the implied simple forward rates are slightly
  above the 3% fixed rate that this position receives.
- Rates and spreads are annual decimals unless stated otherwise: `0.03` is 3%.
- Each row of `result.sensitivities` is the derivative of the value with
  respect to one input. For a rate input, multiply by `0.0001` to estimate the
  change in value, in money, for a one-basis-point increase.
- Swap cashflow tables show signed amounts: receipts are positive and payments
  are negative. Initial advances are included. The table has no present-value
  column.

## Key concepts

- **Instrument**: the terms of a contract, such as `Swap` or `FixedRateBond`.
  An instrument is not a position.
- **Trade**: a position in an instrument. It holds the trade date, the side
  (for example `Side.LongReceive`), optional size overrides, and, for bonds,
  the pricing anchor. You always value trades, not bare instruments. Do not put
  `side` or `trade_date` in instrument dictionaries.
- **Market inputs**: `QuoteStore` holds quotes. `CurveConfiguration` describes
  how to build a curve from quote identifiers.
- **Pricing context**: `PricingContext` combines the market inputs with pricing
  policies. Enter it with `with context:` before you value anything.
- **Requests**: the measures to calculate, such as `"Value"`, `"FairRate"`,
  `"Sensitivities"`, or `"Cashflows"`.
- **Results**: `EvaluationResults` holds scalar measures and pandas tables. A
  measure that was not calculated is `None`.

Classes are grouped in the `quantsupport.time`, `.market`, `.instruments`,
`.pricing`, and `.risk` packages. The package root exports the same classes,
so `quantsupport.Swap` and `quantsupport.instruments.Swap` are the same class.

### Pricing contexts

- `position.evaluate()` uses the innermost active context. Without arguments it
  requests `[Request.Value]`. It applies that context's scenarios, pricing
  policies, and registered pricers.
- `context.evaluate(position, requests)` does the same with an explicit
  context. Use it for portfolios as well.
- Nested `with` blocks restore the previous context when they exit.
- The context builds curves and other market objects when a calculation first
  needs them. Call `context.initialize()` to build all of them up front.
- When the outermost `with` block exits, the context releases the market
  objects it built. Keep the results you need, but do not use curves or other
  market objects from the context after the block, or after a scenario, ends.
- Properties that return stores or configuration lists return copies. To change
  an input, edit the copy and assign it back, for example
  `context.quotes = updated_quotes`. The context then rebuilds what depends on it.

### Portfolios

Group trades in a `Portfolio` and evaluate it with `context.evaluate`. The
result is a standard `EvaluationResults`:

```python
book = qs.Portfolio("PORTFOLIO", [position, another_position])
with context:
    result = context.evaluate(
        book, ["Value", "Sensitivities", "Cashflows"],
    )
    print(result.price)
    print(result.sensitivities)
    print(result.cashflows)  # type, market_index, dates, notional, rate/spread, conventions
    print(result.cashflow_summary)  # payment_date, currency, interest, capital, other, total
```

How portfolio results are combined:

- Each trade is valued with its own pricer. Results are added in portfolio
  order, and sensitivities to the same risk factor are summed.
- A trade listed twice counts as two positions.
- If any member does not produce a measure, or the portfolio does not support
  it, that measure is missing from the result.
- Built-in pricers report values and sensitivities in the context's base
  currency. They convert using the context's FX store, so FX risk is included.
  Python pricers must also report money amounts in the base currency.
- Cashflows stay in their payment currency.

The cashflow tables:

- `result.cashflows` lists the contractual terms of each coupon: type,
  fixing index (including leg overrides), accrual dates, day count, overnight
  conventions, and payoff. Past payments are kept.
- Compatible coupons are merged. Fixed coupons show a notional-weighted rate,
  and linear floating coupons show a notional-weighted spread.
- Pay and receive coupons stay in separate rows. So do daily-compounded spreads,
  coupons with different option payoffs, and coupons without contractual terms.
- Date columns use pandas datetime types, with `NaT` for a missing date.
- `result.cashflow_summary` totals each payment date into net coupon interest,
  signed capital (redemptions and advances), other (unknown payment types), and
  total. It reports payments only; it does not spread interest over accrual
  periods.

To learn the portfolio workflow, start with
[How a portfolio works](examples/sensitivity/portfolio.ipynb). It covers
building positions, requests, result tables, and checking the totals. Then
open the [portfolio aggregation notebook](examples/sensitivity/portfolio_aggregation.ipynb).
It has an editable deposit and swap book, weighted quotes, separate fixing
indices, a check against individual positions, and optional CSV exports.

### Product notes

- **Deposits**: use `qs.FixedRateDeposit` (also available as
  `qs.instruments.FixedRateDeposit`), or build one with `MakeFixedRateDeposit`.
  Wrap it in a `qs.Trade` to add it to a portfolio.
- **Bonds**: a bond trade requires a `pricing_anchor`. Clean and dirty prices
  are in quotation units, usually per 100 of principal. Spread anchors are a
  Z-spread for straight bonds and an OAS for bonds with issuer calls. Choose the
  discount curve with the context's discount policy.
- For bonds, request `YieldToMaturity`, `ModifiedDuration`, `ZSpread`, or the
  selected model's `OAS` instead of `FairRate`.
- **Loans**: `Value` is the present value of future expected receipts. It does
  not include the initial advance. Value loans as `qs.Trade` positions, alone or
  in a portfolio, with `context.evaluate(...)`. Set fair-rate and refinancing
  options with `PricerConfiguration.loan(...)`, and the discount curve with
  `context.fixed_income_policy`.
- **Scripting**: `context.evaluate_script` returns the average value of each
  numeric script variable. It does not return sensitivity or cashflow tables.
  Configure rate models explicitly. With a finite number of paths, raw cashflow
  PVs may not add up to the selected result variable, because that variable
  can include a control-variate adjustment.
- **XVA**: `run_xva` computes CVA and FVA for the supported products listed in
  the guide. ENE is signed. Exposure profiles are averages at each date, before
  margin; they are not PFE quantiles.
- **XVA sensitivities**: when credit or funding come from curves, sensitivities
  are reported against survival-probability and derived funding-spread
  pillars. They are not sensitivities to the original CDS or funding quotes.
- **Historical markets**: a selected snapshot is one complete market with its
  own valuation date. Supply fixings separately; they are not filtered by
  publication date.

### Inputs

- Many inputs accept an enum value or its name as a string. Shock, calendar,
  and schedule parameters accept only the documented enum values.
- For an equity index, use `qs.MarketIndex.equity("SPX")` or
  `{"Equity": "SPX"}`, not `"EQ:SPX"`.
- To load JSON, read the file with Python's `json` module and pass the data to
  `from_dict` or `from_dict_list`. For configurations, `from_dict` returns one
  object and `from_dict_list` returns a list. Product dictionaries use the same
  keys as the constructor's keyword arguments.

## Documentation

- [Python user guide](https://jmelo11.github.io/quantsupport-python/python/guide/index.html):
  installation, a complete valuation, conventions, markets, products, scenarios,
  and exposure and XVA.
  - [First valuation and lifecycle](https://jmelo11.github.io/quantsupport-python/python/guide/first-valuation.html)
  - [Curves, market data, calibration, and history](https://jmelo11.github.io/quantsupport-python/python/guide/markets.html)
  - [Bonds, loans, options, and scripting](https://jmelo11.github.io/quantsupport-python/python/guide/valuation.html)
  - [Sensitivities, netting, XVA, and custom pricers](https://jmelo11.github.io/quantsupport-python/python/guide/risk.html)
- [Example notebooks](https://jmelo11.github.io/quantsupport-python/python/studies/index.html),
  grouped by financial topic.
- [API reference](https://jmelo11.github.io/quantsupport-python/autoapi/quantsupport/index.html)
  for every class: constructors, parameters, defaults, properties, and errors.
- The [QuantSupport Book](https://jmelo11.github.io/quantsupport/) explains the
  financial concepts behind the core library.

## Development

### Build from source

Building from source requires the stable Rust toolchain. From the repository
root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install "maturin>=1.5,<2.0"
maturin develop -m Cargo.toml --release
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1`.

Use this same interpreter in Jupyter. An older installed wheel may be missing
classes that exist in your checkout.

### Run the tests and example notebooks

The [examples guide](examples/README.md) explains environment setup and
reading order. After building the package, run from the repository root:

```sh
python -m pip install -r examples/requirements.txt
python examples/run_notebooks.py
python examples/run_notebooks.py valuation/swaps --write
python -m unittest discover -s tests
```

About the notebook runner:

- It runs each notebook in a fresh kernel.
- Before running any cells, it checks that the kernel uses the expected
  interpreter and the freshly built package. It stops if the package is out of
  date.
- Without `--write`, it does not change the notebooks. With `--write`, it saves
  the new outputs and records the Python and package versions in the
  notebook's `execution_environment` metadata.
- The documentation shows the saved outputs; it does not run notebooks.

### Rust checks

```sh
cargo check -p quantsupport-py
cargo test -p quantsupport-py python_dict_and_script_contracts -- --nocapture
```

- Do not enable the `extension-module` feature for Rust tests.
- Set `PYO3_PYTHON` when Cargo needs a specific Python interpreter.
- On Windows, add the Python runtime DLL directories to `PATH` so tests can
  link and load.
- Put new native product implementations under `src/instruments/` and their
  dispatch under `src/pricing/`.

### Build the documentation

See the [documentation build guide](docs/README.md). A documentation build
needs neither the native module nor notebook execution.

## Maintainers: core dependency and releases

### Core library version

This package uses the core Rust library at the exact Git revision set in
`Cargo.toml`. Build, release, and documentation workflows all run in this
repository.

To use a newer core revision:

1. Update `dependencies.quantsupport.rev` in `Cargo.toml`.
2. Run `cargo update -p quantsupport`.
3. Add wrappers and documentation here for any new Rust APIs.
4. Run this repository's checks.
5. Commit `Cargo.toml` and `Cargo.lock` together, then merge.

### Releases

- The package version is set in `[workspace.package]` in `Cargo.toml`.
- Merging to `main` takes the next patch version and builds a release. The
  signed release commit updates both `Cargo.toml` and `Cargo.lock`.
- Add `[skip release]` to the commit message for documentation-only changes.
  Add `[release]` to release anyway.
- If `main` is protected, the signed version commit may need a `RELEASE_TOKEN`
  secret.
- Configure GitHub Pages to deploy from GitHub Actions.
- Before publishing, configure the PyPI trusted publisher for
  `jmelo11/quantsupport-python`, workflow `release.yml`, environment `pypi`.
