"""File loading for the notebooks; pricing stays in the notebook cells.

Paths are relative to this module, never the shell's working directory. The
market is the repository's illustrative 2026-02-24 Hull-White snapshot, not a
live feed. This module is example code, not part of the installed package.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import quantsupport as qs

EXAMPLES = Path(__file__).resolve().parents[1]
MARKET_DATA = EXAMPLES / "data" / "hullwhite"


@dataclass
class MarketInputs:
    """Raw market inputs; a PricingContext builds curves and surfaces from them."""

    quotes: qs.QuoteStore
    curves: list[qs.CurveConfiguration]
    volatility_surfaces: list[qs.VolatilitySurfaceConfiguration]
    csa_policy: qs.SingleCurveCSADiscountPolicy


def load_market():
    """Load fresh typed inputs from the shared USD/SOFR example data."""
    return MarketInputs(
        quotes=qs.QuoteStore.from_dict(
            json.loads(Path(MARKET_DATA / "quotes.json").read_text(encoding="utf-8"))
        ),
        curves=qs.CurveConfiguration.from_dict_list(
            json.loads(
                Path(MARKET_DATA / "curve_specs.json").read_text(encoding="utf-8")
            )
        ),
        volatility_surfaces=qs.VolatilitySurfaceConfiguration.from_dict_list(
            json.loads(Path(MARKET_DATA / "vol_specs.json").read_text(encoding="utf-8"))
        ),
        csa_policy=qs.SingleCurveCSADiscountPolicy(
            qs.Currency.USD, qs.MarketIndex.SOFR
        ),
    )


def read_configuration(scope, filename):
    """Read an editable JSON configuration from one example folder."""
    return json.loads(
        (EXAMPLES / scope / "data" / filename).read_text(encoding="utf-8")
    )
