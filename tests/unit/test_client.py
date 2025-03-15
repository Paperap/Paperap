"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    test_client.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.7
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-13     By Jess Mann

"""
from __future__ import annotations
import json
import os
import requests
from typing import Any, Dict, Iterator, override
import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from pathlib import Path
from yarl import URL
from string import Template

from paperap.auth import AuthBase, BasicAuth, TokenAuth
from paperap.client import PaperlessClient
from paperap.exceptions import (
    APIError,
    AuthenticationError,
    BadResponseError,
    ConfigurationError,
    InsufficientPermissionError,
    RequestError,
    ResourceNotFoundError,
    ResponseParsingError
)
from paperap.resources.correspondents import CorrespondentResource
from paperap.resources.custom_fields import CustomFieldResource
from paperap.resources.documents import DocumentResource
from paperap.resources.document_types import DocumentTypeResource
from paperap.resources.storage_paths import StoragePathResource
from paperap.resources.tags import TagResource
from paperap.resources.tasks import TaskResource
from paperap.settings import Settings
from paperap.tests import UnitTestCase, load_sample_data
from paperap.models.abstract import BaseQuerySet
from paperap.models.document import Document
from paperap.models.tag import Tag

# Load sample response from tests/sample_data/documents_list.json
sample_data = load_sample_data('documents_list.json')

class TestClient(UnitTestCase):
    resource_class = DocumentResource

    @patch("paperap.client.PaperlessClient.request")
    def test_get_documents(self, mock_request):
        mock_request.return_value = sample_data
        documents = self.client.documents()
        self.assertIsInstance(documents, BaseQuerySet)
        total = documents.count()
        self.assertEqual(total, sample_data['count'], "Count of documents incorrect")
        total_on_page = documents.count_this_page()
        self.assertEqual(total_on_page, len(sample_data['results']), "Count of documents on this page incorrect")

        count = 0
        # Ensure paging works, then break
        test_iterations = total_on_page + 2

        # A warning should be issued for repeating the same url
        # this happens because when the 2nd page is requested, the next url is populated, even though we're going to break before using it.
        # Log was turned to a debug (maybe temporarily?)
        #with self.assertLogs(level='WARNING'):
        for document in documents:
            count += 1
            self.assertIsInstance(document, Document, f"Expected Document, got {type(document)}")
            self.assertIsInstance(document.id, int, f"Document id is wrong type: {type(document.id)}")
            self.assertIsInstance(document.title, str, f"Document title is wrong type: {type(document.title)}")
            if document.correspondent_id:
                self.assertIsInstance(document.correspondent_id, int, f"Document correspondent is wrong type: {type(document.correspondent_id)}")
            self.assertIsInstance(document.document_type_id, int, f"Document document_type is wrong type: {type(document.document_type_id)}")
            self.assertIsInstance(document.tag_ids, list, f"Document tags is wrong type: {type(document.tag_ids)}")

            for tag in document.tag_ids:
                self.assertIsInstance(tag, int, f"Document tag is wrong type: {type(tag)}")

            # Ensure paging works, then break
            if count >= test_iterations:
                break

        self.assertEqual(count, test_iterations, "Document queryset did not iterate over 3 pages.")


class TestClientInitialization(unittest.TestCase):
    """Test the initialization of the PaperlessClient class."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    def test_init_with_token(self):
        """Test initializing with a token."""
        client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))
        self.assertIsInstance(client.auth, TokenAuth)
        self.assertEqual(client.auth.token, "40characterslong40characterslong40charac")
        self.assertEqual(str(client.base_url), "https://example.com")

    def test_init_with_basic_auth(self):
        """Test initializing with username and password."""
        client = PaperlessClient(Settings(
            base_url="https://example.com",
            username="testuser",
            password="testpass"
        ))
        self.assertIsInstance(client.auth, BasicAuth)
        self.assertEqual(client.auth.username, "testuser") # type: ignore
        self.assertEqual(client.auth.password, "testpass") # type: ignore

    def test_init_missing_auth(self):
        """Test that initialization fails without auth credentials."""
        # Patch the env to be empty
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                PaperlessClient(Settings(base_url="https://example.com"))

    def test_init_resources(self):
        """Test that all resources are initialized."""
        client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))
        self.assertIsInstance(client.documents, DocumentResource)
        self.assertIsInstance(client.correspondents, CorrespondentResource)
        self.assertIsInstance(client.tags, TagResource)
        self.assertIsInstance(client.document_types, DocumentTypeResource)
        # Check a few more resources to ensure they're all initialized
        self.assertIsInstance(client.custom_fields, CustomFieldResource)
        self.assertIsInstance(client.storage_paths, StoragePathResource)
        self.assertIsInstance(client.tasks, TaskResource)

    def test_init_plugins(self):
        """Test that plugins are initialized."""
        client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))
        self.assertIsInstance(client.plugins, dict)
        # At least the default TestDataCollector plugin should be present
        self.assertIn("SampleDataCollector", client.plugins)

    def test_context_manager(self):
        """Test using the client as a context manager."""
        with patch('requests.Session.close') as mock_close:
            with PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac")) as client:
                self.assertIsInstance(client, PaperlessClient)
            mock_close.assert_called_once()


class TestClientRequests(UnitTestCase):
    """Test the request methods of the PaperlessClient class."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.
    @override
    def setUp(self):
        super().setUp()
        self.session_patcher = patch('requests.Session.request')
        self.mock_session_request = self.session_patcher.start()

        # Setup a mock response
        self.mock_response = Mock(spec=requests.Response)
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"key": "value"}
        self.mock_response.content = b'{"key": "value"}'
        self.mock_session_request.return_value = self.mock_response

    @override
    def tearDown(self):
        self.session_patcher.stop()

    def test_request_with_relative_endpoint(self):
        """Test making a request with a relative endpoint."""
        result = self.client.request("GET", "api/documents/")
        self.mock_session_request.assert_called_once()
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["method"], "GET")
        self.assertEqual(call_args["url"], "http://example.com/api/documents/")
        self.assertEqual(result, {"key": "value"})

    def test_request_with_absolute_url(self):
        """Test making a request with an absolute URL."""
        _result = self.client.request("GET", "https://other-example.com/api/documents/")
        self.mock_session_request.assert_called_once()
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "https://other-example.com/api/documents/")

    def test_request_with_data(self):
        """Test making a request with JSON data."""
        data = {"title": "Test Document"}
        self.client.request("POST", "api/documents/", data=data)
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["json"], data)

    def test_request_with_files(self):
        """Test making a request with files."""
        files = {"file": ("test.pdf", b"file content")}
        data = {"title": "Test Document"}
        self.client.request("POST", "api/documents/upload/", data=data, files=files)
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["files"], files)
        self.assertEqual(call_args["data"], data)
        self.assertIsNone(call_args["json"])  # json should be None when files are present

    def test_request_with_template(self):
        """Test making a request with a Template endpoint."""
        template = Template("api/documents/$id/")
        self.client.request("GET", template)
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "http://example.com/api/documents/$id/")

    def test_request_with_url_object(self):
        """Test making a request with a URL object."""
        url = URL("api/documents/")
        self.client.request("GET", url)
        call_args = self.mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "http://example.com/api/documents/")

    def test_request_no_content_response(self):
        """Test handling a 204 No Content response."""
        self.mock_response.status_code = 204
        result = self.client.request("DELETE", "api/documents/1/")
        self.assertIsNone(result)

    def test_request_non_json_response(self):
        """Test handling a non-JSON response."""
        self.mock_response.json.side_effect = ValueError("Invalid JSON")
        self.mock_response.content = b"Not JSON"
        self.mock_response.url = "https://example.com/api/documents/"
        with self.assertLogs(level="WARNING"):
            with self.assertRaises(ResponseParsingError):
                self.client.request("GET", "api/documents/")

    def test_request_binary_response(self):
        """Test requesting binary content."""
        self.mock_response.content = b"Binary content"
        result = self.client.request("GET", "api/documents/1/download/", json_response=False)
        self.assertEqual(result, b"Binary content")

    def test_request_connection_error(self):
        """Test handling a connection error."""
        self.mock_session_request.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertLogs(level='WARNING'):
            with self.assertRaises(RequestError):
                self.client.request("GET", "api/documents/")

    def test_request_timeout(self):
        """Test handling a request timeout."""
        self.mock_session_request.side_effect = requests.exceptions.Timeout("Request timed out")
        with self.assertRaises(RequestError):
            self.client.request("GET", "api/documents/")


class TestClientErrorHandling(unittest.TestCase):
    """Test the error handling of the PaperlessClient class."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    @override
    def setUp(self):
        self.client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))
        self.session_patcher = patch('requests.Session.request')
        self.mock_session_request = self.session_patcher.start()

        # Setup a mock error response
        self.mock_response = Mock(spec=requests.Response)
        self.mock_response.url = "https://example.com/api/documents/"
        self.mock_session_request.return_value = self.mock_response

    @override
    def tearDown(self):
        self.session_patcher.stop()

    def test_handle_400_error(self):
        """Test handling a 400 Bad Request error."""
        self.mock_response.status_code = 400
        self.mock_response.json.return_value = {"detail": "This field is required"}
        self.mock_response.text = "This field is required"

        with self.assertRaises(ValueError):
            self.client.request("POST", "api/documents/")

    def test_handle_401_error(self):
        """Test handling a 401 Unauthorized error."""
        self.mock_response.status_code = 401
        self.mock_response.json.return_value = {"detail": "Invalid token"}
        self.mock_response.text = "Invalid token"

        with self.assertRaises(AuthenticationError):
            self.client.request("GET", "api/documents/")

    def test_handle_403_error_csrf(self):
        """Test handling a 403 Forbidden error with CSRF message."""
        self.mock_response.status_code = 403
        self.mock_response.json.return_value = {"detail": "CSRF Failed: this site requires a CSRF token"}
        self.mock_response.text = "CSRF Failed: this site requires a CSRF token"

        with self.assertRaises(ConfigurationError):
            self.client.request("POST", "api/documents/")

    def test_handle_403_error_permission(self):
        """Test handling a 403 Forbidden error for permission issues."""
        self.mock_response.status_code = 403
        self.mock_response.json.return_value = {"detail": "You do not have permission to perform this action"}
        self.mock_response.text = "You do not have permission to perform this action"

        with self.assertRaises(InsufficientPermissionError):
            self.client.request("POST", "api/documents/")

    def test_handle_404_error(self):
        """Test handling a 404 Not Found error."""
        self.mock_response.status_code = 404
        self.mock_response.json.return_value = {"detail": "Not found"}
        self.mock_response.text = "Not found"

        with self.assertRaises(ResourceNotFoundError):
            self.client.request("GET", "api/documents/999/")

    def test_handle_500_error(self):
        """Test handling a 500 Internal Server Error."""
        self.mock_response.status_code = 500
        self.mock_response.json.return_value = {"detail": "Internal server error"}
        self.mock_response.text = "Internal server error"

        with self.assertRaises(BadResponseError):
            self.client.request("GET", "api/documents/")

    def test_extract_error_message_detail(self):
        """Test extracting error message with 'detail' field."""
        self.mock_response.json.return_value = {"detail": "Error message"}
        message = self.client._extract_error_message(self.mock_response) # type: ignore
        self.assertEqual(message, "Error message")

    def test_extract_error_message_error(self):
        """Test extracting error message with 'error' field."""
        self.mock_response.json.return_value = {"error": "Error message"}
        message = self.client._extract_error_message(self.mock_response) # type: ignore
        self.assertEqual(message, "Error message")

    def test_extract_error_message_non_field_errors(self):
        """Test extracting error message with 'non_field_errors' field."""
        self.mock_response.json.return_value = {"non_field_errors": ["Error 1", "Error 2"]}
        message = self.client._extract_error_message(self.mock_response) # type: ignore
        self.assertEqual(message, "Error 1, Error 2")

    def test_extract_error_message_nested(self):
        """Test extracting error message with nested fields."""
        self.mock_response.json.return_value = {
            "title": ["This field is required"],
            "tags": ["Invalid tag ID"]
        }
        message = self.client._extract_error_message(self.mock_response) # type: ignore
        self.assertIn("title: This field is required", message)
        self.assertIn("tags: Invalid tag ID", message)

    def test_extract_error_message_invalid_json(self):
        """Test extracting error message with invalid JSON response."""
        self.mock_response.json.side_effect = ValueError("Invalid JSON")
        self.mock_response.text = "Not JSON"
        self.mock_response.status_code = 400
        message = self.client._extract_error_message(self.mock_response) # type: ignore
        self.assertEqual(message, "Not JSON")


class TestClientUtilityMethods(unittest.TestCase):
    """Test the utility methods of the PaperlessClient class."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.
    @override
    def setUp(self):
        self.client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))

    @patch("paperap.client.PaperlessClient.request")
    def test_get_statistics(self, mock_request):
        """Test getting system statistics."""
        mock_request.return_value = {"document_count": 100, "inbox_count": 5}
        stats = self.client.get_statistics()
        mock_request.assert_called_once_with("GET", "api/statistics/")
        self.assertEqual(stats["document_count"], 100)
        self.assertEqual(stats["inbox_count"], 5)

    @patch("paperap.client.PaperlessClient.request")
    def test_get_statistics_error(self, mock_request):
        """Test error handling when getting statistics."""
        mock_request.return_value = None
        with self.assertRaises(APIError):
            self.client.get_statistics()

    @patch("paperap.client.PaperlessClient.request")
    def test_get_system_status(self, mock_request):
        """Test getting system status."""
        mock_request.return_value = {"status": "OK", "tasks_pending": 0}
        status = self.client.get_system_status()
        mock_request.assert_called_once_with("GET", "api/status/")
        self.assertEqual(status["status"], "OK")

    @patch("paperap.client.PaperlessClient.request")
    def test_get_system_status_error(self, mock_request):
        """Test error handling when getting system status."""
        mock_request.return_value = None
        with self.assertRaises(APIError):
            self.client.get_system_status()

    @patch("paperap.client.PaperlessClient.request")
    def test_get_config(self, mock_request):
        """Test getting system configuration."""
        mock_request.return_value = {"app_title": "Paperless-ngx", "app_logo": ""}
        config = self.client.get_config()
        mock_request.assert_called_once_with("GET", "api/config/")
        self.assertEqual(config["app_title"], "Paperless-ngx")

    @patch("paperap.client.PaperlessClient.request")
    def test_get_config_error(self, mock_request):
        """Test error handling when getting configuration."""
        mock_request.return_value = None
        with self.assertRaises(APIError):
            self.client.get_config()


class TestTokenGeneration(unittest.TestCase):
    """Test the token generation functionality."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.
    @override
    def setUp(self):
        self.client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))

    @patch("requests.post")
    def test_generate_token_success(self, mock_post):
        """Test successful token generation."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "40characterslong40characterslong40charac"}
        mock_post.return_value = mock_response

        token = self.client.generate_token(
            base_url="https://example.com",
            username="testuser",
            password="testpass"
        )

        mock_post.assert_called_once()
        # mock_post.call_args:
        # call('https://example.com/api/token/', json={'username': 'testuser', 'password': 'testpass'}, headers={'Accept': 'application/json'}, timeout=60)
        # mock_post.call_args[0]:
        # ('https://example.com/api/token/',)
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://example.com/api/token/", f"URL Not in {call_args}")
        self.assertEqual(call_args[1]["json"], {"username": "testuser", "password": "testpass"})
        self.assertEqual(token, "40characterslong40characterslong40charac")

    @patch("requests.post")
    def test_generate_token_with_http_prefix(self, mock_post):
        """Test token generation with http:// prefix in base_url."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "40characterslong40characterslong40charac"}
        mock_post.return_value = mock_response

        token = self.client.generate_token(
            base_url="http://example.com",
            username="testuser",
            password="testpass"
        )

        # mock_post.call_args:
        # call('http://example.com/api/token/', json={'username': 'testuser', 'password': 'testpass'}, headers={'Accept': 'application/json'}, timeout=60)
        # mock_post.call_args[0]:
        # ('https://example.com/api/token/',)
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://example.com/api/token/", f"URL Not in {call_args}")
        self.assertEqual(token, "40characterslong40characterslong40charac")

    @patch("requests.post")
    def test_generate_token_with_trailing_slash(self, mock_post):
        """Test token generation with trailing slash in base_url."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "40characterslong40characterslong40charac"}
        mock_post.return_value = mock_response

        token = self.client.generate_token(
            base_url="https://example.com/",
            username="testuser",
            password="testpass"
        )

        # mock_post.call_args:
        # call('https://example.com/api/token/', json={'username': 'testuser', 'password': 'testpass'}, headers={'Accept': 'application/json'}, timeout=60)
        # mock_post.call_args[0]:
        # ('https://example.com/api/token/',)
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://example.com/api/token/", f"URL Not in {call_args}")
        self.assertEqual(token, "40characterslong40characterslong40charac")

    @patch("requests.post")
    def test_generate_token_auth_error(self, mock_post):
        """Test token generation with authentication error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid credentials"}
        mock_post.return_value = mock_response

        # Create a HTTPError with the mock response
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_post.side_effect = http_error

        with self.assertRaises(AuthenticationError):
            self.client.generate_token(
                base_url="https://example.com",
                username="testuser",
                password="wrongpass"
            )

    @patch("requests.post")
    def test_generate_token_connection_error(self, mock_post):
        """Test token generation with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with self.assertRaises(RequestError):
            self.client.generate_token(
                base_url="https://example.com",
                username="testuser",
                password="testpass"
            )

    @patch("requests.post")
    def test_generate_token_invalid_response(self, mock_post):
        """Test token generation with invalid response (no token field)."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Success but no token"}
        mock_post.return_value = mock_response

        with self.assertRaises(ResponseParsingError):
            self.client.generate_token(
                base_url="https://example.com",
                username="testuser",
                password="testpass"
            )

    @patch("requests.post")
    def test_generate_token_json_error(self, mock_post):
        """Test token generation with JSON parsing error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        with self.assertRaises(ResponseParsingError):
            self.client.generate_token(
                base_url="https://example.com",
                username="testuser",
                password="testpass"
            )

if __name__ == "__main__":
    unittest.main()
