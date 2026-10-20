"""Calibrate NSS parameters to observed (tenor, zero-rate) points — nonlinear least squares (scipy)."""
from __future__ import annotations

from fanar.marketdata.nss import NssParams, zero_rate


def fit_nss(points: list[tuple[float, float]], *, initial: list[float] | None = None,
            max_nfev: int = 10000) -> NssParams:
    """Fit NSS to [(t_years, zero_rate)] points. Returns the calibrated parameters."""
    import numpy as np
    from scipy.optimize import least_squares

    ts = [float(t) for t, _ in points]
    ys = [float(y) for _, y in points]
    if initial is None:
        level = sum(ys) / len(ys)
        slope = ys[0] - ys[-1] if len(ys) > 1 else 0.0
        initial = [level, slope, 0.0, 0.0, 1.5, 5.0]
    lower = [-1.0, -1.0, -1.0, -1.0, 1e-3, 1e-3]
    upper = [1.0, 1.0, 1.0, 1.0, 30.0, 30.0]

    def residuals(x):
        p = NssParams(*x)
        return np.array([zero_rate(p, t) for t in ts]) - np.array(ys)

    result = least_squares(residuals, initial, bounds=(lower, upper), max_nfev=max_nfev)
    return NssParams(*(float(v) for v in result.x))
