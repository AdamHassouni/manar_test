import unittest

from fanar.marketdata.nss import NssParams, discount_factor, zero_rate

P = NssParams(beta0=0.03, beta1=-0.01, beta2=0.02, beta3=0.01, tau1=1.5, tau2=5.0)


class TestNss(unittest.TestCase):
    def test_short_end_limit(self):
        # y(0) -> beta0 + beta1
        self.assertAlmostEqual(zero_rate(P, 1e-9), P.beta0 + P.beta1, places=4)

    def test_long_end_limit(self):
        # y(inf) -> beta0
        self.assertAlmostEqual(zero_rate(P, 300.0), P.beta0, places=3)

    def test_discount_factor(self):
        self.assertAlmostEqual(discount_factor(P, 0.0), 1.0)
        self.assertLess(discount_factor(P, 10.0), 1.0)

    def test_negative_maturity_raises(self):
        with self.assertRaises(ValueError):
            zero_rate(P, -1.0)


if __name__ == "__main__":
    unittest.main()
