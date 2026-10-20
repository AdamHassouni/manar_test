import unittest
from urllib.parse import parse_qs, urlparse

from fanar.security.oidc import OidcClient, OidcEndpoints


class TestOidc(unittest.TestCase):
    def test_endpoints_from_issuer(self):
        ep = OidcEndpoints("https://idp/realms/fanar")
        self.assertEqual(ep.token, "https://idp/realms/fanar/protocol/openid-connect/token")
        self.assertTrue(ep.authorize.endswith("/auth"))

    def test_authorization_url_has_pkce(self):
        client = OidcClient("https://idp/realms/fanar", "fanar-frontend", "http://localhost:8000/auth/callback")
        url = client.authorization_url(state="st8", code_challenge="chal")
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        self.assertTrue(url.startswith("https://idp/realms/fanar/protocol/openid-connect/auth?"))
        self.assertEqual(q["response_type"], ["code"])
        self.assertEqual(q["client_id"], ["fanar-frontend"])
        self.assertEqual(q["code_challenge_method"], ["S256"])
        self.assertEqual(q["code_challenge"], ["chal"])
        self.assertEqual(q["state"], ["st8"])


if __name__ == "__main__":
    unittest.main()
