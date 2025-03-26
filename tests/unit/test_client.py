

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from string import Template
from typing import Any, Dict, Iterator, override
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import requests
from pydantic import HttpUrl

from paperap.auth import AuthBase, BasicAuth, TokenAuth
from paperap.client import PaperlessClient
from paperap.exceptions import (
    APIError,
    AuthenticationError,
    BadResponseError,
    ConfigurationError,
    InsufficientPermissionError,
    RelationshipNotFoundError,
    RequestError,
    ResourceNotFoundError,
    ResponseParsingError,
)
from paperap.models.abstract import BaseQuerySet
from paperap.models.document import Document
from paperap.models.tag import Tag
from paperap.resources.correspondents import CorrespondentResource
from paperap.resources.custom_fields import CustomFieldResource
from paperap.resources.document_types import DocumentTypeResource
from paperap.resources.documents import DocumentResource
from paperap.resources.storage_paths import StoragePathResource
from paperap.resources.tags import TagResource
from paperap.resources.tasks import TaskResource
from paperap.settings import Settings
from tests.lib import UnitTestCase, load_sample_data

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
            if document.document_type_id is not None:
                self.assertIsInstance(document.document_type_id, int, f"Document document_type is wrong type: {type(document.document_type_id)}")
            self.assertIsInstance(document.tag_ids, list, f"Document tags is wrong type: {type(document.tag_ids)}")

            for tag in document.tag_ids:
                self.assertIsInstance(tag, int, f"Document tag is wrong type: {type(tag)}")

            # Ensure paging works, then break
            if count >= test_iterations:
                break

        #self.assertEqual(count, test_iterations, "Document queryset did not iterate over 3 pages.")


class TestClientInitialization(unittest.TestCase):

    """Test the initialization of the PaperlessClient class."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    def test_init_with_token(self):
        """Test initializing with a token."""
        client = PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac"))
        self.assertIsInstance(client.auth, TokenAuth)
        self.assertEqual(client.auth.token, "40characterslong40characterslong40charac")
        self.assertEqual(str(client.base_url), "https://example.com/")

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
        #self.assertIn("SampleDataCollector", client.plugins)

    def test_context_manager(self):
        """Test using the client as a context manager."""
        with patch('requests.Session.close') as mock_close:
            with PaperlessClient(Settings(base_url="https://example.com", token="40characterslong40characterslong40charac")) as client:
                self.assertIsInstance(client, PaperlessClient)
            mock_close.assert_called_once()

class DisableTestClientRequests(UnitTestCase):
    """Test the request methods of the PaperlessClient class."""
    # Temporarily Disabled due to other tests apparently not cleaning up? TODO

    @patch('requests.Session.request')
    def __test_request_with_relative_endpoint(self, mock_session_request):
        """Test making a request with a relative endpoint."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.content = b'{"key": "value"}'

        mock_session_request.return_value = mock_response
        result = self.client.request("GET", "api/documents/")
        mock_session_request.assert_called_once()
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["method"], "GET")
        self.assertEqual(call_args["url"], "http://example.com/api/documents/")
        self.assertEqual(result, {"key": "value"})

    @patch('requests.Session.request')
    def __test_request_binary_response(self, mock_session_request):
        """Test requesting binary content."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.content = b"Binary content"

        mock_session_request.return_value = mock_response
        result = self.client.request("GET", "api/documents/1/download/", json_response=False)
        self.assertEqual(result, b"Binary content")

class TestClientRequests(UnitTestCase):
    """Test the request methods of the PaperlessClient class."""

    @patch('requests.Session.request')
    def test_request_with_absolute_url(self, mock_session_request):
        """Test making a request with an absolute URL."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.content = b'{"key": "value"}'

        mock_session_request.return_value = mock_response
        _result = self.client.request("GET", "https://other-example.com/api/documents/")
        mock_session_request.assert_called_once()
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "https://other-example.com/api/documents/")

    @patch('requests.Session.request')
    def test_request_with_data(self, mock_session_request):
        """Test making a request with JSON data."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        data = {"title": "Test Document"}
        self.client.request("POST", "api/documents/", data=data)
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["json"], data)

    @patch('requests.Session.request')
    def test_request_with_files(self, mock_session_request):
        """Test making a request with files."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        files = {"file": ("test.pdf", b"file content")}
        data = {"title": "Test Document"}
        self.client.request("POST", "api/documents/upload/", data=data, files=files)
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["files"], files)
        self.assertEqual(call_args["data"], data)
        # Check that data is used instead of json when files are present
        self.assertNotIn("json", call_args)

    @patch('requests.Session.request')
    def test_request_with_url_object(self, mock_session_request):
        """Test making a request with a pydantic HttpUrl object."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        url = HttpUrl("http://example.com/api/documents/")
        self.client.request("GET", url)
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "http://example.com/api/documents/")

    @patch('requests.Session.request')
    def test_request_no_content_response(self, mock_session_request):
        """Test handling a 204 No Content response."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 204
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        result = self.client.request("DELETE", "api/documents/1/")
        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_http_methods(self, mock_session_request):
        """Test all HTTP methods are properly passed to the session."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        for method in methods:
            self.client.request(method, "api/documents/")
            call_args = mock_session_request.call_args[1]
            self.assertEqual(call_args["method"], method)

    @patch('requests.Session.request')
    def test_request_with_unusual_url_formats(self, mock_session_request):
        """Test handling of unusual URL formats."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_session_request.return_value = mock_response
        # With double slashes
        self.client.request("GET", "//api/documents/")
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "http://example.com/api/documents/")

        # With query parameters in the endpoint
        self.client.request("GET", "api/documents/?query=test")
        call_args = mock_session_request.call_args[1]
        self.assertEqual(call_args["url"], "http://example.com/api/documents/?query=test")

    @patch('requests.Session.request')
    def test_request_non_json_response(self, mock_session_request):
        """Test handling a non-JSON response."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.content = b"Not JSON"
        mock_response.url = "https://example.com/api/documents/"

        mock_session_request.return_value = mock_response
        with self.assertLogs(level="WARNING"):
            with self.assertRaises(ResponseParsingError):
                self.client.request("GET", "api/documents/")

    @patch('requests.Session.request')
    def test_request_connection_error(self, mock_session_request):
        """Test handling a connection error."""
        mock_session_request.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertLogs(level='WARNING'):
            with self.assertRaises(RequestError):
                self.client.request("GET", "api/documents/")

    @patch('requests.Session.request')
    def test_request_timeout(self, mock_session_request):
        """Test handling a request timeout."""
        mock_session_request.side_effect = requests.exceptions.Timeout("Request timed out")
        with self.assertRaises(RequestError):
            self.client.request("GET", "api/documents/")

    @patch('requests.Session.request')
    def test_request_other_exceptions(self, mock_session_request):
        """Test handling of other request exceptions."""
        exceptions = [
            requests.exceptions.TooManyRedirects("Too many redirects"),
            requests.exceptions.RequestException("Generic request exception"),
            requests.exceptions.HTTPError("HTTP error")
        ]

        for exception in exceptions:
            mock_session_request.side_effect = exception
            with self.assertRaises(RequestError):
                self.client.request("GET", "api/documents/")


class TestClientErrorHandling(UnitTestCase):
    """Test the error handling of the PaperlessClient class."""

    @patch('requests.Session.request')
    def test_handle_400_error(self, mock_session_request):
        """Test handling a 400 Bad Request error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "This field is required"}
        mock_response.text = "This field is required"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.request("POST", "api/documents/")

    @patch('requests.Session.request')
    def test_handle_401_error(self, mock_session_request):
        """Test handling a 401 Unauthorized error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_response.text = "Invalid token"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            self.client.request("GET", "api/documents/")

    @patch('requests.Session.request')
    def test_handle_403_error_csrf(self, mock_session_request):
        """Test handling a 403 Forbidden error with CSRF message."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "CSRF Failed: this site requires a CSRF token"}
        mock_response.text = "CSRF Failed: this site requires a CSRF token"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(ConfigurationError):
            self.client.request("POST", "api/documents/")

    @patch('requests.Session.request')
    def test_handle_403_error_permission(self, mock_session_request):
        """Test handling a 403 Forbidden error for permission issues."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "You do not have permission to perform this action"}
        mock_response.text = "You do not have permission to perform this action"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(InsufficientPermissionError):
            self.client.request("POST", "api/documents/")

    @patch('requests.Session.request')
    def test_handle_404_error(self, mock_session_request):
        """Test handling a 404 Not Found error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.text = "Not found"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(ResourceNotFoundError):
            self.client.request("GET", "api/documents/999/")

    @patch('requests.Session.request')
    def test_handle_500_error(self, mock_session_request):
        """Test handling a 500 Internal Server Error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_response.text = "Internal server error"
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(BadResponseError):
            self.client.request("GET", "api/documents/")

    def test_extract_error_message_detail(self):
        """Test extracting error message with 'detail' field."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {"detail": "Error message"}
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertEqual(message, "Error message")

    def test_extract_error_message_error(self):
        """Test extracting error message with 'error' field."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {"error": "Error message"}
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertEqual(message, "Error message")

    def test_extract_error_message_non_field_errors(self):
        """Test extracting error message with 'non_field_errors' field."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {"non_field_errors": ["Error 1", "Error 2"]}
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertEqual(message, "Error 1, Error 2")

    def test_extract_error_message_nested(self):
        """Test extracting error message with nested fields."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {
            "title": ["This field is required"],
            "tags": ["Invalid tag ID"]
        }
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertIn("title: This field is required", message)
        self.assertIn("tags: Invalid tag ID", message)

    def test_extract_error_message_invalid_json(self):
        """Test extracting error message with invalid JSON response."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Not JSON"
        mock_response.status_code = 400
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertEqual(message, "Not JSON")

    def test_extract_error_message_complex_nested(self):
        """Test extracting error message with complex nested structure."""
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {
            "errors": {
                "document": {
                    "title": ["Too short", "Contains invalid characters"],
                    "content": ["Empty content not allowed"]
                }
            }
        }
        message = self.client._extract_error_message(mock_response) # type: ignore
        self.assertEqual(message, "errors: {'document': {'title': ['Too short', 'Contains invalid characters'], 'content': ['Empty content not allowed']}}")

    @patch('requests.Session.request')
    def test_handle_400_error_with_relationship(self, mock_session_request):
        """Test handling a 400 error with relationship error."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "correspondent: Invalid pk \"999\" - object does not exist."}
        mock_response.text = "correspondent: Invalid pk \"999\" - object does not exist."
        mock_response.url = "https://example.com/api/documents/"
        mock_session_request.return_value = mock_response

        with self.assertRaises(RelationshipNotFoundError):
            self.client.request("POST", "api/documents/")


class TestClientUtilityMethods(UnitTestCase):
    """Test the utility methods of the PaperlessClient class."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.
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


class TestTokenGeneration(UnitTestCase):
    """Test the token generation functionality."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.
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

class TestSignalIntegration(UnitTestCase):
    """Test the integration with the signal system."""

    @override
    def tearDown(self) -> None:
        """Clean up any resources used by the tests."""
        # Make sure any global state is reset
        # Add specific cleanup if needed
        super().tearDown()

    def test_generate_token_emits_signals(self):
        """Test that generate_token emits the appropriate signals."""
        with patch("paperap.client.registry.emit") as mock_emit:
            with patch("requests.post") as mock_post:
                mock_response = Mock(spec=requests.Response)
                mock_response.status_code = 200
                mock_response.json.return_value = {"token": "40characterslong40characterslong40charac"}
                mock_post.return_value = mock_response

                self.client.generate_token(
                    base_url="https://example.com",
                    username="testuser",
                    password="testpass"
                )

                # Check that signals were emitted
                self.assertEqual(mock_emit.call_count, 2)

                # First call should be client.generate_token__before
                self.assertEqual(mock_emit.call_args_list[0][0][0], "client.generate_token__before")

                # Second call should be client.generate_token__after
                self.assertEqual(mock_emit.call_args_list[1][0][0], "client.generate_token__after")


class TestPluginSystem(UnitTestCase):
    """Test the plugin system integration."""

    def test_plugin_initialization(self):
        """Test that plugins are properly initialized during client creation."""
        with patch("paperap.plugins.manager.PluginManager.discover_plugins") as mock_discover:
            with patch("paperap.plugins.manager.PluginManager.configure") as mock_configure:
                with patch("paperap.plugins.manager.PluginManager.initialize_all_plugins") as mock_initialize:
                    mock_initialize.return_value = {"TestPlugin": MagicMock()}

                    client = PaperlessClient(Settings(
                        base_url="https://example.com",
                        token="40characterslong40characterslong40charac"
                    ))

                    try:
                        # Verify plugins are accessible
                        self.assertIsInstance(client.plugins, dict)
                    finally:
                        # Ensure client is closed properly
                        client.close()

    def test_custom_plugin_config(self):
        """Test initializing with custom plugin configuration."""
        custom_config = {
            "enabled_plugins": ["CustomPlugin"],
            "settings": {
                "CustomPlugin": {
                    "option1": "value1",
                    "option2": "value2"
                }
            }
        }

        with patch("paperap.plugins.manager.PluginManager.configure") as mock_configure:
            with patch("paperap.plugins.manager.PluginManager.initialize_all_plugins") as mock_initialize:
                mock_initialize.return_value = {"CustomPlugin": MagicMock()}

                client = PaperlessClient(Settings(
                    base_url="https://example.com",
                    token="40characterslong40characterslong40charac"
                ))

                try:
                    # Initialize with custom config
                    client._initialize_plugins(custom_config)

                    # Verify custom config was used
                    mock_configure.assert_called_with(custom_config)
                finally:
                    # Ensure client is closed properly
                    client.close()


if __name__ == "__main__":
    unittest.main()
