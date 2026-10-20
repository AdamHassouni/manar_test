import unittest

import numpy as np

from fanar.marketdata.kalman import KalmanFilter


class TestKalman(unittest.TestCase):
    def test_tracks_a_noisy_constant(self):
        kf = KalmanFilter(
            F=np.array([[1.0]]), H=np.array([[1.0]]),
            Q=np.array([[1e-5]]), R=np.array([[1.0]]),
            x=np.array([0.0]), P=np.array([[1.0]]),
        )
        true = 5.0
        rng = np.random.default_rng(0)
        est = kf.x
        for _ in range(300):
            est = kf.step([true + rng.normal(0.0, 1.0)])
        self.assertLess(abs(float(est[0]) - true), 0.4)


if __name__ == "__main__":
    unittest.main()
