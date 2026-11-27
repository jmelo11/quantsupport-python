Example notebooks
=================

These notebooks build curves and calculate values and risk with the Python
package. Each one starts from a financial problem, states its assumptions, and
explains the results. The :doc:`Python guide <../guide/index>` explains the
conventions they share. Use the :doc:`reference <../../autoapi/quantsupport/index>`
to look up a class or method.

Each page shows the code, tables, and figures saved in the notebook. The
documentation build does not run the notebooks. To reproduce the results, use
the notebook's input files and a package built from the same checkout. Each
notebook states its numerical settings, such as grids, random seeds, and
comparison tolerances.

Curve construction
------------------

Build a discount curve from market quotes, then inspect its forward rates,
zero rates, and repricing checks.

.. toctree::
   :maxdepth: 1

   notebooks/curves

Swaps and collateral currencies
-----------------------------------

These notebooks start with a receive-fixed swap, then solve for the par
rate. The last one covers cashflows, FX quote direction, and currency
conversion that depends on the collateral currency.

.. toctree::
   :maxdepth: 1

   notebooks/first-swap
   notebooks/par-swap
   notebooks/currency-conversion

Fixed income and loans
--------------------------

These notebooks cover bond price and spread anchors, bonds with issuer calls,
and loans with amortization and borrower prepayment. Each product has its own
price and cashflow conventions.

.. toctree::
   :maxdepth: 1

   notebooks/fixed-rate-bond
   notebooks/callable-bond
   notebooks/loans

Rate options and volatility
-------------------------------

Check the option inputs before you read a price. A rate strike, a quoted
Black volatility, and a calibrated short-rate sigma are different quantities.

.. toctree::
   :maxdepth: 1

   notebooks/caps-and-caplets
   notebooks/curves-and-volatility

Short-rate simulation
---------------------

This notebook covers model calibration, stored paths, random seeds, and
sampling error. Stored simulation paths do not carry calibration or volatility
sensitivities.

.. toctree::
   :maxdepth: 1

   notebooks/simulations

Portfolio risk
--------------

Start with how a portfolio is built: its trades, position sizes, requests,
and combined result tables. The next notebooks cover weighted coupons, fixing
indices, and separate interest and capital payments. The last one checks
sensitivities against full revaluation.

.. toctree::
   :maxdepth: 1

   notebooks/portfolio
   notebooks/portfolio-aggregation
   notebooks/portfolio-risk

Scripted payoffs
--------------------

This notebook values the same bond as a built-in product and as a script, and
compares the results. Exact checks are kept separate from simulation
estimates. A script's result variable can include a control-variate adjustment.

.. toctree::
   :maxdepth: 1

   notebooks/scripted-cashflows

Exposure and XVA
----------------

Compare netting and collateral assumptions, signed average exposures, and
CVA and FVA. An exposure profile is the average exposure at each date. It is
not a potential future exposure (PFE) quantile or an average over time.

.. toctree::
   :maxdepth: 1

   notebooks/xva

Reproduction
------------

Build the package, then install the example dependencies into the same
environment. From the repository root, run:

.. code-block:: console

   python examples/run_notebooks.py
   python examples/run_notebooks.py valuation/swaps --write

- The runner starts a fresh kernel for each notebook. It uses the current
  interpreter unless you select a kernel.
- The first command checks the notebooks without changing them. ``--write``
  saves the new outputs.
- Before running any cells, the runner checks that the kernel uses the
  expected interpreter and the freshly built package. It stops if the package
  is out of date.
- Each saved notebook records the Python and package versions, and whether the
  kernel matched the runner, in its ``execution_environment`` metadata. Check
  this metadata to see what produced the outputs.
- Each notebook page links to its source and to the folder with its input
  files. A downloaded notebook needs those input files to run.
