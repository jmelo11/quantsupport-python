"""Explicit, exhaustively checked topic navigation over public binding symbols."""

from pathlib import Path

from python_api import declarations
from sphinx.errors import ExtensionError

PYTHON_EXCEPTIONS = "QuantSupportError QuantSupportTypeError QuantSupportValueError QuantSupportStateError QuantSupportIOError QuantSupportNotImplementedError UnresolvedProductErr".split()


PYTHON_SECTIONS = {
    "time": {
        "Dates and Periods": "Date DateTime Period TimeUnit",
        "Calendars": "Calendar UnitedStatesMarket BrazilMarket AustraliaMarket CanadaMarket NewZealandMarket SouthKoreaMarket ChinaMarket JointCalendarRule",
        "Schedules and IMM": "Schedule IMM DateGenerationRule BusinessDayConvention",
        "Accrual and Frequency": "DayCounter Compounding Frequency",
    },
    "market": {
        "Currencies and Indices": "Currency MarketIndex",
        "Quotes, Fixings, and FX": "QuoteStore FixingStore FxStore Level",
        "Historical Snapshots": "SnapshotSelectionRule SnapshotSelector MarketSnapshot MarketSnapshotStore",
        "Forward Markets": "ForwardMarketConfiguration",
        "Curve Construction": "CurveConfiguration CreditCurveConfiguration Interpolator",
        "Yield Curves": "DiscountCurve ZeroRateTermStructure TenorBasedZeroRateTermStructure",
        "Volatility": "VolatilitySurface VolatilityCube VolatilitySurfaceConfiguration VolatilityCubeConfiguration VolatilityType SmileType",
        "Simulation": "Simulation SimulationConfiguration",
    },
    "instruments": {
        "Base Types and Direction": "Instrument Side",
        "Interest Rates": "InterestRate Swap BasisSwap CrossCurrencySwap FixFloatCrossCurrencySwap RateFutures",
        "Rate Options": "EuropeanSwaption SwaptionType CapFloor CapFloorType CapletFloorlet CapletFloorletType",
        "Fixed Income": "FixedRateBond FloatingRateNote FixedRateDeposit SteppedCouponBond CallScheduleEntry PaymentStructure",
        "Loans and Prepayment": "Loan LoanRepaymentStructure PrepaymentModelConfiguration",
        "Coupons and Payoffs": "FixedRateCoupon FloatingRateCoupon OptionEmbeddedCoupon PayoffOps",
        "Foreign Exchange": "FxForward FxOption",
        "Equity and Credit": "EquityForward EquityOption OptionType CreditDefaultSwap",
        "Scripting": "ScriptedProduct",
        "Instrument Makers": "MakeInstrument MakeSwap MakeFloatFloatCrossCurrencySwap MakeCrossCurrencySwap MakeBasisSwap MakeFixFloatCrossCurrencySwap MakeFixedRateBond MakeSteppedCouponBond MakeFloatingRateNote MakeFixedRateDeposit MakeLoan MakeFxForward MakeFxEuropeanOption MakeFxOption MakeEquityEuropeanOption MakeEquityOption MakeCreditDefaultSwap MakeCapFloor MakeCapletFloorlet MakeRateFutures MakeSwaption MakeEuropeanSwaption MakeEquityForward MakeScriptedProduct MakeTrade",
    },
    "pricing": {
        "Positions and Requests": "Trade Portfolio Request BondPricingAnchor",
        "Contexts and Results": "PricingContext RiskContext ZeroRateRisk EvaluationResults",
        "Pricers and Policies": "PricerConfiguration SingleCurveCSADiscountPolicy FixedIncomeDiscountPolicy",
        "Python Extension Interfaces": "Pricer MarketDataProvider Evaluator",
    },
    "risk": {
        "Scenarios and Shocks": "Scenario Shock ScenarioType",
        "Collateral and Netting": "CsaTerms NettingSet",
        "Exposure and XVA": "ExposureProfile XvaConfig XvaResult",
    },
}

DOMAIN_TITLES = {
    "time": "Time",
    "market": "Market Data",
    "instruments": "Instruments",
    "pricing": "Pricing",
    "risk": "Risk and XVA",
}


def slug(title):
    return title.lower().replace(",", "").replace(" ", "-")


def python_sections(module):
    domain = module.rsplit(".", 1)[-1]
    return [
        (title, f"/python/sections/{domain}/{slug(title)}")
        for title in PYTHON_SECTIONS.get(domain, {})
    ]


def generate_python_navigation(app):
    public = {name for name in declarations() if "._" not in name}
    assigned = [f"quantsupport.{name}" for name in PYTHON_EXCEPTIONS]
    for domain, sections in PYTHON_SECTIONS.items():
        output = Path(app.srcdir) / "python/sections" / domain
        output.mkdir(parents=True, exist_ok=True)
        for title, names in sections.items():
            classes = [f"quantsupport.{domain}.{name}" for name in names.split()]
            assigned.extend(classes)
            lines = [title, "=" * len(title), "", ".. toctree::", "   :maxdepth: 1", ""]
            lines.extend(
                f"   {name.rsplit('.', 1)[-1]} </autoapi/{name.replace('.', '/')}>"
                for name in classes
            )
            lines.extend(["", ".. autoapisummary::", ""])
            lines.extend(f"   {name}" for name in classes)
            if domain == "time" and title == "Calendars":
                lines.extend(
                    [
                        "",
                        "Native Calendar Variants",
                        "------------------------",
                        "",
                        "All native calendar variants are available through :py:class:`quantsupport.time.Calendar`.",
                        "Country calendars are values of this class, not separate Python classes.",
                        "",
                        ".. list-table::",
                        "   :header-rows: 1",
                        "",
                        "   * - Rust calendar",
                        "     - Python declaration",
                    ]
                )
                for native, expression in (
                    ("NullCalendar", "Calendar.NullCalendar"),
                    ("WeekendsOnly", "Calendar.WeekendsOnly"),
                    ("TARGET", "Calendar.TARGET"),
                    ("UnitedKingdom", "Calendar.UnitedKingdom"),
                    ("Japan", "Calendar.Japan"),
                    ("Chile", "Calendar.Chile"),
                    (
                        "UnitedStates",
                        "Calendar.UnitedStates(market=UnitedStatesMarket.Sofr)",
                    ),
                    ("Brazil", "Calendar.Brazil(market=BrazilMarket.Settlement)"),
                    (
                        "Australia",
                        "Calendar.Australia(market=AustraliaMarket.Settlement)",
                    ),
                    ("Canada", "Calendar.Canada(market=CanadaMarket.Settlement)"),
                    (
                        "NewZealand",
                        "Calendar.NewZealand(market=NewZealandMarket.Wellington)",
                    ),
                    (
                        "SouthKorea",
                        "Calendar.SouthKorea(market=SouthKoreaMarket.Settlement)",
                    ),
                    ("China", "Calendar.China(market=ChinaMarket.IB)"),
                    ("Switzerland", "Calendar.Switzerland"),
                    ("Norway", "Calendar.Norway"),
                    ("Sweden", "Calendar.Sweden"),
                    ("Denmark", "Calendar.Denmark"),
                    ("SouthAfrica", "Calendar.SouthAfrica"),
                    (
                        "JointCalendar",
                        "Calendar.JointCalendar(calendars=[Calendar.TARGET, Calendar.Japan])",
                    ),
                ):
                    lines.extend([f"   * - {native}", f"     - ``{expression}``"])
                lines.extend(
                    [
                        "",
                        "Calendar Operations",
                        "-------------------",
                        "",
                        "* Business-day queries: :py:meth:`~quantsupport.time.Calendar.is_business_day`, :py:meth:`~quantsupport.time.Calendar.is_holiday`, and :py:meth:`~quantsupport.time.Calendar.is_weekend`.",
                        "* Date adjustment: :py:meth:`~quantsupport.time.Calendar.adjust` and :py:meth:`~quantsupport.time.Calendar.advance`.",
                        "* Business month-end: :py:meth:`~quantsupport.time.Calendar.end_of_month` and :py:meth:`~quantsupport.time.Calendar.is_end_of_month`.",
                        "* Date ranges: :py:meth:`~quantsupport.time.Calendar.business_days_between`, :py:meth:`~quantsupport.time.Calendar.holiday_list`, and :py:meth:`~quantsupport.time.Calendar.business_day_list`.",
                        "* Independent overrides: :py:meth:`~quantsupport.time.Calendar.with_added_holiday` and :py:meth:`~quantsupport.time.Calendar.with_removed_holiday` return new values; they do not mutate shared calendar attributes.",
                        "",
                    ]
                )
            (output / f"{slug(title)}.rst").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
    if len(assigned) != len(set(assigned)) or set(assigned) != public:
        raise ExtensionError(
            f"Python navigation must cover each public class once; missing={public - set(assigned)}, unknown={set(assigned) - public}"
        )
