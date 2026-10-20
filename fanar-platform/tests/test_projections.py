import unittest
from datetime import date

from fanar.domain.events import Event, EventType
from fanar.ibor.projections import latest_nav, project_positions


def ev(t, fund, payload, d, seq):
    return Event(t, fund, "entity1", payload, d, sequence=seq)


class TestProjections(unittest.TestCase):
    def test_positions_fold_from_ledger(self):
        events = [
            ev(EventType.TRANSACTION_VALIDATED, "3983", {"fund": "3983", "instrument": "BDT1", "quantity": 100, "sign": 1}, date(2026, 10, 15), 1),
            ev(EventType.TRANSACTION_VALIDATED, "3983", {"fund": "3983", "instrument": "BDT1", "quantity": 40, "sign": -1}, date(2026, 10, 16), 2),
            ev(EventType.REPO_OPENED, "3984", {"fund": "3984", "instrument": "BDT2", "quantity": 10, "sign": 1}, date(2026, 10, 16), 3),
        ]
        pos = project_positions(events)
        self.assertEqual(pos[("3983", "BDT1")], 60)
        self.assertEqual(pos[("3984", "BDT2")], 10)

    def test_as_of_is_bitemporal(self):
        events = [
            ev(EventType.TRANSACTION_VALIDATED, "3983", {"fund": "3983", "instrument": "BDT1", "quantity": 100}, date(2026, 10, 15), 1),
            ev(EventType.TRANSACTION_VALIDATED, "3983", {"fund": "3983", "instrument": "BDT1", "quantity": 50}, date(2026, 10, 20), 2),
        ]
        self.assertEqual(project_positions(events, as_of=date(2026, 10, 16))[("3983", "BDT1")], 100)

    def test_latest_nav(self):
        events = [
            ev(EventType.NAV_VALIDATED, "3983", {"fund": "3983", "nav": 1012.5}, date(2026, 10, 18), 1),
            ev(EventType.NAV_VALIDATED, "3983", {"fund": "3983", "nav": 1013.1}, date(2026, 10, 19), 2),
        ]
        self.assertEqual(latest_nav(events, "3983")["nav"], 1013.1)


if __name__ == "__main__":
    unittest.main()
