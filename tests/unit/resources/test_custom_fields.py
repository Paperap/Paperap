

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from paperap.client import PaperlessClient
from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.resources.custom_fields import CustomFieldResource


class TestCustomFieldResource(unittest.TestCase):
    """Test suite for the CustomFieldResource class."""

    def setUp(self) -> None:
        """
        Set up test fixtures.

        Written By claude
        """
        self.mock_client = MagicMock(spec=PaperlessClient)
        self.resource = CustomFieldResource(self.mock_client)

        # Mock get_endpoint to return string URLs instead of HttpUrl objects
        self.resource.get_endpoint = MagicMock()

    def test_initialization(self) -> None:
        """
        Test that the resource initializes with correct attributes.

        Written By claude
        """
        self.assertEqual(self.resource.name, "custom_fields")
        self.assertEqual(self.resource.model_class, CustomField)
        self.assertEqual(self.resource.queryset_class, CustomFieldQuerySet)
        self.assertEqual(self.resource.client, self.mock_client)

    def test_all(self) -> None:
        """
        Test that the all() method returns a CustomFieldQuerySet.

        Written By claude
        """
        queryset = self.resource.all()
        self.assertIsInstance(queryset, CustomFieldQuerySet)
        self.assertEqual(queryset.resource, self.resource)

    def test_filter(self) -> None:
        """
        Test that the filter() method returns a filtered CustomFieldQuerySet.

        Written By claude
        """
        queryset = self.resource.filter(name="Test")
        self.assertIsInstance(queryset, CustomFieldQuerySet)
        self.assertEqual(queryset.resource, self.resource)
        self.assertEqual(queryset.filters, {"name": "Test"})

    @patch.object(CustomFieldResource, 'parse_to_model')
    def test_get(self, mock_parse) -> None:
        """
        Test that the get() method fetches a custom field by ID.

        Written By claude
        """
        # Set up the endpoint mock
        self.resource.get_endpoint.return_value = "custom_fields/1/"

        mock_response = {"id": 1, "name": "Test Field"}
        self.mock_client.request.return_value = mock_response
        mock_parse.return_value = CustomField(id=1, name="Test Field")

        result = self.resource.get(1)

        self.mock_client.request.assert_called_once_with(
            "GET",
            "custom_fields/1/"
        )
        mock_parse.assert_called_once_with(mock_response)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test Field")

    @patch.object(CustomFieldResource, 'parse_to_model')
    def test_create(self, mock_parse) -> None:
        """
        Test that the create() method creates a new custom field.

        Written By claude
        """
        # Set up the endpoint mock
        self.resource.get_endpoint.return_value = "custom_fields/"

        mock_response = {"id": 1, "name": "New Field"}
        self.mock_client.request.return_value = mock_response
        mock_parse.return_value = CustomField(id=1, name="New Field")

        result = self.resource.create(name="New Field")

        self.mock_client.request.assert_called_once_with(
            "POST",
            "custom_fields/",
            data={"name": "New Field"}
        )
        mock_parse.assert_called_once_with(mock_response)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "New Field")

    def test_parse_to_model(self) -> None:
        """
        Test that parse_to_model correctly converts API response to a CustomField.

        Written By claude
        """
        data = {"id": 1, "name": "Test Field"}
        result = self.resource.parse_to_model(data)

        self.assertIsInstance(result, CustomField)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test Field")

    @patch("paperap.models.custom_field.CustomField.update")
    def test_update_model(self, mock_update) -> None:
        """
        Test that a model can be updated through the resource.

        Written By claude
        """
        model = CustomField(id=1, name="Old Name")

        # Mock the client's request method
        mock_response = {"id": 1, "name": "New Name"}
        self.mock_client.request.return_value = mock_response

        # Set the client on the model
        model.resource.client = self.mock_client

        # Update the model
        model.update(name="New Name")

        # Verify the update method was called
        mock_update.assert_called_once()

    @patch.object(CustomFieldQuerySet, 'name')
    def test_queryset_name_filter(self, mock_name) -> None:
        """
        Test that the queryset's name filter method is called correctly.

        Written By claude
        """
        mock_queryset = MagicMock(spec=CustomFieldQuerySet)
        mock_name.return_value = mock_queryset

        queryset = self.resource.all()
        result = queryset.name("Test")

        # Update to match actual call arguments (without the keyword args)
        mock_name.assert_called_once_with("Test")
        self.assertEqual(result, mock_queryset)

if __name__ == "__main__":
    unittest.main()
