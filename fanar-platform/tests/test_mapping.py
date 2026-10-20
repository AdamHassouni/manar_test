import unittest
from datetime import date

from fanar.domain.events import Event, EventType
from fanar.ibor.mapping import event_to_columns, row_to_event


class TestMapping(unittest.TestCase):
    def test_round_trip_event_row(self):
        e = Event(
            EventType.REPO_OPENED, "3983", "entity1",
            {"fund": "3983", "instrument": "BDT1", "quantity": 100},
            date(2026, 10, 19), actor="ADAM", idempotency_key="k1",
        )
        cols = event_to_columns(e)
        self.assertNotIn("sequence", cols)        # DB assigns it
        self.assertEqual(cols["type"], "repo.opened")

        row = dict(cols)
        row["sequence"] = 7                        # simulate the stored row
        back = row_to_event(row)

        self.assertEqual(back.type, EventType.REPO_OPENED)
        self.assertEqual(back.aggregate_id, "3983")
        self.assertEqual(back.payload["quantity"], 100)
        self.assertEqual(back.effective_date, date(2026, 10, 19))
        self.assertEqual(back.actor, "ADAM")
        self.assertEqual(back.idempotency_key, "k1")
        self.assertEqual(back.sequence, 7)


if __name__ == "__main__":
    unittest.main()
