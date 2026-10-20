"""NAV / VL engine — pure, unit-tested.

Given priced holdings + cash + units + fees, compute a `Valuation` (docs/05 §1.7). Bond pricing off
the NSS curve lives in `nav.pricing` (QuantLib). `nav_breaks` is the dual-calc gate — Sterling's
`validation_vl` made native: two independent computations must agree within tolerance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fanar.domain.models import Valuation


@dataclass(frozen=True)
class Holding:
    instrument: str
    quantity: float
    price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.price


def market_value(holdings: list[Holding]) -> float:
    return sum(h.market_value for h in holdings)


def compute_nav(
    *,
    fund: str,
    effective_date: date,
    holdings: list[Holding],
    cash: float,
    units: float,
    fees: float = 0.0,
    currency: str = "MAD",
) -> Valuation:
    gross = market_value(holdings) + cash
    net = gross - fees
    return Valuation(
        fund=fund,
        effective_date=effective_date,
        currency=currency,
        gross_asset=gross,
        net_asset_pre_nav=gross,
        net_asset_post_nav=net,
        nav_per_unit=(net / units if units else 0.0),
        units_pre=units,
        units_post=units,
        management_fees=fees,
        status="draft",
    )


def nav_breaks(primary: Valuation, independent: Valuation, *, tolerance: float = 1e-6) -> float | None:
    """Return the absolute VL difference if it exceeds tolerance (a break), else None."""
    diff = abs(primary.nav_per_unit - independent.nav_per_unit)
    return diff if diff > tolerance else None
