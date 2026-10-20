import unittest

from fanar.acl.guard import ReadOnlyViolation, enforce, is_read

Q = "http://m/api/portfolio-management/query/repo/list"
CMD = "http://m/api/portfolio-management/command/repo"
TOKEN = "http://m/realms/manar/protocol/openid-connect/token"


class TestReadOnlyGuard(unittest.TestCase):
    def test_get_is_read(self):
        self.assertTrue(is_read("GET", "http://m/api/administration/query/list/titres"))

    def test_post_to_query_is_read(self):
        self.assertTrue(is_read("POST", Q))

    def test_command_is_blocked(self):
        self.assertFalse(is_read("POST", CMD))
        with self.assertRaises(ReadOnlyViolation):
            enforce("POST", CMD)

    def test_auth_flow_allowed(self):
        self.assertTrue(is_read("POST", TOKEN))

    def test_authorized_write_passes(self):
        enforce("POST", CMD, authorized_write=True)  # must not raise


if __name__ == "__main__":
    unittest.main()
