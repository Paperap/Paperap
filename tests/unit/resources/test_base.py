


from __future__ import annotations

import unittest
from string import Template
from typing import Any, Dict, Iterator, List, Optional, Type
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel as PydanticBaseModel
from pydantic import HttpUrl

from paperap.client import PaperlessClient
from paperap.const import URLS, Endpoints
from paperap.exceptions import (
    ConfigurationError,
    ModelValidationError,
    ObjectNotFoundError,
    ResourceNotFoundError,
    ResponseParsingError,
)
from paperap.models.abstract.model import BaseModel, StandardModel
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.resources.base import BaseResource, StandardResource
from paperap.signals import SignalRegistry, registry
from tests.lib import UnitTestCase


class ExampleModel(BaseModel):
    """Test model for BaseResource tests."""

    name: str
    value: int = 0

    def is_new(self) -> bool:
        return False

    class Meta(BaseModel.Meta):
        """Metadata for TestModel."""

        name = "test"
        field_map = {"api_name": "name"}


class ExampleStandardModel(StandardModel):
    """Test model for StandardResource tests."""

    name: str
    value: int = 0

    class Meta(StandardModel.Meta):
        """Metadata for TestStandardModel."""

        name = "test"
        field_map = {"api_name": "name"}


class ExampleQuerySet(BaseQuerySet[ExampleModel]):
    """Test queryset for BaseResource tests."""

    pass


class ExampleStandardQuerySet(StandardQuerySet[ExampleStandardModel]):
    """Test queryset for StandardResource tests."""

    pass


class TestBaseResource(UnitTestCase):
    """
    Test the BaseResource class.

    Written By claude
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()

        # Create a mock client instead of using the real one
        self.mock_client = MagicMock(spec=PaperlessClient)

        # Create a concrete subclass of BaseResource for testing
        class ConcreteBaseResource(BaseResource[ExampleModel, ExampleQuerySet]):
            model_class = ExampleModel
            queryset_class = ExampleQuerySet
            endpoints = {
                "list": Template("${resource}/"),
                "create": Template("${resource}/"),
            }

        self.resource_class = ConcreteBaseResource
        self.resource = self.resource_class(self.mock_client)

        # Reset signal registry for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")

    def test_init(self) -> None:
        """
        Test initialization of BaseResource.

        Written By claude
        """
        resource = self.resource_class(self.client)
        self.assertEqual(resource.client, self.client)
        self.assertEqual(resource.name, "tests")
        self.assertEqual(resource.endpoints["list"].template, "tests/")
        self.assertEqual(resource.endpoints["create"].template, "tests/")
        self.assertEqual(resource.model_class._resource, resource)  # type: ignore

    def test_init_subclass_validation(self) -> None:
        """
        Test validation during subclass initialization.

        Written By claude
        """
        # Test missing model_class
        with self.assertRaises(ConfigurationError):
            class InvalidResource(BaseResource):  # type: ignore
                pass

        # Test invalid endpoints
        with self.assertRaises(ModelValidationError):
            class InvalidEndpointsResource(BaseResource[ExampleModel, ExampleQuerySet]):
                model_class = ExampleModel
                queryset_class = ExampleQuerySet
                endpoints = "not_a_dict"  # type: ignore

        # Test invalid endpoint value
        with self.assertRaises(ModelValidationError):
            class InvalidEndpointValueResource(BaseResource[ExampleModel, ExampleQuerySet]):
                model_class = ExampleModel
                queryset_class = ExampleQuerySet
                endpoints = {"list": 123}  # type: ignore

    def test_get_endpoint(self) -> None:
        """
        Test get_endpoint method.

        Written By claude
        """
        # Mock the get_endpoint method to return a string instead of HttpUrl
        self.resource.get_endpoint = MagicMock()
        self.resource.get_endpoint.return_value = "tests/"

        # Now test with the mocked method
        endpoint = self.resource.get_endpoint("list")
        self.assertEqual(endpoint, "tests/")

        # Test with additional substitutions
        self.resource.get_endpoint.return_value = "tests/123/"
        endpoint = self.resource.get_endpoint("detail", id=123)
        self.assertEqual(endpoint, "tests/123/")

    def test_all(self) -> None:
        """
        Test all method returns a queryset.

        Written By claude
        """
        queryset = self.resource.all()
        self.assertIsInstance(queryset, ExampleQuerySet)
        self.assertEqual(queryset.resource, self.resource)

    def test_filter(self) -> None:
        """
        Test filter method returns a filtered queryset.

        Written By claude
        """
        with patch.object(ExampleQuerySet, 'filter') as mock_filter:
            mock_filter.return_value = "filtered_queryset"
            result = self.resource.filter(name="test")
            mock_filter.assert_called_once_with(name="test")
            self.assertEqual(result, "filtered_queryset")

    def test_get_not_implemented(self) -> None:
        """
        Test get method raises NotImplementedError.

        Written By claude
        """
        with self.assertRaises(NotImplementedError):
            self.resource.get(1)

    def test_create(self) -> None:
        """
        Test create method.

        Written By claude
        """
        # Mock client.request to return a response
        self.mock_client.request.return_value = {"name": "test", "value": 42}

        # Mock get_endpoint to return a valid string
        self.resource.get_endpoint = MagicMock(return_value="tests/")

        # Test create method
        model = self.resource.create(name="test", value=42)

        # Verify client.request was called correctly
        self.mock_client.request.assert_called_once_with("POST", "tests/", data={"name": "test", "value": 42})

        # Verify model was created correctly
        self.assertIsInstance(model, ExampleModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with missing create endpoint
        self.resource.get_endpoint.return_value = None
        with self.assertRaises(ConfigurationError):
            self.resource.create(name="test")

        # Test with empty response
        self.resource.get_endpoint.return_value = "tests/"
        self.mock_client.request.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.resource.create(name="test")

    def test_update_not_implemented(self) -> None:
        """
        Test update method raises NotImplementedError.

        Written By claude
        """
        model = ExampleModel(name="test")
        with self.assertRaises(NotImplementedError):
            self.resource.update(model)

    def test_update_dict_not_implemented(self) -> None:
        """
        Test update_dict method raises NotImplementedError.

        Written By claude
        """
        with self.assertRaises(NotImplementedError):
            self.resource.update_dict(1, name="test")

    def test_delete_not_implemented(self) -> None:
        """
        Test delete method raises NotImplementedError.

        Written By claude
        """
        with self.assertRaises(NotImplementedError):
            self.resource.delete(1)

    def test_parse_to_model(self) -> None:
        """
        Test parse_to_model method.

        Written By claude
        """
        # Test with valid data
        model = self.resource.parse_to_model({"name": "test", "value": 42})
        self.assertIsInstance(model, ExampleModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with invalid data
        with self.assertLogs(level="ERROR"):
            with self.assertRaises(Exception):
                self.resource.parse_to_model({"invalid": "data"})

    def test_transform_data_input(self) -> None:
        """
        Test transform_data_input method.

        Written By claude
        """
        # Test with field mapping
        data = self.resource.transform_data_input(api_name="test", value=42)
        self.assertEqual(data, {"name": "test", "value": 42})

        # Test without field mapping
        data = self.resource.transform_data_input(name="test", value=42)
        self.assertEqual(data, {"name": "test", "value": 42})

    def test_transform_data_output(self) -> None:
        """
        Test transform_data_output method.

        Written By claude
        """
        # Test with model
        model = ExampleModel(name="test", value=42)
        data = self.resource.transform_data_output(model)
        self.assertEqual(data, {"api_name": "test", "value": 42})

        # Test with data
        data = self.resource.transform_data_output(name="test", value=42)
        self.assertEqual(data, {"api_name": "test", "value": 42})

        # Test with both model and data (should raise ValueError)
        with self.assertRaises(ValueError):
            self.resource.transform_data_output(model, name="test")

    def test_create_model(self) -> None:
        """
        Test create_model method.

        Written By claude
        """
        model = self.resource.create_model(name="test", value=42)
        self.assertIsInstance(model, ExampleModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)
        self.assertEqual(model._resource, self.resource)  # type: ignore

    def test_request_raw(self) -> None:
        """
        Test request_raw method.

        Written By claude
        """
        # Mock client.request to return a response
        self.mock_client.request.return_value = {"results": [{"name": "test"}]}

        # Mock get_endpoint to return a valid string
        self.resource.get_endpoint = MagicMock(return_value="tests/")

        # Test with explicit URL
        response = self.resource.request_raw("https://example.com/api/tests/")
        self.mock_client.request.assert_called_with("GET", "https://example.com/api/tests/", params=None, data=None)
        self.assertEqual(response, {"results": [{"name": "test"}]})

        # Test with template URL
        response = self.resource.request_raw(Template("${resource}/"))
        self.mock_client.request.assert_called_with("GET", "tests/", params=None, data=None)

        # Test with default URL
        response = self.resource.request_raw()
        self.mock_client.request.assert_called_with("GET", "tests/", params=None, data=None)

        # Test with missing list endpoint
        self.resource.get_endpoint.return_value = None
        with self.assertRaises(ConfigurationError):
            self.resource.request_raw()

    def test_handle_response(self) -> None:
        """
        Test handle_response method.

        Written By claude
        """
        # Test with results list
        results = list(self.resource.handle_dict_response(results=[{"name": "test1"}, {"name": "test2"}]))
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], ExampleModel)
        self.assertEqual(results[0].name, "test1")
        self.assertEqual(results[1].name, "test2")

        # Test with single result dict
        results = list(self.resource.handle_dict_response(results={"name": "test"}))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ExampleModel)
        self.assertEqual(results[0].name, "test")

        # Test with results in top-level response
        results = list(self.resource.handle_dict_response(name="test"))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ExampleModel)
        self.assertEqual(results[0].name, "test")

        # Test with invalid results type
        with self.assertRaises(ResponseParsingError):
            list(self.resource.handle_dict_response(results=123))  # type: ignore

    def test_handle_results(self) -> None:
        """
        Test handle_results method.

        Written By claude
        """
        # Test with valid results
        results = list(self.resource.handle_results([{"name": "test1"}, {"name": "test2"}]))
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], ExampleModel)
        self.assertEqual(results[0].name, "test1")
        self.assertEqual(results[1].name, "test2")

        # Test with invalid results type
        with self.assertRaises(ResponseParsingError):
            list(self.resource.handle_results("not_a_list"))  # type: ignore

        # Test with invalid item type
        with self.assertRaises(ResponseParsingError):
            list(self.resource.handle_results([1, 2, 3]))  # type: ignore

    def test_call(self) -> None:
        """
        Test __call__ method.

        Written By claude
        """
        with patch.object(self.resource, 'filter') as mock_filter:
            mock_filter.return_value = "filtered_queryset"
            result = self.resource(name="test")
            mock_filter.assert_called_once_with(name="test")
            self.assertEqual(result, "filtered_queryset")


class TestStandardResource(UnitTestCase):
    """
    Test the StandardResource class.

    Written By claude
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()

        # Create a mock client instead of using the real one
        self.mock_client = MagicMock(spec=PaperlessClient)

        # Create a concrete subclass of StandardResource for testing
        class ConcreteStandardResource(StandardResource[ExampleStandardModel, ExampleStandardQuerySet]):
            model_class = ExampleStandardModel
            queryset_class = ExampleStandardQuerySet
            endpoints = {
                "list": Template("${resource}/"),
                "detail": Template("${resource}/${pk}/"),
                "create": Template("${resource}/"),
                "update": Template("${resource}/${pk}/"),
                "delete": Template("${resource}/${pk}/"),
                "bulk": Template("${resource}/"),
            }

        self.resource_class = ConcreteStandardResource
        self.resource = self.resource_class(self.mock_client)

        # Reset signal registry for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")

    def test_get(self) -> None:
        """
        Test get method.

        Written By claude
        """
        # Mock client.request to return a response
        self.mock_client.request.return_value = {"id": 1, "name": "test", "value": 42}

        # Mock get_endpoint to return a valid string
        self.resource.get_endpoint = MagicMock(return_value="tests/1/")

        # Test get method
        model = self.resource.get(1)

        # Verify client.request was called correctly
        self.mock_client.request.assert_called_once_with("GET", "tests/1/")

        # Verify model was created correctly
        self.assertIsInstance(model, ExampleStandardModel)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with missing detail endpoint
        self.resource.get_endpoint.return_value = None
        with self.assertRaises(ConfigurationError):
            self.resource.get(1)

        # Test with empty response
        self.resource.get_endpoint.return_value = "tests/1/"
        self.mock_client.request.return_value = None
        with self.assertRaises(ObjectNotFoundError):
            self.resource.get(1)

        # Test with response missing ID
        self.mock_client.request.return_value = {"name": "test"}
        with self.assertRaises(ObjectNotFoundError):
            self.resource.get(1)

    def test_update(self) -> None:
        """
        Test update method.

        Written By claude
        """
        # Create a model to update
        model = ExampleStandardModel(id=1, name="test", value=42)

        # Mock update_dict to return an updated model
        updated_model = ExampleStandardModel(id=1, name="updated", value=43)
        with patch.object(self.resource, 'update_dict', return_value=updated_model) as mock_update_dict:
            # Test update method
            result = self.resource.update(model)

            # Verify update_dict was called correctly
            mock_update_dict.assert_called_once_with(1, api_name="test", value=42)

            # Verify result is the updated model
            self.assertEqual(result, updated_model)

    def test_delete(self) -> None:
        """
        Test delete method.

        Written By claude
        """
        # Mock get_endpoint to return a valid string
        self.resource.get_endpoint = MagicMock()
        self.resource.get_endpoint.return_value = "tests/1/"

        # Test delete with ID
        self.resource.delete(1)
        self.mock_client.request.assert_called_once_with("DELETE", "tests/1/")

        # Reset mocks and setup for next test
        self.mock_client.request.reset_mock()
        self.resource.get_endpoint.return_value = "tests/2/"

        # Test delete with model
        model = ExampleStandardModel(id=2, name="test")
        self.resource.delete(model)
        self.mock_client.request.assert_called_once_with("DELETE", "tests/2/")

        # Test with missing ID
        with self.assertRaises(ValueError):
            self.resource.delete(None)  # type: ignore

        # Test with missing delete endpoint
        self.resource.get_endpoint.return_value = None
        with self.assertRaises(ConfigurationError):
            self.resource.delete(1)

    def test_update_dict(self) -> None:
        """
        Test update_dict method.

        Written By claude
        """
        # Mock client.request to return a response
        self.mock_client.request.return_value = {"id": 1, "name": "updated", "value": 43}

        # Mock get_endpoint to return a valid string
        self.resource.get_endpoint = MagicMock(return_value="tests/1/")

        # Test update_dict method
        model = self.resource.update_dict(1, name="updated", value=43)

        # Verify client.request was called correctly
        self.mock_client.request.assert_called_once_with("PUT", "tests/1/", data={"name": "updated", "value": 43})

        # Verify model was updated correctly
        self.assertIsInstance(model, ExampleStandardModel)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "updated")
        self.assertEqual(model.value, 43)

        # Test with missing update endpoint
        self.resource.get_endpoint.return_value = None
        with self.assertRaises(ConfigurationError):
            self.resource.update_dict(1, name="updated")

        # Test with empty response
        self.resource.get_endpoint.return_value = "tests/1/"
        self.mock_client.request.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.resource.update_dict(1, name="updated")


if __name__ == "__main__":
    unittest.main()
