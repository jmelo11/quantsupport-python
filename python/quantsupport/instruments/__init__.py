"""Product specifications, coupons, loan terms, and payoff scripts."""

from ..quantsupport import (
    BasisSwap as BasisSwap,
)
from ..quantsupport import (
    CallScheduleEntry as CallScheduleEntry,
)
from ..quantsupport import (
    CapFloor as CapFloor,
)
from ..quantsupport import (
    CapFloorType as CapFloorType,
)
from ..quantsupport import (
    CapletFloorlet as CapletFloorlet,
)
from ..quantsupport import (
    CapletFloorletType as CapletFloorletType,
)
from ..quantsupport import (
    CreditDefaultSwap as CreditDefaultSwap,
)
from ..quantsupport import (
    CrossCurrencySwap as CrossCurrencySwap,
)
from ..quantsupport import (
    EquityForward as EquityForward,
)
from ..quantsupport import (
    EquityOption as EquityOption,
)
from ..quantsupport import (
    EuropeanSwaption as EuropeanSwaption,
)
from ..quantsupport import (
    FixedRateBond as FixedRateBond,
)
from ..quantsupport import (
    FixedRateCoupon as FixedRateCoupon,
)
from ..quantsupport import (
    FixedRateDeposit as FixedRateDeposit,
)
from ..quantsupport import (
    FixFloatCrossCurrencySwap as FixFloatCrossCurrencySwap,
)
from ..quantsupport import (
    FloatingRateCoupon as FloatingRateCoupon,
)
from ..quantsupport import (
    FloatingRateNote as FloatingRateNote,
)
from ..quantsupport import (
    FxForward as FxForward,
)
from ..quantsupport import (
    FxOption as FxOption,
)
from ..quantsupport import (
    Instrument as Instrument,
)
from ..quantsupport import (
    InterestRate as InterestRate,
)
from ..quantsupport import (
    Loan as Loan,
)
from ..quantsupport import (
    LoanRepaymentStructure as LoanRepaymentStructure,
)
from ..quantsupport import (
    OptionEmbeddedCoupon as OptionEmbeddedCoupon,
)
from ..quantsupport import (
    OptionType as OptionType,
)
from ..quantsupport import (
    PaymentStructure as PaymentStructure,
)
from ..quantsupport import (
    PayoffOps as PayoffOps,
)
from ..quantsupport import (
    PrepaymentModelConfiguration as PrepaymentModelConfiguration,
)
from ..quantsupport import (
    RateFutures as RateFutures,
)
from ..quantsupport import (
    ScriptedProduct as ScriptedProduct,
)
from ..quantsupport import (
    Side as Side,
)
from ..quantsupport import (
    SteppedCouponBond as SteppedCouponBond,
)
from ..quantsupport import (
    Swap as Swap,
)
from ..quantsupport import (
    SwaptionType as SwaptionType,
)

__all__ = [
    "Instrument",
    "Side",
    "OptionType",
    "SwaptionType",
    "CapFloorType",
    "CapletFloorletType",
    "PaymentStructure",
    "LoanRepaymentStructure",
    "PrepaymentModelConfiguration",
    "Loan",
    "EquityForward",
    "EuropeanSwaption",
    "Swap",
    "CrossCurrencySwap",
    "BasisSwap",
    "FixFloatCrossCurrencySwap",
    "FixedRateBond",
    "InterestRate",
    "PayoffOps",
    "FixedRateCoupon",
    "FloatingRateCoupon",
    "OptionEmbeddedCoupon",
    "CallScheduleEntry",
    "SteppedCouponBond",
    "FloatingRateNote",
    "FixedRateDeposit",
    "FxForward",
    "FxOption",
    "EquityOption",
    "CreditDefaultSwap",
    "CapFloor",
    "CapletFloorlet",
    "RateFutures",
    "ScriptedProduct",
    "MakeInstrument",
    "MakeSwap",
    "MakeFloatFloatCrossCurrencySwap",
    "MakeCrossCurrencySwap",
    "MakeBasisSwap",
    "MakeFixFloatCrossCurrencySwap",
    "MakeFixedRateBond",
    "MakeSteppedCouponBond",
    "MakeFloatingRateNote",
    "MakeFixedRateDeposit",
    "MakeLoan",
    "MakeFxForward",
    "MakeFxEuropeanOption",
    "MakeFxOption",
    "MakeEquityEuropeanOption",
    "MakeEquityOption",
    "MakeCreditDefaultSwap",
    "MakeCapFloor",
    "MakeCapletFloorlet",
    "MakeRateFutures",
    "MakeSwaption",
    "MakeEuropeanSwaption",
    "MakeEquityForward",
    "MakeScriptedProduct",
    "MakeTrade",
]

# Runtime counterpart of the generic maker type parameter in the public stubs.
from typing import TypeVar as _TypeVar

from ..quantsupport import (
    MakeBasisSwap as MakeBasisSwap,
)
from ..quantsupport import (
    MakeCapFloor as MakeCapFloor,
)
from ..quantsupport import (
    MakeCapletFloorlet as MakeCapletFloorlet,
)
from ..quantsupport import (
    MakeCreditDefaultSwap as MakeCreditDefaultSwap,
)
from ..quantsupport import (
    MakeCrossCurrencySwap as MakeCrossCurrencySwap,
)
from ..quantsupport import (
    MakeEquityEuropeanOption as MakeEquityEuropeanOption,
)
from ..quantsupport import (
    MakeEquityForward as MakeEquityForward,
)
from ..quantsupport import (
    MakeEquityOption as MakeEquityOption,
)
from ..quantsupport import (
    MakeEuropeanSwaption as MakeEuropeanSwaption,
)
from ..quantsupport import (
    MakeFixedRateBond as MakeFixedRateBond,
)
from ..quantsupport import (
    MakeFixedRateDeposit as MakeFixedRateDeposit,
)
from ..quantsupport import (
    MakeFixFloatCrossCurrencySwap as MakeFixFloatCrossCurrencySwap,
)
from ..quantsupport import (
    MakeFloatFloatCrossCurrencySwap as MakeFloatFloatCrossCurrencySwap,
)
from ..quantsupport import (
    MakeFloatingRateNote as MakeFloatingRateNote,
)
from ..quantsupport import (
    MakeFxEuropeanOption as MakeFxEuropeanOption,
)
from ..quantsupport import (
    MakeFxForward as MakeFxForward,
)
from ..quantsupport import (
    MakeFxOption as MakeFxOption,
)
from ..quantsupport import (
    MakeInstrument as MakeInstrument,
)
from ..quantsupport import (
    MakeLoan as MakeLoan,
)
from ..quantsupport import (
    MakeRateFutures as MakeRateFutures,
)
from ..quantsupport import (
    MakeScriptedProduct as MakeScriptedProduct,
)
from ..quantsupport import (
    MakeSteppedCouponBond as MakeSteppedCouponBond,
)
from ..quantsupport import (
    MakeSwap as MakeSwap,
)
from ..quantsupport import (
    MakeSwaption as MakeSwaption,
)
from ..quantsupport import (
    MakeTrade as MakeTrade,
)

ProductT = _TypeVar("ProductT")
