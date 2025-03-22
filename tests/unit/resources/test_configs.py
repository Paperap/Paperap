"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_configs.py
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
from unittest import mock

from paperap.client import PaperlessClient
from paperap.models.config import Config
from paperap.resources.configs import ConfigResource
from paperap.exceptions import ObjectNotFoundError


class TestConfigResource(unittest.TestCase):
    """Test suite for the ConfigResource class."""

    def setUp(self) -> None:
        """
        Set up test fixtures before each test method.

        Written By claude
        """
        self.mock_client = mock.MagicMock(spec=PaperlessClient)
        self.resource = ConfigResource(self.mock_client)

        # Sample config data for testing
        self.config_data = {
            "id": 1,
            "key": "test_key",
            "value": "test_value"
        }

        # Sample config object
        self.config = Config(**self.config_data)

    def test_init(self) -> None:
        """
        Test that the ConfigResource initializes correctly.

        Written By claude
        """
        self.assertEqual(self.resource.model_class, Config)
        self.assertEqual(self.resource.name, "configs")
        self.assertEqual(self.resource.client, self.mock_client)

    def test_get_config(self) -> None:
        """
        Test retrieving a config by ID.

        Written By claude
        """
        # Mock the client's request method
        self.mock_client.request.return_value = self.config_data

        # Call the get method
        config = self.resource.get(1)

        # Verify the request was made correctly
        self.mock_client.request.assert_called_once_with(
            "GET",
            "configs/1/",
            params=None
        )

        # Verify the returned config
        self.assertIsInstance(config, Config)
        self.assertEqual(config.id, 1)
        self.assertEqual(config.key, "test_key")
        self.assertEqual(config.value, "test_value")

    def test_get_nonexistent_config(self) -> None:
        """
        Test retrieving a config that doesn't exist.

        Written By claude
        """
        # Mock the client's request method to raise an exception
        self.mock_client.request.side_effect = ObjectNotFoundError(
            message="Config not found",
            resource_name="configs",
            model_id=999
        )

        # Verify that the correct exception is raised
        with self.assertRaises(ObjectNotFoundError) as context:
            self.resource.get(999)

        # Verify the exception details
        self.assertEqual(context.exception.resource_name, "configs")
        self.assertEqual(context.exception.model_id, 999)

    def test_create_config(self) -> None:
        """
        Test creating a new config.

        Written By claude
        """
        # Mock the client's request method
        self.mock_client.request.return_value = self.config_data

        # Call the create method
        config = self.resource.create(key="test_key", value="test_value")

        # Verify the request was made correctly
        self.mock_client.request.assert_called_once_with(
            "POST",
            "configs/",
            data={"key": "test_key", "value": "test_value"}
        )

        # Verify the returned config
        self.assertIsInstance(config, Config)
        self.assertEqual(config.key, "test_key")
        self.assertEqual(config.value, "test_value")

    def test_update_config(self) -> None:
        """
        Test updating an existing config.

        Written By claude
        """
        # Updated config data
        updated_config_data = {
            "id": 1,
            "key": "test_key",
            "value": "updated_value"
        }

        # Mock the client's request method
        self.mock_client.request.return_value = updated_config_data

        # Create a config instance and update it
        config = Config(**self.config_data)
        config.update(value="updated_value")

        # Verify the request was made correctly
        self.mock_client.request.assert_called_once_with(
            "PUT",
            "configs/1/",
            data={"id": 1, "key": "test_key", "value": "updated_value"}
        )

        # Verify the config was updated
        self.assertEqual(config.value, "updated_value")

    def test_filter_configs(self) -> None:
        """
        Test filtering configs.

        Written By claude
        """
        # Mock response data for multiple configs
        configs_data = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {"id": 1, "key": "key1", "value": "value1"},
                {"id": 2, "key": "key2", "value": "value2"}
            ]
        }

        # Mock the client's request method
        self.mock_client.request.return_value = configs_data

        # Call the filter method
        queryset = self.resource.filter(key="key")

        # Verify the request parameters
        self.mock_client.request.assert_called_once_with(
            "GET",
            "configs/",
            params={"key": "key"}
        )

        # Verify the queryset is properly configured
        self.assertEqual(queryset.resource, self.resource)
        self.assertEqual(queryset.filters, {"key": "key"})

    def test_delete_config(self) -> None:
        """
        Test deleting a config.

        Written By claude
        """
        # Create a config instance
        config = Config(**self.config_data)

        # Mock the client's request method
        self.mock_client.request.return_value = None

        # Delete the config
        config.delete()

        # Verify the request was made correctly
        self.mock_client.request.assert_called_once_with(
            "DELETE",
            "configs/1/",
            params=None
        )

    def test_bulk_action(self) -> None:
        """
        Test performing a bulk action on configs.

        Written By claude
        """
        # Mock response for bulk action
        bulk_response = {"success": True, "count": 2}

        # Mock the client's request method
        self.mock_client.request.return_value = bulk_response

        # Perform a bulk action
        result = self.resource.bulk_action("delete", [1, 2])

        # Verify the request was made correctly
        self.mock_client.request.assert_called_once_with(
            "POST",
            "configs/bulk_delete/",
            data={"ids": [1, 2]}
        )

        # Verify the result
        self.assertEqual(result, bulk_response)

    def test_parse_to_model(self) -> None:
        """
        Test parsing a dictionary to a Config model.

        Written By claude
        """
        # Parse a dictionary to a Config model
        config = self.resource.parse_to_model(self.config_data)

        # Verify the parsed model
        self.assertIsInstance(config, Config)
        self.assertEqual(config.id, 1)
        self.assertEqual(config.key, "test_key")
        self.assertEqual(config.value, "test_value")


if __name__ == "__main__":
    unittest.main()
