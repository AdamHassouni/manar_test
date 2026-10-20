import unittest
from datetime import datetime, timezone

from fanar.audit.log import AuditEntry, InMemoryAuditLog


class TestAuditLog(unittest.TestCase):
    def test_record_assigns_sequence_and_recent_is_newest_first(self):
        log = InMemoryAuditLog()
        log.record(AuditEntry(actor="adam", action="record_transaction", target="3983",
                              at=datetime.now(timezone.utc)))
        second = log.record(AuditEntry(actor="amine", action="validate", target="3984",
                                       at=datetime.now(timezone.utc)))
        self.assertEqual(second.sequence, 2)
        recent = log.recent()
        self.assertEqual(recent[0].actor, "amine")   # newest first
        self.assertEqual(len(recent), 2)


if __name__ == "__main__":
    unittest.main()
