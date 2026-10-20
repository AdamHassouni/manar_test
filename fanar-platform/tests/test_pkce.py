import unittest

from fanar.security.pkce import challenge_for, generate_pkce, generate_verifier, random_token


class TestPkce(unittest.TestCase):
    def test_challenge_is_deterministic_s256(self):
        v = "abc123-verifier"
        self.assertEqual(challenge_for(v), challenge_for(v))
        # Known S256 of the verifier, base64url without padding:
        import base64
        import hashlib
        expected = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(challenge_for(v), expected)

    def test_generate_pkce_pair(self):
        verifier, challenge = generate_pkce()
        self.assertGreaterEqual(len(verifier), 43)
        self.assertEqual(challenge, challenge_for(verifier))
        self.assertNotIn("=", challenge)       # base64url, unpadded

    def test_tokens_are_unique(self):
        self.assertNotEqual(generate_verifier(), generate_verifier())
        self.assertNotEqual(random_token(), random_token())


if __name__ == "__main__":
    unittest.main()
