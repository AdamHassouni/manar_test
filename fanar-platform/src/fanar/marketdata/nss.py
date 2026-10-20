"""Nelson-Siegel-Svensson (NSS) yield curve — pure math, unit-tested (no numpy needed).

Zero rate (continuous comp) at maturity t (years):

    y(t) = b0
         + b1 * L1(t, tau1)
         + b2 * L2(t, tau1)
         + b3 * L2(t, tau2)

with L1(t, τ) = (1 - e^{-t/τ}) / (t/τ)          (level→slope loading)
     L2(t, τ) = (1 - e^{-t/τ}) / (t/τ) - e^{-t/τ}   (curvature loading)

Limits: y(0) = b0 + b1 ; y(∞) = b0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NssParams:
    beta0: float
    beta1: float
    beta2: float
    beta3: float
    tau1: float
    tau2: float


def _loading1(t: float, tau: float) -> float:
    x = t / tau
    if x == 0:
        return 1.0
    return (1.0 - math.exp(-x)) / x


def _loading2(t: float, tau: float) -> float:
    x = t / tau
    if x == 0:
        return 0.0
    return (1.0 - math.exp(-x)) / x - math.exp(-x)


def zero_rate(p: NssParams, t: float) -> float:
    """Continuously-compounded zero rate at maturity `t` years (t >= 0)."""
    if t < 0:
        raise ValueError("maturity t must be >= 0")
    return (
        p.beta0
        + p.beta1 * _loading1(t, p.tau1)
        + p.beta2 * _loading2(t, p.tau1)
        + p.beta3 * _loading2(t, p.tau2)
    )


def discount_factor(p: NssParams, t: float) -> float:
    """Discount factor exp(-y(t) * t) for maturity `t` years."""
    return math.exp(-zero_rate(p, t) * t)


def zero_curve(p: NssParams, tenors: list[float]) -> list[tuple[float, float]]:
    """Convenience: [(t, zero_rate)] over the given tenors."""
    return [(t, zero_rate(p, t)) for t in tenors]
