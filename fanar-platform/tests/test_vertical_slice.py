"""End-to-end vertical slice: login (principal) -> read reference (ACL/local) -> record to the
ledger -> audited, with the projection reflecting the result. All offline via in-memory adapters.
"""
import unittest
from datetime import date

from fanar.audit.log import InMemoryAuditLog
from fanar.ibor.commands import RecordTransaction
from fanar.ibor.event_store import InMemoryEventStore
from fanar.ibor.projections import project_positions
from fanar.reference.service import LocalReferenceSource, ReferenceService
from fanar.security.auth import AuthError, Principal
from fanar.services.transactions import UnknownFund, book_transaction


def principal(roles=("front",)) -> Principal:
    return Principal("u1", "adam", "entity1", frozenset(roles))


class TestVerticalSlice(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryEventStore()
        self.reference = ReferenceService(LocalReferenceSource())
        self.audit = InMemoryAuditLog()

    def _book(self, p, cmd):
        return book_transaction(p, cmd, store=self.store, reference=self.reference, audit=self.audit)

    def test_login_read_reference_record_audited(self):
        result = self._book(principal(), RecordTransaction("3983", "BDT1", 100, date(2026, 10, 19)))
        event = result["event"]
        # attributed to the logged-in principal
        self.assertEqual(event.actor, "adam")
        self.assertEqual(event.tenant, "entity1")
        # ledger -> projection
        self.assertEqual(project_positions(self.store.all())[("3983", "BDT1")], 100)
        # audited, linked to the event
        entry = self.audit.recent()[0]
        self.assertEqual(entry.action, "record_transaction")
        self.assertEqual(entry.actor, "adam")
        self.assertEqual(entry.correlation_id, event.event_id)

    def test_unknown_fund_is_rejected(self):
        with self.assertRaises(UnknownFund):
            self._book(principal(), RecordTransaction("9999", "X", 1, date(2026, 10, 19)))
        self.assertEqual(self.store.all(), [])
        self.assertEqual(self.audit.recent(), [])

    def test_requires_maker_checker_role(self):
        with self.assertRaises(AuthError):
            self._book(principal(roles=("viewer",)), RecordTransaction("3983", "BDT1", 1, date(2026, 10, 19)))


if __name__ == "__main__":
    unittest.main()
