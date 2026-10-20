import unittest

from fanar.marketdata.fit import fit_nss
from fanar.marketdata.nss import NssParams, zero_rate

TENORS = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30]


class TestFitNss(unittest.TestCase):
    def test_recovers_the_curve(self):
        true = NssParams(0.03, -0.01, 0.02, 0.01, 1.5, 5.0)
        points = [(t, zero_rate(true, t)) for t in TENORS]
        fitted = fit_nss(points)
        for t in TENORS:
            self.assertAlmostEqual(zero_rate(fitted, t), zero_rate(true, t), places=3)


if __name__ == "__main__":
    unittest.main()
