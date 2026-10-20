"""Bond pricing off the NSS curve, using QuantLib — replaces the hand-rolled Excel pricer.

Builds a zero curve by sampling NSS, then prices a fixed-rate bond on it. QuantLib is imported
lazily so modules that don't price bonds don't require it.
"""
from __future__ import annotations

from datetime import date

from fanar.marketdata.nss import NssParams, zero_rate


def price_fixed_rate_bond(
    *,
    valuation_date: date,
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    nss: NssParams,
    frequency: int = 1,
    face: float = 100.0,
) -> float:
    """Clean price of a fixed-rate bond discounted on the NSS zero curve."""
    import QuantLib as ql

    def d(x: date) -> "ql.Date":
        return ql.Date(x.day, x.month, x.year)

    calendar = ql.NullCalendar()
    day_count = ql.Actual365Fixed()
    vd = d(valuation_date)
    ql.Settings.instance().evaluationDate = vd

    tenors = [0.0, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30]
    dates = [calendar.advance(vd, ql.Period(int(round(t * 365)), ql.Days)) for t in tenors]
    rates = [zero_rate(nss, max(t, 1e-8)) for t in tenors]
    curve = ql.ZeroCurve(dates, rates, day_count, calendar, ql.Linear(), ql.Continuous)
    curve.enableExtrapolation()
    handle = ql.YieldTermStructureHandle(curve)

    freq = ql.Annual if frequency == 1 else ql.Semiannual
    schedule = ql.Schedule(
        d(issue_date), d(maturity_date), ql.Period(freq), calendar,
        ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Backward, False,
    )
    bond = ql.FixedRateBond(0, face, schedule, [coupon_rate], day_count)
    bond.setPricingEngine(ql.DiscountingBondEngine(handle))
    return bond.cleanPrice()
