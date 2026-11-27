# QuantSupport example notebooks

These fifteen notebooks show how to use QuantSupport for quantitative finance
calculations in Python. Each one starts from a contract or market problem,
states its assumptions, and explains the results. They assume you know the
financial products and introduce the library as they go.

Run the cells in order in a fresh kernel. The notebooks are saved with their
outputs, which the documentation site displays.

## Catalog by financial workflow

The notebooks are grouped into folders by workflow. Each folder has its own
catalog, notebooks, and input files. Most folders include a `market_data.py`
loader. The portfolio notebooks define their small markets in the notebook.

| Scope | Catalog | Coverage |
| --- | --- | --- |
| `bootstrap` | [Curve construction](bootstrap/README.md) | Quotes, bootstrap configurations, nodes, pillars, and forwards |
| `valuation/swaps` | [Swaps](valuation/swaps/README.md) | First valuation, par coupon and base-currency conversion |
| `valuation/bonds` | [Bonds](valuation/bonds/README.md) | Straight-bond analytics and callable stepped bonds |
| `valuation/caps` | [Caps and caplets](valuation/caps/README.md) | Black option values and curve/volatility risk |
| `valuation/loans` | [Loans](valuation/loans/README.md) | Repayment, resets, prepayment, credit, valuation and risk |
| `volatilitysurface` | [Volatility markets](volatilitysurface/README.md) | Curves, surfaces, and independent rate/volatility valuation shocks |
| `hullwhite` | [Rate simulations](hullwhite/README.md) | Calibrated model setup and retrieving simulation results |
| `sensitivity` | [Portfolio and risk](sensitivity/README.md) | Portfolio basics, valuation requests, aggregation, quote risk, and scenarios |
| `scripting` | [Payoff events](scripting/README.md) | Dated payoff scripts and representation checks |
| `cva` | [Exposure and XVA](cva/README.md) | Netting sets, credit/funding inputs, exposure profiles, and XVA |

## Suggested reading order

| Order | Notebook | What you will learn |
| --- | --- | --- |
| 1 | [From quotes to a swap](valuation/swaps/tour.ipynb) | Dates and conventions, product/position terms, market indices, the context lifecycle, requests, and result units |
| 2 | [Par swap](valuation/swaps/par_swap.ipynb) | Solve the fixed coupon and verify zero PV |
| 3 | [Fixed-rate bond](valuation/bonds/fixed_rate_bond.ipynb) | Price/Z-spread anchors, yield, duration, payments and quote risk |
| 4 | [Caps and caplets](valuation/caps/caps_and_caplets.ipynb) | Black option values and separate rate/volatility risk |
| 5 | [Loans](valuation/loans/loans.ipynb) | Repayment, resets, prepayment, par coupon/spread, credit and risk |
| 6 | [Currency conversion](valuation/swaps/currency_conversion.ipynb) | Read FX direction, value a CLP swap under USD collateral, and reconcile its base-currency PV |
| 7 | [Curves and volatility](volatilitysurface/curves_and_volatility.ipynb) | Configure and inspect curves and surfaces, query forwards and smiles, and explain market-shock P&L |
| 8 | [Simulations and their results](hullwhite/simulations.ipynb) | Model calibration, path count/seed/grid, retrieving paths, seeds and sampling error |
| 9 | [How a portfolio works](sensitivity/portfolio.ipynb) | Build positions, use `qs.Portfolio`, reconcile PV/risk/payments, and understand membership and request rules |
| 10 | [Portfolio valuation and risk](sensitivity/portfolio_risk.ipynb) | Aggregate quote risk and payments, distinguish DV01 from vega, and check AAD against full revaluation |
| 11 | [Coupon and cashflow aggregation](sensitivity/portfolio_aggregation.ipynb) | Use `qs.Portfolio`, retain fixing indices, inspect weighted quotes, and separate interest/capital payments |
| 12 | [Callable stepped-coupon bond](valuation/bonds/stepped_coupon_bond.ipynb) | Typed terms, calibrated tree/Fourier engines, OAS and risk |
| 13 | [Scripted cashflows](scripting/scripted_cashflows.ipynb) | Dated observations/payments and the native-versus-scripted bond check |
| 14 | [Exposure and XVA](cva/xva.ipynb) | Netting sets, client terms, exposure profiles and adjustment risk |

Start with the first notebook. Each later notebook sets up its own small
market, so you can also go straight to the subject you need. Some useful
entry points:

- Portfolios: [How a portfolio works](sensitivity/portfolio.ipynb) covers
  `qs.Portfolio`, position sizes, the common reporting currency, and which
  requests a portfolio supports. For weighted coupons and interest and capital
  payments, open
  [`sensitivity/portfolio_aggregation.ipynb`](sensitivity/portfolio_aggregation.ipynb).
- Curves: [bootstrap/curves.ipynb](bootstrap/curves.ipynb) looks at curve
  construction in detail before any pricing.
- Loans: [the loan walkthrough](valuation/loans/loans.ipynb) goes from a fixed
  payment schedule through floating resets, prepayment, valuation, and risk.

## Install and run

The notebooks need the package built from this checkout. From the repository
root, inside an activated virtual environment or Conda environment, run:

```bash
python -m pip install maturin -r examples/requirements.txt
maturin develop -m Cargo.toml --release
cd examples
python -m jupyterlab
```

To create a virtual environment, run `python -m venv .venv` and activate it:
`source .venv/bin/activate` on macOS and Linux, or
`.venv\Scripts\Activate.ps1` in PowerShell. A Conda environment also works.
In Jupyter, select the kernel for the interpreter where `maturin develop`
installed the package.

Open any notebook and run its cells in order:

- Most notebooks load their market with `from market_data import load_market`.
  The `market_data.py` file in the notebook's folder finds the data and
  configuration files relative to its own location.
- The portfolio introduction and aggregation notebooks define their small
  markets in the notebook.
- The scripting notebook also uses the event builder in its folder.
- No extra helper package or notebook magic is needed.

Jupyter starts each kernel in the notebook's folder. If your editor uses a
different working directory, set the kernel's working directory to the folder
that contains the notebook. The runner below does this for you.

The notebooks do not run Cargo, download live data, or depend on variables from
other notebooks. If the package and the usual notebook and plotting
libraries are installed, you can run them without further setup.

To run all notebooks without a browser, run this from the repository root
with your environment's Python:

```bash
python examples/run_notebooks.py
```

This runs all fifteen notebooks.

To run selected notebooks and save the executed copies outside the source
folders:

```bash
python examples/run_notebooks.py hullwhite/simulations.ipynb sensitivity/portfolio_risk.ipynb --output-dir artifacts/notebooks
```

What the runner does:

- It finds notebooks in every folder and runs each one in a fresh kernel that
  uses the current interpreter.
- It checks the notebook format and fails on any cell error.
- Before running cells, it compares the kernel with the caller: Python
  executable, environment prefix, package import path and version, and the
  package's exports. It stops at once if the package is out of date.
- The reported executable must be inside your intended environment. Do not
  replace a virtual environment's Python symlink with the base interpreter it
  points to.
- After running, it checks the kernel again and refuses to save outputs if the
  environment changed.
- Saved notebooks record the Python and package versions and whether the
  kernel matched the runner. They do not record machine-specific paths.
- With `--output-dir`, executed copies keep the same folder layout.

Options:

- By default, source notebooks are not changed. Pass `--write` to save new
  outputs into them.
- Pass `--kernel NAME` to use a registered kernel instead of the current
  interpreter.
- The timeout for each cell is 600 seconds. Change it with `--timeout`.

Build the package with `--release`, as above, for interactive pricing. The
callable-bond notebook uses small grids for its two calibrated valuations and
the OAS solve, so it runs quickly. The notebook explains how to refine them.

The runner's own tests use the standard-library test runner, the package
built from this checkout, and the notebook dependencies in `requirements.txt`
(`nbclient`, `nbformat`, and `ipykernel`; `jupyter_client` comes with Jupyter):

```bash
python -m unittest discover -s examples -p test_run_notebooks.py
```

Two of these tests start real kernels:

- The default kernel must use the calling interpreter and package, even if a
  different `python3` kernel is registered.
- A kernel selected by name must keep its own launch command.

The tests create their kernels and notebooks under
`artifacts/notebook-runner-tests` and delete them after each test. They do not
register kernels globally or install anything.

## How the pieces fit

Market data:

- `QuoteStore` holds market quotes.
- `FixingStore` holds past index fixings.
- `FxStore` holds spot exchange rates.
- Curve and volatility configurations describe how to build curves and
  surfaces from quote identifiers.
- A `MarketIndex`, such as SOFR, links those curves to products and models. It
  is a name, not a market value.

Most examples value USD products from a single reference date and need no past
fixings. The currency-conversion example also supplies a USD/CLP spot rate and
a CLP curve under USD collateral.

Pricing:

1. Create a `PricingContext` and enter `with context:`. Entering checks the
   inputs. Curves and other objects are then built when a curve query,
   valuation, script, or XVA calculation first needs them.
2. Optionally call `initialize()` to build all configured objects up front.
   The `with` block does not need it.
3. Call `evaluate(trade, requests)`. It returns an `EvaluationResults` object
   with numbers and pandas tables. The instrument and trade describe the
   contract and position; the built-in pricer does the valuation.
4. Keep the results and use them after the block. Use curve, surface, and
   simulation objects only inside the active context.
5. When the block exits, even because of an exception, the context releases
   the objects it built.

Run contexts one after another, not at the same time on one thread.

Other workflows:

- A simulation configuration adds a model and path-generation settings. A
  simulated rate path is not a product value.
- Script evaluation and the XVA engine combine models with future payments to
  answer different questions.
- For portfolio valuation, use
  `context.evaluate(Portfolio("BOOK", trades), requests)`. The portfolio risk
  notebook also shows how to reconcile results with labeled pandas tables.
- Legal netting is defined separately with `NettingSet`.

You can also price your own Python instruments with `register_pricer`; see the
[guide to extending valuation in Python](https://jmelo11.github.io/quantsupport-python/python/guide/risk.html#extending-valuation-in-python). The
notebooks use the built-in products.

## Auxiliary files and market provenance

| File | Responsibility |
| --- | --- |
| `market_data.py` in each folder | Loader imported by the folder's notebooks; reads market inputs and configurations, and does no pricing |
| [stepped_cashflows.py](scripting/stepped_cashflows.py) | Turns the notebook's six-year semiannual note into script events; does not model the issuer's optimal call |
| [valuation/bonds/data/bond_tree.json](valuation/bonds/data/bond_tree.json), [valuation/bonds/data/bond_fourier.json](valuation/bonds/data/bond_fourier.json) | Native pricer/model schema and numerical grids |
| [hullwhite/data/simulation.json](hullwhite/data/simulation.json) | Calibrated Hull–White simulation settings |
| [cva/data/xva.json](cva/data/xva.json) | Calibrated LGM exposure-engine settings |
| [run_notebooks.py](run_notebooks.py) | Runs the notebooks against the installed package |

The market data is illustrative, not real:

- Most notebooks use the 2026-02-24 market in
  [`examples/data/hullwhite`](data/hullwhite): `quotes.json`,
  `curve_specs.json`, and `vol_specs.json`.
- The [currency-conversion notebook](valuation/swaps/currency_conversion.ipynb)
  uses the USD/CLP quote and curve files in
  [`examples/data/bootstrap`](data/bootstrap) for the same date, with a spot
  rate of 935 CLP per USD.
- The [loan notebook](valuation/loans/loans.ipynb) uses a separate EUR market
  from [`examples/data/loans`](data/loans).

Keep the repository layout when you run the notebooks. If you copy only the
notebooks, their helper files and market data are missing. The quotes are never
downloaded or updated automatically.

The market contains a SOFR curve and a Black caplet volatility surface with
absolute-strike smiles. The simulation and callable-bond notebooks calibrate a
short-rate volatility schedule to that surface. A quoted Black volatility and
the model's absolute sigma are different quantities.

## Reading the numbers

- Rates and spreads are decimals: `0.04` is 4%, and `1e-4` is 1 bp.
- A Black volatility of `0.30` is 30%; +1 volatility point is `0.01`.
- `result.price` is the position's present value, with its sign. Bond clean
  and dirty price anchors use the bond's quotation units, usually per 100 of
  principal.
- `sensitivities.value` is a derivative per unit of the input quote. Multiply it
  by the size of the move before reporting DV01 or vega. The notebooks keep the
  signs.
- Cashflow amounts are undiscounted payments, labeled with currency and leg.
  Swap, bond, and loan reports include the position's direction:
  receipts are positive and payments are negative. To reconcile with PV,
  discount the amounts and convert currencies as needed, but do not apply the
  direction again.
- A measure that is missing or was not requested is not zero. Do not fill it
  with zero when reporting product-level results.

## Numerical checks and limitations

| Study | Independent numerical evidence |
| --- | --- |
| Bootstrap | Deposit repricing, forward/discount-factor identity, positive discount factors |
| Swap tour/par | Signed cashflow PV, reversed position, annuity/par formula and zero-PV repricing |
| Currency conversion | FX reciprocity, CLP/USD PV reconciliation, principal cancellation |
| Straight bond | Spread and yield PV reconstruction, duration bump, spread AAD/bump |
| Caps | Direct Black formula, put–call parity, explicit caplet-strip sum |
| Callable bond | OAS round trip, callable/underlying inequality, observed grid refinement |
| Volatility | Smile interpolation and isolation of rate versus volatility shocks |
| Simulation | Calibration residuals/domain, seeds, Gaussian Euler moment recursion |
| Portfolio introduction | Individual PV/risk/payment sums, zero-rate central differences, discounted payment PV, repeated/opposing positions |
| Portfolio risk | Rate/volatility AAD versus central differences; signed payment PVs |
| Scripting | Deterministic native representation check; repeated-seed stochastic estimates |
| Loans | Annuity payment, principal conservation, receipt PVs, par repricing, funding PV01 |
| XVA | Signed profile identity, raw-exposure netting, margin/profile distinction |

Tolerances, seeds, and grids are visible in the code. Exact formula checks,
calibration derivatives, discretization checks, and sampling checks each test
something different. Keep in mind:

- Simulated Hull–White paths use Euler steps and are stored as plain `f64`
  numbers. Exported paths carry no sensitivities to the input quotes.
- A script's result variable may include a martingale control-variate
  adjustment. With a finite number of paths, the raw payment PVs may not add
  up to that adjusted result.
- Exposure profiles are averages at each date, before margin. ENE is signed and
  negative. CVA and FVA use paths after margin, and FVA uses signed exposure.
- A scenario target matches quotes whose identifier contains all of its
  underscore-separated parts, so even a full identifier can match other quotes.
  The volatility notebooks use one target for a whole quote family and check
  that each intended quote moves exactly once.

These notebooks explain and check the library's calculations. Their simplified
settings and illustrative markets do not show that a model is adequate for
production use.
