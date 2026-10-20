import unittest

from fanar.acl.token_provider import ManarTokenProvider


class FakeSecrets:
    def get(self, name: str) -> str:
        return {"manar_username": "u", "manar_password": "p"}[name]


class TestManarTokenProvider(unittest.TestCase):
    def test_caches_until_expiry_then_refetches(self):
        calls: list[dict] = []
        now = [1000.0]

        def fetch(form: dict) -> dict:
            calls.append(form)
            return {"access_token": f"tok{len(calls)}", "expires_in": 100}

        p = ManarTokenProvider(token_url="x", client_id="manar-frontend", secrets=FakeSecrets(),
                               leeway_seconds=10, clock=lambda: now[0], fetch=fetch)
        self.assertEqual(p(), "tok1")
        now[0] = 1050.0                 # inside validity (expiry 1100, minus 10 leeway = 1090)
        self.assertEqual(p(), "tok1")   # cached, no refetch
        self.assertEqual(len(calls), 1)
        now[0] = 1095.0                 # past the leeway boundary
        self.assertEqual(p(), "tok2")   # refetched
        self.assertEqual(len(calls), 2)

    def test_sends_password_grant_with_secret_credentials(self):
        captured: dict = {}

        def fetch(form: dict) -> dict:
            captured.update(form)
            return {"access_token": "t", "expires_in": 60}

        ManarTokenProvider(token_url="x", client_id="manar-frontend",
                           secrets=FakeSecrets(), fetch=fetch)()
        self.assertEqual(captured["grant_type"], "password")
        self.assertEqual(captured["client_id"], "manar-frontend")
        self.assertEqual(captured["username"], "u")
        self.assertEqual(captured["password"], "p")


if __name__ == "__main__":
    unittest.main()
