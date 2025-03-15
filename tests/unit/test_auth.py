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

from pydantic import ValidationError
from paperap.auth import TokenAuth, BasicAuth

class TestTokenAuth(unittest.TestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    def test_get_auth_headers(self):
        auth = TokenAuth(token="40characterslong40characterslong40charac")
        self.assertEqual(auth.get_auth_headers(), {"Authorization": "Token 40characterslong40characterslong40charac"})

    def test_get_auth_params(self):
        auth = TokenAuth(token="40characterslong40characterslong40charac")
        self.assertEqual(auth.get_auth_params(), {})

    def test_no_params(self):
        with self.assertRaises(ValueError):
            TokenAuth() # type: ignore

    def test_empty_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="")

    def test_whitespace_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="   ")

    def test_strip_token(self):
        auth = TokenAuth(token=" 40characterslong40characterslong40charac ")
        self.assertEqual(auth.token, "40characterslong40characterslong40charac")

    def test_strip_token_middle_whitespace(self):
        with self.assertRaises(ValueError):
            TokenAuth(token=" 40charact  erslong40 characterslong40charac ")

    def test_short_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="20characterslong20ch")

    def test_short_token_with_padding(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="          40characterslong40ch          ")

    def test_long_token(self):
        with self.assertRaises(ValueError):
            TokenAuth(token="80characterslong80characterslong80characterslong80characterslong80characterslong")

class TestBasicAuth(unittest.TestCase):
    def test_get_auth_headers(self):
        auth = BasicAuth(username="user", password="pass")
        self.assertEqual(auth.get_auth_headers(), {})

    def test_get_auth_params(self):
        auth = BasicAuth(username="user", password="pass")
        self.assertEqual(auth.get_auth_params(), {"auth": ("user", "pass")})

if __name__ == "__main__":
    unittest.main()
