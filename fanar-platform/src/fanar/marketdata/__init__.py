"""Market data & curves (Phase 1).

`nss` is the Nelson-Siegel-Svensson yield-curve model (pure math); `kalman` is a linear Kalman
filter used for the Dynamic-NSS factor dynamics; `fit` calibrates NSS to observed rates (scipy).
This is Sterling's existing edge — modelling the BAM curve, not just storing rates.
"""
