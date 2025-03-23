

import unittest
from unittest import mock

from pydantic import ValidationError

from paperap.auth import AuthBase, BasicAuth, TokenAuth


class TestAuthBase(unittest.TestCase):
    """Test the abstract AuthBase class."""

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        with self.assertRaises(TypeError):
            AuthBase()  # type: ignore

    def test_with_concrete_implementation(self):
        """Test with a concrete implementation."""
        class ConcreteAuth(AuthBase):
            def get_auth_headers(self) -> dict[str, str]:
                return {"X-Test": "value"}

            def get_auth_params(self) -> dict[str, str]:
                return {"param": "value"}

        auth = ConcreteAuth()
        self.assertEqual(auth.get_auth_headers(), {"X-Test": "value"})
        self.assertEqual(auth.get_auth_params(), {"param": "value"})


class TestTokenAuth(unittest.TestCase):
    """Test the TokenAuth class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_token = "40characterslong40characterslong40charac"
        self.auth = TokenAuth(token=self.valid_token)

    def test_initialization(self):
        """Test basic initialization with valid token."""
        self.assertEqual(self.auth.token, self.valid_token)

    def test_get_auth_headers(self):
        """Test that auth headers are correctly formatted."""
        self.assertEqual(
            self.auth.get_auth_headers(),
            {"Authorization": f"Token {self.valid_token}"}
        )

    def test_get_auth_params(self):
        """Test that auth params are empty for token auth."""
        self.assertEqual(self.auth.get_auth_params(), {})

    def test_no_params(self):
        """Test that token is required."""
        with self.assertRaises(ValueError):
            TokenAuth()  # type: ignore

    def test_empty_token(self):
        """Test that empty token is rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="")

    def test_whitespace_token(self):
        """Test that whitespace-only token is rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="   ")

    def test_strip_token(self):
        """Test that whitespace is stripped from token."""
        auth = TokenAuth(token=f" {self.valid_token} ")
        self.assertEqual(auth.token, self.valid_token)

    def test_strip_token_middle_whitespace(self):
        """Test that tokens with internal whitespace are rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token=" 40charact  erslong40 characterslong40charac ")

    def test_short_token(self):
        """Test that tokens shorter than minimum length are rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="20characterslong20ch")

    def test_short_token_with_padding(self):
        """Test that padding doesn't help short tokens."""
        with self.assertRaises(ValueError):
            TokenAuth(token="          40characterslong40ch          ")

    def test_long_token(self):
        """Test that tokens longer than maximum length are rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="80characterslong80characterslong80characterslong80characterslong80characterslong")

    def test_invalid_characters(self):
        """Test that tokens with invalid characters are rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="40characterslong40characterslong40charac!")

    def test_token_with_special_chars(self):
        """Test that tokens with special characters are rejected."""
        with self.assertRaises(ValueError):
            TokenAuth(token="40characterslong40characterslong40charac$")

    def test_model_serialization(self):
        """Test that the model can be serialized to dict."""
        auth_dict = self.auth.model_dump()
        self.assertEqual(auth_dict, {"token": self.valid_token})

    def test_model_deserialization(self):
        """Test that the model can be deserialized from dict."""
        auth_dict = {"token": self.valid_token}
        auth = TokenAuth.model_validate(auth_dict)
        self.assertEqual(auth.token, self.valid_token)


class TestBasicAuth(unittest.TestCase):
    """Test the BasicAuth class."""

    def setUp(self):
        """Set up test fixtures."""
        self.username = "testuser"
        self.password = "testpass"
        self.auth = BasicAuth(username=self.username, password=self.password)

    def test_initialization(self):
        """Test basic initialization with valid credentials."""
        self.assertEqual(self.auth.username, self.username)
        self.assertEqual(self.auth.password, self.password)

    def test_get_auth_headers(self):
        """Test that auth headers are empty for basic auth."""
        self.assertEqual(self.auth.get_auth_headers(), {})

    def test_get_auth_params(self):
        """Test that auth params contain the correct credentials."""
        self.assertEqual(
            self.auth.get_auth_params(),
            {"auth": (self.username, self.password)}
        )

    def test_no_params(self):
        """Test that username and password are required."""
        with self.assertRaises(ValueError):
            BasicAuth()  # type: ignore

    def test_missing_username(self):
        """Test that username is required."""
        with self.assertRaises(ValueError):
            BasicAuth(password=self.password)  # type: ignore

    def test_missing_password(self):
        """Test that password is required."""
        with self.assertRaises(ValueError):
            BasicAuth(username=self.username)  # type: ignore

    def test_empty_username(self):
        """Test that empty username is accepted (though not recommended)."""
        auth = BasicAuth(username="", password=self.password)
        self.assertEqual(auth.username, "")

    def test_empty_password(self):
        """Test that empty password is accepted (though not recommended)."""
        auth = BasicAuth(username=self.username, password="")
        self.assertEqual(auth.password, "")

    def test_whitespace_username(self):
        """Test that whitespace is stripped from username."""
        auth = BasicAuth(username=f" {self.username} ", password=self.password)
        self.assertEqual(auth.username, self.username)

    def test_whitespace_password(self):
        """Test that whitespace is stripped from password."""
        auth = BasicAuth(username=self.username, password=f" {self.password} ")
        self.assertEqual(auth.password, self.password)

    def test_model_serialization(self):
        """Test that the model can be serialized to dict."""
        auth_dict = self.auth.model_dump()
        self.assertEqual(auth_dict, {"username": self.username, "password": self.password})

    def test_model_deserialization(self):
        """Test that the model can be deserialized from dict."""
        auth_dict = {"username": self.username, "password": self.password}
        auth = BasicAuth.model_validate(auth_dict)
        self.assertEqual(auth.username, self.username)
        self.assertEqual(auth.password, self.password)


if __name__ == "__main__":
    unittest.main()
