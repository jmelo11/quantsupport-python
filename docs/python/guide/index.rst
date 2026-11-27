Python user guide
=================

A valuation in QuantSupport needs three things:

- a **contract**, which defines the payments;
- a **trade**, which records the position you hold in that contract;
- a **market**, which supplies quotes, curves, and past fixings.

A pricer combines these inputs to calculate the results you request.

This guide builds that workflow with fixed dates and small in-memory markets.
It first explains the conventions you need to read prices and sensitivities.
It then covers valuation and risk for specific products. The
:doc:`example notebooks <../studies/index>` show larger examples, and the
:doc:`API reference <../../autoapi/quantsupport/index>` describes each class,
method, and accepted argument type.

.. toctree::
   :maxdepth: 2

   first-valuation
   markets
   valuation
   risk

Reading path
------------

#. :doc:`first-valuation`: installation, position direction, result units,
   and how long a pricing context keeps its market.
#. :doc:`markets`: curves, market data, and calibration. Read it before you
   change curve or calibration settings.
#. :doc:`valuation`: quotation and model choices for each product type.
#. :doc:`risk`: scenario checks, netting, XVA, and writing your own pricers.

Requirements:

- The package needs Python 3.9 or later.
- The documentation build needs Python 3.11 or later. It does not need the
  compiled package.
- The examples need the compiled package and pandas. Simulation notebooks list
  any extra dependencies themselves.
