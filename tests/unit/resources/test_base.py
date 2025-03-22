"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_base.py
        Project: paperap
        Created: 2025-03-21
        Version: 0.0.9
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-21     By Jess Mann

"""

from __future__ import annotations

import unittest
from string import Template
from typing import Any, Dict, Iterator, List, Optional, Type
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel as PydanticBaseModel

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


class TestModel(BaseModel):
    """Test model for BaseResource tests."""

    name: str
    value: int = 0

    class Meta(BaseModel.Meta):
        """Metadata for TestModel."""

        name = "test"
        field_map = {"api_name": "name"}


class TestStandardModel(StandardModel):
    """Test model for StandardResource tests."""

    name: str
    value: int = 0

    class Meta(StandardModel.Meta):
        """Metadata for TestStandardModel."""

        name = "test"
        field_map = {"api_name": "name"}


class TestQuerySet(BaseQuerySet[TestModel]):
    """Test queryset for BaseResource tests."""

    pass


class TestStandardQuerySet(StandardQuerySet[TestStandardModel]):
    """Test queryset for StandardResource tests."""

    pass


class TestBaseResource(unittest.TestCase):
    """
    Test the BaseResource class.

    Written By claude
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.client = MagicMock(spec=PaperlessClient)

        # Create a concrete subclass of BaseResource for testing
        class ConcreteBaseResource(BaseResource[TestModel, TestQuerySet]):
            model_class = TestModel
            queryset_class = TestQuerySet
            endpoints = {
                "list": Template("${resource}/"),
                "create": Template("${resource}/"),
            }

        self.resource_class = ConcreteBaseResource
        self.resource = self.resource_class(self.client)

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
            class InvalidEndpointsResource(BaseResource[TestModel, TestQuerySet]):
                model_class = TestModel
                queryset_class = TestQuerySet
                endpoints = "not_a_dict"  # type: ignore

        # Test invalid endpoint value
        with self.assertRaises(ModelValidationError):
            class InvalidEndpointValueResource(BaseResource[TestModel, TestQuerySet]):
                model_class = TestModel
                queryset_class = TestQuerySet
                endpoints = {"list": 123}  # type: ignore

    def test_get_endpoint(self) -> None:
        """
        Test get_endpoint method.

        Written By claude
        """
        endpoint = self.resource.get_endpoint("list")
        self.assertEqual(endpoint, "tests/")

        # Test with additional substitutions
        self.resource.endpoints["detail"] = Template("${resource}/${id}/")
        endpoint = self.resource.get_endpoint("detail", id=123)
        self.assertEqual(endpoint, "tests/123/")

    def test_all(self) -> None:
        """
        Test all method returns a queryset.

        Written By claude
        """
        queryset = self.resource.all()
        self.assertIsInstance(queryset, TestQuerySet)
        self.assertEqual(queryset.resource, self.resource)

    def test_filter(self) -> None:
        """
        Test filter method returns a filtered queryset.

        Written By claude
        """
        with patch.object(TestQuerySet, 'filter') as mock_filter:
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
        self.client.request.return_value = {"name": "test", "value": 42}

        # Test create method
        model = self.resource.create(name="test", value=42)

        # Verify client.request was called correctly
        self.client.request.assert_called_once_with("POST", "tests/", data={"name": "test", "value": 42})

        # Verify model was created correctly
        self.assertIsInstance(model, TestModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with missing create endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.create(name="test")

        # Test with empty response
        self.client.request.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.resource.create(name="test")

    def test_update_not_implemented(self) -> None:
        """
        Test update method raises NotImplementedError.

        Written By claude
        """
        model = TestModel(name="test")
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
        self.assertIsInstance(model, TestModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with invalid data
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
        model = TestModel(name="test", value=42)
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
        self.assertIsInstance(model, TestModel)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)
        self.assertEqual(model._resource, self.resource)  # type: ignore

    def test_request_raw(self) -> None:
        """
        Test request_raw method.

        Written By claude
        """
        # Mock client.request to return a response
        self.client.request.return_value = {"results": [{"name": "test"}]}

        # Test with explicit URL
        response = self.resource.request_raw("https://example.com/api/tests/")
        self.client.request.assert_called_with("GET", "https://example.com/api/tests/", params=None, data=None)
        self.assertEqual(response, {"results": [{"name": "test"}]})

        # Test with template URL
        response = self.resource.request_raw(Template("${resource}/"))
        self.client.request.assert_called_with("GET", "tests/", params=None, data=None)

        # Test with default URL
        response = self.resource.request_raw()
        self.client.request.assert_called_with("GET", "tests/", params=None, data=None)

        # Test with missing list endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.request_raw()

    def test_handle_response(self) -> None:
        """
        Test handle_response method.

        Written By claude
        """
        # Test with results list
        results = list(self.resource.handle_response(results=[{"name": "test1"}, {"name": "test2"}]))
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], TestModel)
        self.assertEqual(results[0].name, "test1")
        self.assertEqual(results[1].name, "test2")

        # Test with single result dict
        results = list(self.resource.handle_response(results={"name": "test"}))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], TestModel)
        self.assertEqual(results[0].name, "test")

        # Test with results in top-level response
        results = list(self.resource.handle_response(name="test"))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], TestModel)
        self.assertEqual(results[0].name, "test")

        # Test with invalid results type
        with self.assertRaises(ResponseParsingError):
            list(self.resource.handle_response(results=123))  # type: ignore

    def test_handle_results(self) -> None:
        """
        Test handle_results method.

        Written By claude
        """
        # Test with valid results
        results = list(self.resource.handle_results([{"name": "test1"}, {"name": "test2"}]))
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], TestModel)
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


class TestStandardResource(unittest.TestCase):
    """
    Test the StandardResource class.

    Written By claude
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.client = MagicMock(spec=PaperlessClient)

        # Create a concrete subclass of StandardResource for testing
        class ConcreteStandardResource(StandardResource[TestStandardModel, TestStandardQuerySet]):
            model_class = TestStandardModel
            queryset_class = TestStandardQuerySet
            endpoints = {
                "list": Template("${resource}/"),
                "detail": Template("${resource}/${pk}/"),
                "create": Template("${resource}/"),
                "update": Template("${resource}/${pk}/"),
                "delete": Template("${resource}/${pk}/"),
                "bulk": Template("${resource}/"),
            }

        self.resource_class = ConcreteStandardResource
        self.resource = self.resource_class(self.client)

        # Reset signal registry for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")

    def test_get(self) -> None:
        """
        Test get method.

        Written By claude
        """
        # Mock client.request to return a response
        self.client.request.return_value = {"id": 1, "name": "test", "value": 42}

        # Test get method
        model = self.resource.get(1)

        # Verify client.request was called correctly
        self.client.request.assert_called_once_with("GET", "tests/1/")

        # Verify model was created correctly
        self.assertIsInstance(model, TestStandardModel)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test with missing detail endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.get(1)

        # Test with empty response
        self.client.request.return_value = None
        with self.assertRaises(ObjectNotFoundError):
            self.resource.get(1)

        # Test with response missing ID
        self.client.request.return_value = {"name": "test"}
        with self.assertRaises(ObjectNotFoundError):
            self.resource.get(1)

    def test_update(self) -> None:
        """
        Test update method.

        Written By claude
        """
        # Create a model to update
        model = TestStandardModel(id=1, name="test", value=42)

        # Mock update_dict to return an updated model
        updated_model = TestStandardModel(id=1, name="updated", value=43)
        with patch.object(self.resource, 'update_dict', return_value=updated_model) as mock_update_dict:
            # Test update method
            result = self.resource.update(model)

            # Verify update_dict was called correctly
            mock_update_dict.assert_called_once_with(1, api_name="test", value=42)

            # Verify result is the updated model
            self.assertEqual(result, updated_model)

    def test_bulk_action(self) -> None:
        """
        Test bulk_action method.

        Written By claude
        """
        # Mock client.request to return a response
        self.client.request.return_value = {"success": True, "count": 2}

        # Test bulk_action method
        response = self.resource.bulk_action("update", [1, 2], name="updated")

        # Verify client.request was called correctly
        self.client.request.assert_called_once_with(
            "POST",
            "tests/bulk_edit/",
            data={"action": "update", "documents": [1, 2], "name": "updated"}
        )

        # Verify response
        self.assertEqual(response, {"success": True, "count": 2})

        # Test with missing bulk endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.bulk_action("update", [1, 2])

    def test_bulk_delete(self) -> None:
        """
        Test bulk_delete method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}
            response = self.resource.bulk_delete([1, 2])
            mock_bulk_action.assert_called_once_with("delete", [1, 2])
            self.assertEqual(response, {"success": True})

    def test_bulk_update(self) -> None:
        """
        Test bulk_update method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}

            # Test with simple data
            response = self.resource.bulk_update([1, 2], name="updated")
            mock_bulk_action.assert_called_once_with("update", [1, 2], api_name="updated")
            self.assertEqual(response, {"success": True})

    def test_bulk_assign_tags(self) -> None:
        """
        Test bulk_assign_tags method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}

            # Test add tags
            response = self.resource.bulk_assign_tags([1, 2], [10, 20])
            mock_bulk_action.assert_called_once_with("add_tags", [1, 2], tags=[10, 20])
            self.assertEqual(response, {"success": True})

            # Test remove existing tags
            mock_bulk_action.reset_mock()
            response = self.resource.bulk_assign_tags([1, 2], [10, 20], remove_existing=True)
            mock_bulk_action.assert_called_once_with("remove_tags", [1, 2], tags=[10, 20])
            self.assertEqual(response, {"success": True})

    def test_bulk_assign_correspondent(self) -> None:
        """
        Test bulk_assign_correspondent method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}
            response = self.resource.bulk_assign_correspondent([1, 2], 10)
            mock_bulk_action.assert_called_once_with("set_correspondent", [1, 2], correspondent=10)
            self.assertEqual(response, {"success": True})

    def test_bulk_assign_document_type(self) -> None:
        """
        Test bulk_assign_document_type method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}
            response = self.resource.bulk_assign_document_type([1, 2], 10)
            mock_bulk_action.assert_called_once_with("set_document_type", [1, 2], document_type=10)
            self.assertEqual(response, {"success": True})

    def test_bulk_assign_storage_path(self) -> None:
        """
        Test bulk_assign_storage_path method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}
            response = self.resource.bulk_assign_storage_path([1, 2], 10)
            mock_bulk_action.assert_called_once_with("set_storage_path", [1, 2], storage_path=10)
            self.assertEqual(response, {"success": True})

    def test_bulk_assign_owner(self) -> None:
        """
        Test bulk_assign_owner method.

        Written By claude
        """
        with patch.object(self.resource, 'bulk_action') as mock_bulk_action:
            mock_bulk_action.return_value = {"success": True}
            response = self.resource.bulk_assign_owner([1, 2], 10)
            mock_bulk_action.assert_called_once_with("set_owner", [1, 2], owner=10)
            self.assertEqual(response, {"success": True})

    def test_delete(self) -> None:
        """
        Test delete method.

        Written By claude
        """
        # Test delete with ID
        self.resource.delete(1)
        self.client.request.assert_called_once_with("DELETE", "tests/1/")

        # Test delete with model
        self.client.request.reset_mock()
        model = TestStandardModel(id=2, name="test")
        self.resource.delete(model)
        self.client.request.assert_called_once_with("DELETE", "tests/2/")

        # Test with missing ID
        with self.assertRaises(ValueError):
            self.resource.delete(None)  # type: ignore

        # Test with missing delete endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.delete(1)

    def test_update_dict(self) -> None:
        """
        Test update_dict method.

        Written By claude
        """
        # Mock client.request to return a response
        self.client.request.return_value = {"id": 1, "name": "updated", "value": 43}

        # Test update_dict method
        model = self.resource.update_dict(1, name="updated", value=43)

        # Verify client.request was called correctly
        self.client.request.assert_called_once_with("PUT", "tests/1/", data={"name": "updated", "value": 43})

        # Verify model was updated correctly
        self.assertIsInstance(model, TestStandardModel)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "updated")
        self.assertEqual(model.value, 43)

        # Test with missing update endpoint
        self.resource.endpoints = {}  # type: ignore
        with self.assertRaises(ConfigurationError):
            self.resource.update_dict(1, name="updated")

        # Test with empty response
        self.client.request.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.resource.update_dict(1, name="updated")


if __name__ == "__main__":
    unittest.main()
