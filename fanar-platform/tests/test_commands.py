import unittest
from datetime import date

from fanar.ibor.commands import RecordTransaction, record_transaction
from fanar.ibor.event_store import DuplicateEventError, InMemoryEventStore
from fanar.ibor.projections import project_positions


class TestRecordTransaction(unittest.TestCase):
    def test_append_then_project(self):
        store = InMemoryEventStore()
        e1 = record_transaction(store, RecordTransaction("3983", "BDT1", 100, date(2026, 10, 19)))
        self.assertEqual(e1.sequence, 1)
        self.assertEqual(e1.actor, None)
        record_transaction(store, RecordTransaction("3983", "BDT1", 40, date(2026, 10, 19), sign=-1))
        pos = project_positions(store.all())
        self.assertEqual(pos[("3983", "BDT1")], 60)

    def test_idempotency_key_blocks_replay(self):
        store = InMemoryEventStore()
        record_transaction(store, RecordTransaction("3983", "BDT1", 100, date(2026, 10, 19), idempotency_key="k1"))
        with self.assertRaises(DuplicateEventError):
            record_transaction(store, RecordTransaction("3983", "BDT1", 100, date(2026, 10, 19), idempotency_key="k1"))


if __name__ == "__main__":
    unittest.main()
