import unittest
from datetime import date

from fanar.domain.events import Event, EventType
from fanar.ibor.projections import position_deltas


def ev(t: EventType, payload: dict) -> Event:
    return Event(t, payload.get("fund", "X"), "entity1", payload, date(2026, 10, 19))


class TestPositionDeltas(unittest.TestCase):
    def test_validated_adds(self):
        d = position_deltas(ev(EventType.TRANSACTION_VALIDATED,
                               {"fund": "3983", "instrument": "B", "quantity": 100, "sign": 1}))
        self.assertEqual(d, {("3983", "B"): 100})

    def test_repo_open_respects_sign(self):
        d = position_deltas(ev(EventType.REPO_OPENED,
                               {"fund": "3984", "instrument": "B", "quantity": 10, "sign": -1}))
        self.assertEqual(d, {("3984", "B"): -10})

    def test_repo_close_reduces(self):
        d = position_deltas(ev(EventType.REPO_CLOSED, {"fund": "3983", "instrument": "B", "quantity": 40}))
        self.assertEqual(d, {("3983", "B"): -40})

    def test_cancel_reverses(self):
        d = position_deltas(ev(EventType.TRANSACTION_CANCELLED,
                               {"fund": "3983", "instrument": "B", "quantity": 100, "sign": 1}))
        self.assertEqual(d, {("3983", "B"): -100})

    def test_non_position_event_is_noop(self):
        self.assertEqual(position_deltas(ev(EventType.PRICE_OBSERVED, {"instrument": "B"})), {})


if __name__ == "__main__":
    unittest.main()
