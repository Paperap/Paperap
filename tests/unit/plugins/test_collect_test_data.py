"""




----------------------------------------------------------------------------

   METADATA:

       File:    test_collect_test_data.py
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

from __future__ import annotations

import datetime
import json
import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Set, override
import unittest
from unittest.mock import MagicMock, Mock, patch, call

from paperap.client import PaperlessClient
from paperap.models import StandardModel
from paperap.plugins.collect_test_data import TestDataCollector, SANITIZE_KEYS
from paperap.signals import SignalRegistry
from paperap.tests import UnitTestCase


class TestDataCollectorUnitTest(UnitTestCase):
    """Base test case for TestDataCollector tests."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        # Create a temporary directory for test data
        self.test_dir = Path("tests/temp_test_data")
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Create the plugin instance
        self.plugin = TestDataCollector(self.client, test_dir=self.test_dir)

        # Reset the signal registry for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")

    @override
    def tearDown(self) -> None:
        """Clean up after the test."""
        super().tearDown()
        # Remove test files
        if self.test_dir.exists():
            for file in self.test_dir.glob("*.json"):
                file.unlink()
            self.test_dir.rmdir()


class TestPluginInitialization(TestDataCollectorUnitTest):
    """Test the initialization of the TestDataCollector plugin."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    def test_init_with_path_object(self):
        """Test initializing with a Path object."""
        plugin = TestDataCollector(self.client, test_dir=self.test_dir)
        self.assertEqual(plugin.test_dir, self.test_dir)

    def test_init_with_string_path(self):
        """Test initializing with a string path."""
        plugin = TestDataCollector(self.client, test_dir=str(self.test_dir))
        self.assertEqual(plugin.test_dir, self.test_dir)

    def test_init_without_path(self):
        """Test initializing without a path."""
        plugin = TestDataCollector(self.client)
        self.assertEqual(plugin.test_dir, Path("tests/sample_data"))

    def test_init_creates_directory(self):
        """Test that initialization creates the directory if it doesn't exist."""
        test_dir = Path("tests/nonexistent_dir")
        if test_dir.exists():
            test_dir.rmdir()

        plugin = TestDataCollector(self.client, test_dir=test_dir)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())

        # Clean up
        test_dir.rmdir()


class TestPluginSetupTeardown(TestDataCollectorUnitTest):
    """Test the setup and teardown methods of the TestDataCollector plugin."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.signals.registry.connect')
    def test_setup_connects_signals(self, mock_connect):
        """Test that setup connects the signal handlers."""
        self.plugin.setup()

        # Check that connect was called for each signal
        self.assertEqual(mock_connect.call_count, 3)
        mock_connect.assert_has_calls([
            call("resource._handle_response:after", self.plugin.save_list_response, unittest.mock.ANY),
            call("resource._handle_results:before", self.plugin.save_first_item, unittest.mock.ANY),
            call("client.request:after", self.plugin.save_parsed_response, unittest.mock.ANY)
        ], any_order=True)

    @patch('paperap.signals.registry.disconnect')
    def test_teardown_disconnects_signals(self, mock_disconnect):
        """Test that teardown disconnects the signal handlers."""
        self.plugin.teardown()

        # Check that disconnect was called for each signal
        self.assertEqual(mock_disconnect.call_count, 3)
        mock_disconnect.assert_has_calls([
            call("resource._handle_response:after", self.plugin.save_list_response),
            call("resource._handle_results:before", self.plugin.save_first_item),
            call("client.request:after", self.plugin.save_parsed_response)
        ], any_order=True)


class TestJsonSerializer(TestDataCollectorUnitTest):
    """Test the JSON serializer method."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    def test_serialize_datetime(self):
        """Test serializing a datetime object."""
        dt = datetime.datetime(2025, 3, 13, 12, 0, 0)
        result = self.plugin._json_serializer(dt)
        self.assertEqual(result, "2025-03-13T12:00:00")

    def test_serialize_path(self):
        """Test serializing a Path object."""
        path = Path("/test/path")
        result = self.plugin._json_serializer(path)
        self.assertEqual(result, "/test/path")

    def test_serialize_decimal(self):
        """Test serializing a Decimal object."""
        decimal = Decimal("123.45")
        result = self.plugin._json_serializer(decimal)
        self.assertEqual(result, 123.45)

    def test_serialize_standard_model(self):
        """Test serializing a StandardModel object."""
        model = Mock(spec=StandardModel)
        model.to_dict.return_value = {"id": 1, "name": "Test"}
        result = self.plugin._json_serializer(model)
        self.assertEqual(result, {"id": 1, "name": "Test"})

    def test_serialize_set(self):
        """Test serializing a set."""
        test_set = {1, 2, 3}
        result = self.plugin._json_serializer(test_set)
        self.assertEqual(set(result), {1, 2, 3})

    def test_serialize_bytes(self):
        """Test serializing bytes."""
        test_bytes = b"test bytes"
        result = self.plugin._json_serializer(test_bytes)
        self.assertEqual(result, "test bytes")

    def test_serialize_unsupported_type(self):
        """Test serializing an unsupported type raises TypeError."""
        class UnsupportedType:
            pass

        with self.assertRaises(TypeError):
            self.plugin._json_serializer(UnsupportedType())


class TestSanitization(TestDataCollectorUnitTest):
    """Test the sanitization methods."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.plugins.collect_test_data.TestDataCollector._sanitize_value_recursive')
    def test_sanitize_response(self, mock_sanitize_value):
        """Test sanitizing a response."""
        mock_sanitize_value.side_effect = lambda k, v: f"sanitized_{v}"

        response = {
            "key1": "value1",
            "key2": "value2",
            "next": "https://paperless.example.org/api/documents/?page=2"
        }

        result = self.plugin._sanitize_response(**response)

        # Check that _sanitize_value_recursive was called for each key-value pair
        self.assertEqual(mock_sanitize_value.call_count, 3)

        # Check that the "next" URL was sanitized
        self.assertEqual(result["next"], "https://example.com/api/documents/?page=2")

    def test_sanitize_value_recursive_dict(self):
        """Test sanitizing a dictionary recursively."""
        test_dict = {
            "name": "John Doe",
            "nested": {
                "email": "john@example.com"
            }
        }

        result = self.plugin._sanitize_value_recursive("root", test_dict)

        # Check that the dictionary was recursively sanitized
        self.assertIsInstance(result, dict)
        self.assertNotEqual(result["name"], "John Doe")
        self.assertIsInstance(result["nested"], dict)
        self.assertNotEqual(result["nested"]["email"], "john@example.com")

    def test_sanitize_value_recursive_sanitize_keys(self):
        """Test sanitizing values for keys in SANITIZE_KEYS."""
        for key in SANITIZE_KEYS:
            # Test with string value
            result = self.plugin._sanitize_value_recursive(key, "sensitive data")
            self.assertNotEqual(result, "sensitive data")

            # Test with list value
            result = self.plugin._sanitize_value_recursive(key, ["item1", "item2"])
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)
            self.assertNotEqual(result[0], "item1")
            self.assertNotEqual(result[1], "item2")

    def test_sanitize_value_recursive_non_sanitize_keys(self):
        """Test that values for keys not in SANITIZE_KEYS are not sanitized."""
        result = self.plugin._sanitize_value_recursive("not_sensitive", "regular data")
        self.assertEqual(result, "regular data")


class TestSaveResponse(TestDataCollectorUnitTest):
    """Test the save_response method."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.plugins.collect_test_data.TestDataCollector._sanitize_response')
    @patch('json.dump')
    def test_save_response_new_file(self, mock_json_dump, mock_sanitize):
        """Test saving a response to a new file."""
        mock_sanitize.return_value = {"sanitized": True}

        filepath = self.test_dir / "test_response.json"
        response = {"key": "value"}

        self.plugin.save_response(filepath, response)

        # Check that the response was sanitized
        mock_sanitize.assert_called_once_with(**response)

        # Check that json.dump was called with the sanitized response
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0], {"sanitized": True})

    def test_save_response_existing_file(self):
        """Test that save_response does nothing if the file already exists."""
        filepath = self.test_dir / "existing_file.json"

        # Create the file
        with filepath.open("w") as f:
            f.write("{}")

        with patch('json.dump') as mock_json_dump:
            self.plugin.save_response(filepath, {"key": "value"})

            # Check that json.dump was not called
            mock_json_dump.assert_not_called()

    @patch('paperap.plugins.collect_test_data.logger.error')
    def test_save_response_error(self, mock_logger_error):
        """Test that errors are logged but don't propagate."""
        filepath = self.test_dir / "error_file.json"

        # Create a response that will cause an error
        response = {"key": object()}  # object() is not JSON serializable

        self.plugin.save_response(filepath, response)

        # Check that an error was logged
        mock_logger_error.assert_called_once()
        self.assertIn("Error saving response to file", mock_logger_error.call_args[0][0])


class TestSaveListResponse(TestDataCollectorUnitTest):
    """Test the save_list_response method."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_list_response(self, mock_save_response):
        """Test saving a list response."""
        response = {"count": 2, "results": [{"id": 1}, {"id": 2}]}

        result = self.plugin.save_list_response(None, response, resource="documents")

        # Check that save_response was called with the correct arguments
        mock_save_response.assert_called_once()
        args = mock_save_response.call_args[0]
        self.assertEqual(args[0], self.test_dir / "documents_list.json")
        self.assertEqual(args[1], response)

        # Check that the response was returned unchanged
        self.assertEqual(result, response)

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_list_response_no_resource(self, mock_save_response):
        """Test that save_list_response does nothing if no resource is provided."""
        response = {"count": 2, "results": [{"id": 1}, {"id": 2}]}

        result = self.plugin.save_list_response(None, response)

        # Check that save_response was not called
        mock_save_response.assert_not_called()

        # Check that the response was returned unchanged
        self.assertEqual(result, response)

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_list_response_empty_response(self, mock_save_response):
        """Test that save_list_response does nothing if the response is empty."""
        result = self.plugin.save_list_response(None, None, resource="documents")

        # Check that save_response was not called
        mock_save_response.assert_not_called()

        # Check that the response was returned unchanged
        self.assertIsNone(result)


class TestSaveFirstItem(TestDataCollectorUnitTest):
    """Test the save_first_item method."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    @patch('paperap.signals.registry.disable')
    def test_save_first_item(self, mock_disable, mock_save_response):
        """Test saving the first item from a list."""
        item = {"id": 1, "name": "Test Item"}

        result = self.plugin.save_first_item(None, item, resource="documents")

        # Check that save_response was called with the correct arguments
        mock_save_response.assert_called_once()
        args = mock_save_response.call_args[0]
        self.assertEqual(args[0], self.test_dir / "documents_item.json")
        self.assertEqual(args[1], item)

        # Check that the signal handler was disabled
        mock_disable.assert_called_once_with(
            "resource._handle_results:before",
            self.plugin.save_first_item
        )

        # Check that the item was returned unchanged
        self.assertEqual(result, item)

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_first_item_no_resource(self, mock_save_response):
        """Test that save_first_item does nothing if no resource is provided."""
        item = {"id": 1, "name": "Test Item"}

        result = self.plugin.save_first_item(None, item)

        # Check that save_response was not called
        mock_save_response.assert_not_called()

        # Check that the item was returned unchanged
        self.assertEqual(result, item)


class TestSaveParsedResponse(TestDataCollectorUnitTest):
    """Test the save_parsed_response method."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_parsed_response(self, mock_save_response):
        """Test saving a parsed response."""
        parsed_response = {"id": 1, "name": "Test"}
        method = "GET"
        params = {"page": 1, "search": "test"}
        endpoint = "api/documents/"

        result = self.plugin.save_parsed_response(
            parsed_response,
            method=method,
            params=params,
            json_response=True,
            endpoint=endpoint
        )

        # Check that save_response was called with the correct arguments
        mock_save_response.assert_called_once()
        args = mock_save_response.call_args[0]
        self.assertEqual(args[0], self.test_dir / "documents___page|search.json")
        self.assertEqual(args[1], parsed_response)

        # Check that the response was returned unchanged
        self.assertEqual(result, parsed_response)

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_parsed_response_post_method(self, mock_save_response):
        """Test saving a parsed response with POST method."""
        parsed_response = {"id": 1, "name": "Test"}
        method = "POST"
        params = {"title": "New Document"}
        endpoint = "api/documents/"

        self.plugin.save_parsed_response(
            parsed_response,
            method=method,
            params=params,
            json_response=True,
            endpoint=endpoint
        )

        # Check that save_response was called with the correct filename
        args = mock_save_response.call_args[0]
        self.assertEqual(args[0], self.test_dir / "post__documents___title.json")

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_parsed_response_complex_endpoint(self, mock_save_response):
        """Test saving a parsed response with a complex endpoint."""
        parsed_response = {"id": 1, "name": "Test"}
        method = "GET"
        params = {"page": 1}
        endpoint = "https://example.com/api/documents/1/notes/"

        self.plugin.save_parsed_response(
            parsed_response,
            method=method,
            params=params,
            json_response=True,
            endpoint=endpoint
        )

        # Check that save_response was called with the correct filename
        args = mock_save_response.call_args[0]
        self.assertEqual(args[0], self.test_dir / "1_notes___page.json")

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_parsed_response_no_json(self, mock_save_response):
        """Test that save_parsed_response does nothing for non-JSON responses."""
        parsed_response = b"Binary data"

        result = self.plugin.save_parsed_response(
            parsed_response,
            method="GET",
            params={"page": 1},
            json_response=False,
            endpoint="api/documents/1/download/"
        )

        # Check that save_response was not called
        mock_save_response.assert_not_called()

        # Check that the response was returned unchanged
        self.assertEqual(result, parsed_response)

    @patch('paperap.plugins.collect_test_data.TestDataCollector.save_response')
    def test_save_parsed_response_no_params(self, mock_save_response):
        """Test that save_parsed_response does nothing if no params are provided."""
        parsed_response = {"id": 1, "name": "Test"}

        result = self.plugin.save_parsed_response(
            parsed_response,
            method="GET",
            params=None,
            json_response=True,
            endpoint="api/documents/"
        )

        # Check that save_response was not called
        mock_save_response.assert_not_called()

        # Check that the response was returned unchanged
        self.assertEqual(result, parsed_response)


class TestConfigSchema(unittest.TestCase):
    """Test the configuration schema."""
    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    def test_get_config_schema(self):
        """Test that get_config_schema returns the expected schema."""
        schema = TestDataCollector.get_config_schema()

        self.assertIsInstance(schema, dict)
        self.assertIn("test_dir", schema)
        self.assertEqual(schema["test_dir"]["type"], "string")
        self.assertEqual(schema["test_dir"]["required"], False)


if __name__ == "__main__":
    unittest.main()
