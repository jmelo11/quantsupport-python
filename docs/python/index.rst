Python
======

The QuantSupport Python package prices financial instruments and measures their
risk. The basic workflow is:

#. Define the contract and the position you hold.
#. Configure the market.
#. Ask a pricing context for values, cashflows, or sensitivities.

The user guide walks through this workflow with complete examples. The example
notebooks apply it to larger quantitative finance problems.

`Download Python packages <https://jmelo11.github.io/quantsupport-python/python/downloads.html>`_
as wheels or folder ZIPs. Choose the package for your operating system,
architecture, and Python version. Folder ZIPs contain only QuantSupport, so
install its dependency separately with ``python -m pip install pandas``.

.. toctree::
   :maxdepth: 2

   Download Python packages <https://jmelo11.github.io/quantsupport-python/python/downloads.html>
   guide/index
   studies/index
   API reference <../autoapi/quantsupport/index>

The API reference has one page per class, with its constructors, parameters,
methods, properties, and class attributes. Classes are grouped by domain
package, and each domain is split into smaller sections such as Calendars,
Yield Curves, Fixed Income, and Collateral and Netting. The package root
exports the same classes as the domain packages.

Conventions
-----------

- Signatures and parameter descriptions list the input types each argument
  accepts. The reference is generated from the package's type stubs and their
  docstrings.
- A default shown as ``...`` is set by the native library. The parameter
  description gives the actual default or explains how it is chosen.
- Dates accept a ``Date``, ISO text such as ``"2026-02-24"``, or a
  ``datetime.date``.
- Rates and spreads are annual decimals unless a parameter states other units.
- Properties without a setter are read-only.
- Assigning a new value to a context input property makes the context rebuild
  the market objects that depend on it.
- Methods such as ``evaluate()`` perform calculations; they are not attributes.

Exceptions
----------

QuantSupport raises :py:class:`~quantsupport.QSError` or one of its
subclasses. Each error has a stable error code and the name of the native error
type. :py:class:`~quantsupport.QuantSupportError` is an alias of ``QSError``.

The subclasses for type, value, state, I/O, and unsupported-operation errors also
inherit from the matching Python built-in exception. For example, an
``except ValueError`` block also catches
:py:class:`~quantsupport.QuantSupportValueError`.

.. py:exception:: quantsupport.QSError

   Error raised for failures in construction, input conversion, market-data
   lookup, numerical recording, compilation, and evaluation. Inspect ``code``,
   ``native_type``, ``message``, ``operation``, ``path``, ``expected``, ``actual``,
   ``contexts``, and ``details``.
   Fields that do not apply are ``None``. ``__cause__`` holds the original
   exception chain, and ``to_dict()`` exports the same fields and nested causes.
   When an error passes through several operations, they are listed in
   ``contexts`` instead of creating a chain of repeated exceptions.

.. py:exception:: quantsupport.QuantSupportError

   Alias of :py:class:`~quantsupport.QSError`. Both names catch the same errors.

In Jupyter and IPython, an error is shown as one panel. It starts with the
traceback of your code and continues with the error message, the operation, the
input path, and the expected and received types when available. Tracebacks show
complete multiline calls and line markers in the shell's color theme. Long
messages wrap and are not truncated.

This display hides internal binding frames and the cause chain. To see the full
details:

- inspect ``error.__cause__`` or ``error.to_dict()``; or
- print the traceback with its causes using
  ``traceback.print_exception(type(error), error, error.__traceback__)``.

Standard Python tracebacks keep the original causes and also hide internal
binding frames.

The Python subclasses are :py:class:`~quantsupport.QuantSupportTypeError`,
:py:class:`~quantsupport.QuantSupportValueError`,
:py:class:`~quantsupport.QuantSupportStateError`,
:py:class:`~quantsupport.QuantSupportIOError`, and
:py:class:`~quantsupport.QuantSupportNotImplementedError`.

.. code-block:: python

   try:
       quotes = qs.QuoteStore.from_dict(market_inputs)
   except qs.QSError as error:
       print(error.code, error.operation, error.path)
       diagnostics = error.to_dict()

For example, an invalid quote level can report ``code="deserialization"``,
``native_type="DeserializationErr"``, and ``path="quotes[1].mid"``. A missing
quote reports ``code="not_found"`` and ``native_type="NotFoundErr"``. Use these
fields to handle errors; do not match on message text. File errors include the
file path in ``details``. JSON errors also include the line and column when the
parser provides them.

Numerical capture and compilation errors keep the Rust ``QSError`` category.
For example, ``code="comparison_changed"`` and
``native_type="ComparisonChanged"`` mean that the current inputs would take a
different Rust branch from the recorded calculation. Record the calculation
again for those inputs. Invalid numerical buffer sizes report ``input_count``,
``gradient_count``, or ``buffer_count`` and include the required and supplied
lengths in ``expected`` and ``actual``.

Standard Python protocols behave as usual. Attribute lookup, missing mapping
keys, the end of an iteration, and invalid indexes raise ``AttributeError``,
``KeyError``, ``StopIteration``, and ``IndexError``, so the objects work with
Python containers and inspection functions.

:doc:`guide/first-valuation` covers installation, a first valuation, Python
protocols, and reproducibility. The
`binding README <https://github.com/jmelo11/quantsupport-python/blob/main/README.md>`_
also has source-build instructions and development checks.
