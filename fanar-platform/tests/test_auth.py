import unittest

from fanar.security.auth import AuthError, principal_from_claims


class TestAuthRbac(unittest.TestCase):
    def test_roles_from_realm_access(self):
        p = principal_from_claims({
            "sub": "u1", "preferred_username": "adam", "tenant": "entity1",
            "realm_access": {"roles": ["front", "viewer"]},
        })
        self.assertEqual(p.username, "adam")
        self.assertEqual(p.tenant, "entity1")
        self.assertTrue(p.has_any("front"))
        p.require("front")  # must not raise

    def test_missing_role_raises(self):
        p = principal_from_claims({"sub": "u1", "realm_access": {"roles": ["viewer"]}})
        with self.assertRaises(AuthError):
            p.require("back")


if __name__ == "__main__":
    unittest.main()
