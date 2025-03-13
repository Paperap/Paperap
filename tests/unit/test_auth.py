"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_auth.py
        Project: paperap
        Created: 2025-03-13
        Version: 0.0.7
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-13     By Jess Mann

"""
import unittest
from paperap.auth import TokenAuth, BasicAuth

class TestTokenAuth(unittest.TestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    def test_get_auth_headers(self):
        auth = TokenAuth(token="test_token")
        self.assertEqual(auth.get_auth_headers(), {"Authorization": "Token test_token"})

    def test_get_auth_params(self):
        auth = TokenAuth(token="test_token")
        self.assertEqual(auth.get_auth_params(), {})

    def test_empty_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="")

    def test_whitespace_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="   ")

class TestBasicAuth(unittest.TestCase):
    def test_get_auth_headers(self):
        auth = BasicAuth(username="user", password="pass")
        self.assertEqual(auth.get_auth_headers(), {})

    def test_get_auth_params(self):
        auth = BasicAuth(username="user", password="pass")
        self.assertEqual(auth.get_auth_params(), {"auth": ("user", "pass")})

if __name__ == "__main__":
    unittest.main()
