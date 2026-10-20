import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from fanar.domain.events import Event, EventType
from fanar.ibor.event_store import DuplicateEventError, InMemoryEventStore


def _evt(**kw) -> Event:
    base = dict(
        type=EventType.TRANSACTION_VALIDATED, aggregate_id="3983", tenant="entity1",
        payload={"fund": "3983", "instrument": "X", "quantity": 10}, effective_date=date(2026, 10, 19),
    )
    base.update(kw)
    return Event(**base)


class TestEventStore(unittest.TestCase):
    def test_append_assigns_monotonic_sequence(self):
        s = InMemoryEventStore()
        self.assertEqual(s.append(_evt()).sequence, 1)
        self.assertEqual(s.append(_evt()).sequence, 2)
        self.assertEqual(len(s.all()), 2)

    def test_stream_filters_by_aggregate(self):
        s = InMemoryEventStore()
        s.append(_evt(aggregate_id="3983"))
        s.append(_evt(aggregate_id="3984"))
        self.assertEqual(len(s.stream("3983")), 1)

    def test_idempotency_blocks_double_book(self):
        s = InMemoryEventStore()
        s.append(_evt(idempotency_key="k1"))
        with self.assertRaises(DuplicateEventError):
            s.append(_evt(idempotency_key="k1"))

    def test_events_are_immutable(self):
        e = _evt()
        with self.assertRaises(FrozenInstanceError):
            e.payload = {}   # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
