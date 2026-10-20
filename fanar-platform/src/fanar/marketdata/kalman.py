"""A linear Gaussian Kalman filter (numpy) — for the Dynamic-NSS factor dynamics.

State-space:
    x_k = F x_{k-1} + w,   w ~ N(0, Q)
    z_k = H x_k     + v,   v ~ N(0, R)

Dynamic NSS models the NSS factors (level/slope/curvature) as a VAR(1); this filter is the generic
engine that estimates them through time from observed curves. Used standalone here; the factor model
wiring (F/H/Q/R for the NSS factors) follows in the market-data service.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class KalmanFilter:
    F: np.ndarray    # state transition
    H: np.ndarray    # observation model
    Q: np.ndarray    # process-noise covariance
    R: np.ndarray    # observation-noise covariance
    x: np.ndarray    # state mean
    P: np.ndarray    # state covariance

    def predict(self) -> np.ndarray:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, z) -> np.ndarray:
        z = np.atleast_1d(np.asarray(z, dtype=float))
        y = z - self.H @ self.x                      # innovation
        S = self.H @ self.P @ self.H.T + self.R      # innovation covariance
        K = self.P @ self.H.T @ np.linalg.inv(S)     # Kalman gain
        self.x = self.x + K @ y
        identity = np.eye(self.P.shape[0])
        self.P = (identity - K @ self.H) @ self.P
        return self.x

    def step(self, z) -> np.ndarray:
        self.predict()
        return self.update(z)
