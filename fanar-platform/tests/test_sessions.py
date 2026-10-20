import unittest

from fanar.security.sessions import InMemorySessionStore


class TestSessions(unittest.TestCase):
    def test_create_get_delete(self):
        store = InMemorySessionStore()
        s = store.create({"principal": {"username": "adam"}})
        self.assertIsNotNone(store.get(s.id))
        self.assertEqual(store.get(s.id).data["principal"]["username"], "adam")
        store.delete(s.id)
        self.assertIsNone(store.get(s.id))

    def test_unknown_session(self):
        self.assertIsNone(InMemorySessionStore().get("nope"))

    def test_ttl_expiry(self):
        store = InMemorySessionStore(ttl_seconds=60)
        s = store.create({"x": 1})
        s.created_at -= 10_000          # pretend it is old
        self.assertIsNone(store.get(s.id))


if __name__ == "__main__":
    unittest.main()
