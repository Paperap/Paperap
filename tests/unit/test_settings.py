"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_settings.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations
import os
from typing import Any, Iterable
import unittest
from unittest.mock import patch
from yarl import URL
from paperap.settings import Settings
from paperap.exceptions import ConfigurationError
from paperap.tests import TestCase

TOKEN_DATA = {
    'token': 'abc123',
    'base_url': 'https://example.com',
    'require_ssl': False,
    'timeout': 60,
    'username': None,
    'password': None,
}

AUTH_DATA = {
    **TOKEN_DATA,
    'token': None,
    'username': "user",
    'password': "password",
}

# By default, patch os.environ to prevent environment variables from affecting tests
class NoEnvTestCase(TestCase):
    def setUp(self):
        self.patcher = patch.dict(os.environ, {}, clear=True)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

class TestSettings(NoEnvTestCase):
    """Unit tests for the Settings class."""

    def test_valid_settings(self):
        """Test that Settings initializes correctly with valid data."""
        settings = Settings(**TOKEN_DATA)
        self.assertEqual(settings.token, TOKEN_DATA['token'])
        self.assertEqual(settings.username, TOKEN_DATA['username'])
        self.assertEqual(settings.password, TOKEN_DATA['password'])
        self.assertEqual(settings.base_url, URL(TOKEN_DATA['base_url']))
        self.assertEqual(settings.require_ssl, TOKEN_DATA['require_ssl'])
        self.assertEqual(settings.timeout, TOKEN_DATA['timeout'])
        self.assertFalse(settings.require_ssl)

class TestSettingsTimeout(NoEnvTestCase):
    def test_default_timeout(self):
        """Test that the default timeout is set to 60 if not provided."""
        params = TOKEN_DATA.copy()
        del params['timeout']
        settings = Settings(**params)
        self.assertEqual(settings.timeout, 60, "Timeout was not set to default value")

    def test_positive_timeouts(self):
        """Test that the timeout is correctly set."""
        test_cases = [0, 1, 10, 100, 1000, 10000]
        for timeout in test_cases:
            params = {**TOKEN_DATA, 'timeout': timeout}
            settings = Settings(**params)
            self.assertEqual(settings.timeout, timeout)

    def test_negative_timeouts(self):
        """Test that a negative timeout raises a validation error."""
        with self.assertRaises(ConfigurationError):
            params = {**TOKEN_DATA, 'timeout': -1}
            Settings(**params)

    def test_invalid_types(self):
        """Test that invalid types for the timeout raise a validation error."""
        test_cases = ["abc", object(), [], {}]
        for timeout in test_cases:
            with self.assertRaises(TypeError, msg=f"Timeout should be invalid: {timeout}"):
                params = {**TOKEN_DATA, 'timeout': timeout}
                Settings(**params)

class TestSettingsURL(NoEnvTestCase):
    def test_accept_url(self):
        """Test that a URL object is accepted."""
        test_cases = [
            URL("http://example.com"),
            URL("https://example.com"),
        ]
        for url in test_cases:
            params = {**TOKEN_DATA, 'base_url': url}
            settings = Settings(**params)
            self.assertEqual(settings.base_url, url, f"URL does not match: {settings.base_url} != {url}")

    def test_valid_url_conversion(self):
        """Test that a valid URL string is correctly converted to a URL object."""
        test_cases = [
            'http://example.com',
            'https://example.com',
            'http://example.com:8080',
            'https://example.com:8080',
        ]
        for url in test_cases:
            params = {**TOKEN_DATA, 'base_url': url}
            settings = Settings(**params)
            self.assertIsInstance(settings.base_url, URL, f"URL is not a yarl.URL object: {settings.base_url}")
            self.assertEqual(settings.base_url, URL(url), f"URL does not match: {settings.base_url} != {URL(url)}")

    def test_invalid_urls(self):
        """Test that an invalid URL string raises a validation error."""
        # Only check missing schema. Other URL validation is not checked due to local paperless ngx instances.
        test_cases = [
            'random-string',
            'http://',
            'https://',
        ]
        for value in test_cases:
            with self.assertRaises(ConfigurationError, msg=f"URL should be invalid: {value}"):
                params = {**TOKEN_DATA, 'base_url': value}
                Settings(**params)
            with self.assertRaises(ConfigurationError, msg=f"URL object should be invalid: {value}"):
                params = {**TOKEN_DATA, 'base_url': URL(value)}
                Settings(**params)

    def test_url_final_slash_removed(self):
        """Test that a URL with a final slash is correctly removed."""
        test_cases = {
            'http://example.com/': 'http://example.com',
            'https://example.com/': 'https://example.com',
            'http://example.com:8080/': 'http://example.com:8080',
            'https://example.com:8080/': 'https://example.com:8080',
            'http://example.com/path/': 'http://example.com/path',
            'https://example.com/path/': 'https://example.com/path',
            'http://example.com:8080/path/': 'http://example.com:8080/path',
            'https://example.com:8080/path/': 'https://example.com:8080/path',
        }
        for url, expected in test_cases.items():
            params = {**TOKEN_DATA, 'base_url': url}
            settings = Settings(**params)
            self.assertEqual(str(settings.base_url), expected, f"URL final slash not removed. {settings.base_url} != {URL(expected)}")

class TestSettingsToken(NoEnvTestCase):
    def test_null_token(self):
        """Test that a None token is allowed when user/pass is provided."""
        settings = Settings(**AUTH_DATA)
        self.assertIsNone(settings.token, "Token should be None")

class TestSettingsUsernamePassword(NoEnvTestCase):
    def test_null_username_password(self):
        """Test that None values for username and password are allowed."""
        settings = Settings(**TOKEN_DATA)
        self.assertIsNone(settings.username, "Username was initialized incorrectly during Settings init for token auth")
        self.assertIsNone(settings.password, "Password was initialized incorrectly during Settings init for token auth")

class TestSettingsSSL(NoEnvTestCase):
    def test_require_ssl_set(self):
        """Test that require_ssl is set correctly."""
        params = {**TOKEN_DATA, 'require_ssl': True}
        settings = Settings(**params)
        self.assertTrue(settings.require_ssl, "require_ssl was not set during Settings init")

    def test_require_ssl_enforced(self):
        """Test that require_ssl is enforced."""
        params = {**TOKEN_DATA, 'require_ssl': True, 'base_url': 'http://example.com'}
        with self.assertRaises(ConfigurationError, msg="http URL should be invalid when require_ssl is True"):
            Settings(**params)

    def test_require_ssl_success(self):
        """Test that require_ssl is not enforced when disabled."""
        params = {**TOKEN_DATA, 'require_ssl': True, 'base_url': 'https://example.com'}
        settings = Settings(**params)
        self.assertEqual(settings.base_url, URL('https://example.com'), "URL was changed require_ssl is True")

class TestSettingsEnvPrefix(TestCase):
    def test_env_prefix_token_defaults(self):
        """Test that the environment prefix is applied correctly."""
        env_data = {f'PAPERLESS_{key.upper()}': str(value) for key, value in TOKEN_DATA.items() if value is not None}
        with patch.dict(os.environ, env_data, clear=True):
            settings = Settings() # type: ignore # base_url is required, but loaded from env. pyright doesn't like that.
        self.assertEqual(settings.token, TOKEN_DATA['token'], f"Token was changed when token env vars were set: {settings.token} != {TOKEN_DATA['token']}")
        self.assertEqual(settings.username, TOKEN_DATA['username'], f"Username was changed when token env vars were set: {settings.username} != {TOKEN_DATA['username']}")
        self.assertEqual(settings.password, TOKEN_DATA['password'], f"Password was changed when token env vars were set: {settings.password} != {TOKEN_DATA['password']}")
        self.assertEqual(settings.base_url, URL(TOKEN_DATA['base_url']), f"URL was changed when token env vars were set: {settings.base_url} != {URL(TOKEN_DATA['base_url'])}")
        self.assertEqual(settings.require_ssl, TOKEN_DATA['require_ssl'], f"require_ssl was changed when token env vars were set: {settings.require_ssl} != {TOKEN_DATA['require_ssl']}")
        self.assertEqual(settings.timeout, TOKEN_DATA['timeout'], f"Timeout was changed when token env vars were set: {settings.timeout} != {TOKEN_DATA['timeout']}")
        self.assertFalse(settings.require_ssl, "require_ssl was changed when token env vars were set")

    def test_env_prefix_auth_defaults(self):
        """Test that the environment prefix is applied correctly."""
        env_data = {f'PAPERLESS_{key.upper()}': str(value) for key, value in AUTH_DATA.items() if value is not None}
        with patch.dict(os.environ, env_data, clear=True):
            settings = Settings() # type: ignore # base_url is required, but loaded from env. pyright doesn't like that.
        self.assertEqual(settings.token, AUTH_DATA['token'], f"Token was changed when auth env vars were set: {settings.token} != {AUTH_DATA['token']}")
        self.assertEqual(settings.username, AUTH_DATA['username'], f"Username was changed when auth env vars were set: {settings.username} != {AUTH_DATA['username']}")
        self.assertEqual(settings.password, AUTH_DATA['password'], f"Password was changed when auth env vars were set: {settings.password} != {AUTH_DATA['password']}")
        self.assertEqual(settings.base_url, URL(AUTH_DATA['base_url']), f"URL was changed when auth env vars were set: {settings.base_url} != {URL(AUTH_DATA['base_url'])}")
        self.assertEqual(settings.require_ssl, AUTH_DATA['require_ssl'], f"require_ssl was changed when auth env vars were set: {settings.require_ssl} != {AUTH_DATA['require_ssl']}")
        self.assertEqual(settings.timeout, AUTH_DATA['timeout'], f"Timeout was changed when auth env vars were set: {settings.timeout} != {AUTH_DATA['timeout']}")
        self.assertFalse(settings.require_ssl, "require_ssl was changed when auth env vars were set")

    def test_env_prefix_token_override(self):
        env_data = {f'PAPERLESS_{key.upper()}': 'random-env-value' for key, _ in TOKEN_DATA.items()}
        with patch.dict(os.environ, env_data, clear=True):
            settings = Settings(**TOKEN_DATA)
        self.assertEqual(settings.token, TOKEN_DATA['token'], f"Token was not set during init when random env vars were set: {settings.token} != {TOKEN_DATA['token']}")
        self.assertEqual(settings.username, TOKEN_DATA['username'], f"Username was not set during init when random env vars were set: {settings.username} != {TOKEN_DATA['username']}")
        self.assertEqual(settings.password, TOKEN_DATA['password'], f"Password was not set during init when random env vars were set: {settings.password} != {TOKEN_DATA['password']}")
        self.assertEqual(settings.base_url, URL(TOKEN_DATA['base_url']), f"URL was not set during init when random env vars were set: {settings.base_url} != {URL(TOKEN_DATA['base_url'])}")
        self.assertEqual(settings.require_ssl, TOKEN_DATA['require_ssl'], f"require_ssl was not set during init when random env vars were set: {settings.require_ssl} != {TOKEN_DATA['require_ssl']}")
        self.assertEqual(settings.timeout, TOKEN_DATA['timeout'], f"Timeout was not set during init when random env vars were set: {settings.timeout} != {TOKEN_DATA['timeout']}")
        self.assertFalse(settings.require_ssl, "require_ssl was not set during init when random env vars were set")

if __name__ == "__main__":
    unittest.main()
