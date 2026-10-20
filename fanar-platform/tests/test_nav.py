import unittest
from datetime import date

from fanar.nav.engine import Holding, compute_nav, market_value, nav_breaks


class TestNavEngine(unittest.TestCase):
    def test_compute_nav(self):
        holdings = [Holding("BDT1", 100, 101.5), Holding("BDT2", 50, 99.0)]
        self.assertAlmostEqual(market_value(holdings), 15100.0)
        val = compute_nav(fund="3983", effective_date=date(2026, 10, 19),
                          holdings=holdings, cash=5000.0, units=1000.0, fees=200.0)
        self.assertAlmostEqual(val.gross_asset, 20100.0)       # 15100 + 5000
        self.assertAlmostEqual(val.net_asset_post_nav, 19900.0)  # - 200 fees
        self.assertAlmostEqual(val.nav_per_unit, 19.9)

    def test_dual_calc_gate(self):
        a = compute_nav(fund="f", effective_date=date(2026, 10, 19), holdings=[], cash=1000.0, units=100.0)
        b = compute_nav(fund="f", effective_date=date(2026, 10, 19), holdings=[], cash=1000.5, units=100.0)
        self.assertIsNone(nav_breaks(a, a))
        self.assertIsNotNone(nav_breaks(a, b))


if __name__ == "__main__":
    unittest.main()
