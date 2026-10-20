import unittest
from datetime import date

from fanar.marketdata.nss import NssParams
from fanar.nav.pricing import price_fixed_rate_bond


class TestPricing(unittest.TestCase):
    def test_prices_a_fixed_rate_bond(self):
        nss = NssParams(0.03, -0.01, 0.02, 0.01, 1.5, 5.0)
        price = price_fixed_rate_bond(
            valuation_date=date(2026, 10, 19), issue_date=date(2026, 10, 19),
            maturity_date=date(2031, 10, 19), coupon_rate=0.03, nss=nss,
        )
        self.assertTrue(0.0 < price < 200.0)

    def test_zero_coupon_prices_below_face(self):
        flat = NssParams(0.03, 0.0, 0.0, 0.0, 1.5, 5.0)   # flat 3%
        price = price_fixed_rate_bond(
            valuation_date=date(2026, 10, 19), issue_date=date(2026, 10, 19),
            maturity_date=date(2031, 10, 19), coupon_rate=0.0, nss=flat,
        )
        self.assertLess(price, 100.0)


if __name__ == "__main__":
    unittest.main()
