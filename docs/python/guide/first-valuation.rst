A position, a market, and a valuation
=========================================

Installation and reproducibility
------------------------------------

Install the package into the Python interpreter that runs your application or
notebook:

.. code-block:: console

   python -m pip install quantsupport

To download a package by hand, choose your operating system, architecture,
and Python version on the `Python packages page <https://jmelo11.github.io/quantsupport-python/python/downloads.html>`_.
It offers wheels and folder ZIPs. A folder ZIP contains only QuantSupport, so
first install pandas with ``python -m pip install pandas``.

To build the package from this repository, create a virtual environment,
install Maturin, and compile the checkout:

.. code-block:: console

   python -m venv .venv
   . .venv/bin/activate
   python -m pip install "maturin>=1.5,<2.0"
   maturin develop -m Cargo.toml --release

On Windows, activate the environment with ``.venv\Scripts\Activate.ps1``.
Building from source requires the stable Rust toolchain. Use the same
interpreter in your application or notebook so that it loads the package you
just built.

To reproduce a valuation later, keep its market data, conventions, package
version, and model parameters.

Contract and position
---------------------

An instrument, such as :py:class:`~quantsupport.instruments.Swap`, holds the
contract terms. A :py:class:`~quantsupport.pricing.Trade` is your position in
that instrument. It adds:

- the trade (execution) date, which is required and is never taken from the
  maturity, exercise, or context date;
- the side, which sets the direction;
- optional position-size overrides.

Two trades can hold opposite positions in the same contract.

For a vanilla swap, ``LongReceive`` receives fixed and pays floating, and
``PayShort`` does the opposite. Position sizes must not be negative; set the
direction with ``side``. A product dictionary holds only constructor terms. Do
not put ``side``, ``trade_date``, bond anchors, or futures contract counts in it.

The example below values a five-year USD swap with a notional of USD 10
million. It receives a fixed 3% coupon and pays a floating coupon. The market
is a flat, continuously compounded 3% zero-rate curve, given by two pillars
with the same rate.

.. code-block:: python
   :name: guide-python-swap

   import quantsupport as qs

   reference = qs.Date(2026, 2, 24)
   quotes = qs.QuoteStore.from_dict({
       "reference_date": str(reference), "quotes": [
           {"identifier": f"ZeroRate_USD_SOFR_{tenor}", "mid": 0.03}
           for tenor in ["0D", "10Y"]
       ],
   })
   curve_spec = qs.CurveConfiguration(
       market_index=qs.MarketIndex.SOFR,
       quotes=quotes.identifiers(),
       day_counter="Actual360", interpolator="Linear",
       enable_extrapolation=True,
   )
   policy = qs.SingleCurveCSADiscountPolicy("USD", "SOFR")
   context = qs.PricingContext(quotes, [curve_spec], csa_policy=policy)
   swap = qs.Swap(
       identifier="USD-IRS-5Y", start_date=reference,
       maturity_date=reference + "5Y", notional=10_000_000,
       fixed_rate=0.03, currency="USD", market_index="SOFR",
       day_counter="Actual360", compounding="Simple",
       rate_frequency="Annual", fixed_leg_frequency="Semiannual",
       floating_leg_frequency="Quarterly",
   )
   trade = qs.Trade(swap, reference, qs.Side.LongReceive)

   with context:
       result = trade.evaluate([
           qs.Request.Value, qs.Request.FairRate(0),
           qs.Request.Cashflows(), qs.Request.Sensitivities,
       ])
       discount = context.curve("SOFR").discount_factor(reference + "5Y")
       print(result.price, result.fair_rate, discount)
       print(result.sensitivities)

The receive-fixed position has a negative PV. The continuously compounded
curve implies floating coupons slightly above the simply compounded 3% fixed
coupon. ``fair_rate`` is the fixed coupon, as an annual decimal, that makes the
swap's value zero under these conventions. Money amounts are in USD for the
ten-million notional. Rates are decimals.

For a single-currency fixed-versus-floating swap, the value is

.. math::

   V_{\mathrm{receive\ fixed}}
   = \sum_i D(t,T_i)\,C_i^{\mathrm{fixed}}
     - \sum_j D(t,U_j)\,C_j^{\mathrm{floating}}.

For a vanilla swap, the par coupon is :math:`K^*=PV_{\mathrm{float}}/A`, where
:math:`A=N\sum_i\alpha_iD(t,T_i)`.

- ``Request.FairRate(0)`` solves for the first leg's fixed coupon.
- ``Request.FairRate(1)`` solves for the second leg's floating spread.

The solver sets the whole trade's PV to zero. That PV includes principal
exchanges and uses each leg's curves, discount policy, and direction. Only the
selected leg's rate or spread changes. An invalid leg index raises an error.
Each evaluation returns one fair rate.

Interpreting results
--------------------

An :py:class:`~quantsupport.pricing.EvaluationResults` holds the measures you
requested. A property is ``None`` when its measure was not calculated.

- ``Value`` gives the PV in money, not a clean bond price.
- ``Sensitivities`` gives a pandas table with ``pillar`` and ``value`` columns.
  Each row is the derivative of the value with respect to the named input. It
  is not scaled to DV01 or to vega per volatility point.

For a rate input :math:`q` in decimals, a +1 bp move changes the value by about
:math:`(\partial V/\partial q)10^{-4}`. The curve above has two labeled
zero-rate inputs. The sum of their derivatives estimates the effect of moving
both zero rates in parallel. A bootstrapped curve reports derivatives with
respect to its calibration quotes instead. See :doc:`risk` for a check against
full revaluation.

The ``cashflows`` table has the columns ``payment_date``, ``type``,
``amount``, ``fixing``, ``accrual_period``, ``currency``, ``caplet_strike``,
``floorlet_strike``, and ``leg_index``.

For the generic discounted-cashflow pricer:

- Amounts include each leg's direction: receipts are positive and payments
  are negative. Disbursements follow the same rule.
- The table can include initial disbursements and redemptions on both legs, so
  the sum of ``amount`` is not the swap PV.
- To reconcile with PV, discount each amount and convert currencies where
  needed. Do not apply the position's direction again.
- Payments before the valuation date are excluded from PV. Payments on the
  valuation date are included.
- For a seasoned deposit, keep the original contract dates. Its initial
  advance, already paid, is excluded from PV and risk. The interest paid at
  maturity still accrues from the original start date.
- The date window of a cashflow report does not change these valuation rules.

Specialized pricers have their own rules for which payments they include and
report.

Context lifetime
----------------

Creating a :py:class:`~quantsupport.pricing.PricingContext` only stores its
inputs. Entering ``with context:`` checks the inputs and makes the context
active. From then on, curves, volatility objects, models, and simulations are
built when a calculation first needs them. Call ``context.initialize()`` to
build all configured objects at once.

``trade.evaluate(requests=None)`` uses the innermost active context:

- With no requests, it calculates ``[Request.Value]``.
- It applies the same policies, registered pricers, scenario shocks, and risk
  basis as ``context.evaluate(trade, requests)``, which you can also call
  directly.
- Nested contexts restore the previous context when they exit.
- Calling it outside a ``with context:`` block raises ``RuntimeError``.
  ``context.initialize()`` alone does not make a context active.

Use curves and other built objects only inside the ``with`` block. When the
outermost block exits, the context releases the market data it built. This
also happens when an exception is raised. You can keep numbers and result
tables, but do not use a curve object after its context or scenario ends.

Use each context and scenario on the thread that created it. Exit them in the
reverse order you entered them.

Each context input has a setter. Getters for stores and configurations return
copies. To change an input, edit the copy and assign it back to the context.
The objects that depend on it are rebuilt for the next valuation. The
instrument itself does not change, so you can value it again under another
market.

Dates, types, and protocols
-------------------------------

Dates accept a ``Date``, ISO text, or a Python ``datetime.date``.

- Adding a ``Period`` or a tenor such as ``"6M"`` to a ``Date`` moves it on the
  calendar. It does not adjust for business days; use a ``Calendar`` for that.
- ``Schedule`` supports iteration and indexing. It returns copies of its dates
  and of its flags that mark regular periods. Coupon accrual conventions are
  set separately from the schedule.

The examples use Actual360 or Actual365. Two other day counters have rules to
check before you use them:

- ``ActualActual.year_fraction`` splits the period at calendar-year boundaries
  and includes every complete intervening year.
- ``Thirty360US`` adjusts 31st days first, then adjusts February month-ends
  separately. This order differs from the common US/NASD/BondBasis rules.

Check these conventions against your contract's dates.

Timestamps use ``DateTime``. It requires a time-zone offset, converts to UTC,
and keeps nanoseconds. Converting to a Python ``datetime`` truncates to
microseconds. The UTC day of an observation is not always its market valuation
date.

Many constructors accept either an enum or its name, but not every API does.
``Shock.shock_type`` and typed calendar and schedule parameters need the
documented enum values. For indices with parameters, use a factory such as
``MarketIndex.equity("SPX")`` or a tagged dictionary, not a display label such
as ``"EQ:SPX"``. The API reference lists the accepted forms.

Library failures usually raise ``QuantSupportError``. Python argument and
context checks can raise ``TypeError``, ``ValueError``, or ``RuntimeError``.
Use the error details to find the missing input or the conflicting convention
before you change the market setup.
