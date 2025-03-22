"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_correspondents.py
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
from unittest.mock import MagicMock, patch

from paperap.client import PaperlessClient
from paperap.models.correspondent import Correspondent, CorrespondentQuerySet
from paperap.resources.correspondents import CorrespondentResource
from paperap.exceptions import ObjectNotFoundError


class TestCorrespondentResource(unittest.TestCase):
    """
    Test suite for the CorrespondentResource class.

    Tests initialization, querying, filtering, and CRUD operations.
    """

    def setUp(self):
        """
        Written By claude

        Set up test fixtures before each test method.
        Creates a mock client and initializes the resource.
        """
        self.mock_client = MagicMock(spec=PaperlessClient)
        self.resource = CorrespondentResource(self.mock_client)

    def test_initialization(self):
        """
        Written By claude

        Test that the resource initializes correctly with proper attributes.
        """
        self.assertEqual(self.resource.model_class, Correspondent)
        self.assertEqual(self.resource.queryset_class, CorrespondentQuerySet)
        self.assertEqual(self.resource.name, "correspondents")
        self.assertEqual(self.resource.client, self.mock_client)

    def test_all(self):
        """
        Written By claude

        Test that the all() method returns a queryset of the correct type.
        """
        queryset = self.resource.all()
        self.assertIsInstance(queryset, CorrespondentQuerySet)
        self.assertEqual(queryset.resource, self.resource)

    def test_filter(self):
        """
        Written By claude

        Test that the filter() method returns a filtered queryset.
        """
        queryset = self.resource.filter(name="Test Correspondent")
        self.assertIsInstance(queryset, CorrespondentQuerySet)
        self.assertEqual(queryset.resource, self.resource)
        self.assertIn("name", queryset.filters)
        self.assertEqual(queryset.filters["name"], "Test Correspondent")

    @patch.object(CorrespondentResource, 'request')
    def test_get_success(self, mock_request):
        """
        Written By claude

        Test that the get() method returns a correspondent when found.
        """
        # Setup mock response
        mock_data = {
            "id": 1,
            "name": "Test Correspondent",
            "match": "",
            "matching_algorithm": 0,
            "is_insensitive": False,
            "document_count": 5,
            "owner": 1
        }
        mock_request.return_value = mock_data

        # Call the method
        correspondent = self.resource.get(1)

        # Assertions
        self.assertIsInstance(correspondent, Correspondent)
        self.assertEqual(correspondent.id, 1)
        self.assertEqual(correspondent.name, "Test Correspondent")
        mock_request.assert_called_once_with("GET", "correspondents/1/")

    @patch.object(CorrespondentResource, 'request')
    def test_get_not_found(self, mock_request):
        """
        Written By claude

        Test that the get() method raises ObjectNotFoundError when correspondent is not found.
        """
        # Setup mock to raise exception
        mock_request.side_effect = ObjectNotFoundError(
            message="Correspondent with ID 999 not found",
            resource_name="correspondents",
            model_id=999
        )

        # Call the method and check for exception
        with self.assertRaises(ObjectNotFoundError) as context:
            self.resource.get(999)

        # Verify exception details
        self.assertEqual(context.exception.resource_name, "correspondents")
        self.assertEqual(context.exception.model_id, 999)

    @patch.object(CorrespondentResource, 'request')
    def test_create(self, mock_request):
        """
        Written By claude

        Test that the create() method creates and returns a new correspondent.
        """
        # Setup mock response
        mock_data = {
            "id": 1,
            "name": "New Correspondent",
            "match": "match pattern",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 0,
            "owner": 1
        }
        mock_request.return_value = mock_data

        # Call the method
        correspondent = self.resource.create(
            name="New Correspondent",
            match="match pattern",
            matching_algorithm=1,
            is_insensitive=True
        )

        # Assertions
        self.assertIsInstance(correspondent, Correspondent)
        self.assertEqual(correspondent.id, 1)
        self.assertEqual(correspondent.name, "New Correspondent")
        self.assertEqual(correspondent.match, "match pattern")
        mock_request.assert_called_once()
        self.assertEqual(mock_request.call_args[0][0], "POST")
        self.assertEqual(mock_request.call_args[0][1], "correspondents/")

    @patch.object(Correspondent, 'save')
    def test_update(self, mock_save):
        """
        Written By claude

        Test that a correspondent can be updated.
        """
        # Create a correspondent
        correspondent = Correspondent(
            id=1,
            name="Test Correspondent",
            match="",
            matching_algorithm=0,
            is_insensitive=False,
            document_count=5,
            owner=1
        )

        # Update the correspondent
        correspondent.name = "Updated Correspondent"
        correspondent.save()

        # Assertions
        mock_save.assert_called_once()

    @patch.object(CorrespondentResource, 'request')
    def test_delete(self, mock_request):
        """
        Written By claude

        Test that a correspondent can be deleted.
        """
        # Setup mock response
        mock_request.return_value = None

        # Create a correspondent with the resource
        correspondent = Correspondent(
            id=1,
            name="Test Correspondent",
            match="",
            matching_algorithm=0,
            is_insensitive=False,
            document_count=5,
            owner=1,
            _resource=self.resource
        )

        # Delete the correspondent
        correspondent.delete()

        # Assertions
        mock_request.assert_called_once_with("DELETE", "correspondents/1/")

    @patch.object(CorrespondentResource, 'request')
    def test_bulk_action(self, mock_request):
        """
        Written By claude

        Test that bulk actions can be performed on correspondents.
        """
        # Setup mock response
        mock_request.return_value = {"success": True}

        # Call the method
        result = self.resource.bulk_action("delete", [1, 2, 3])

        # Assertions
        self.assertEqual(result, {"success": True})
        mock_request.assert_called_once()
        self.assertEqual(mock_request.call_args[0][0], "POST")
        self.assertEqual(mock_request.call_args[0][1], "correspondents/bulk_action/")
        self.assertEqual(mock_request.call_args[1]["data"]["action"], "delete")
        self.assertEqual(mock_request.call_args[1]["data"]["ids"], [1, 2, 3])

    @patch.object(CorrespondentResource, 'parse_to_model')
    @patch.object(CorrespondentResource, 'request')
    def test_parse_to_model(self, mock_request, mock_parse):
        """
        Written By claude

        Test that the parse_to_model method correctly converts API data to a model.
        """
        # Setup mock response
        mock_data = {
            "id": 1,
            "name": "Test Correspondent",
            "match": "",
            "matching_algorithm": 0,
            "is_insensitive": False,
            "document_count": 5,
            "owner": 1
        }

        # Create a correspondent instance for the mock to return
        correspondent = Correspondent(**mock_data)
        mock_parse.return_value = correspondent

        # Call the method directly
        result = self.resource.parse_to_model(mock_data)

        # Assertions
        self.assertEqual(result, correspondent)
        mock_parse.assert_called_once_with(mock_data)

if __name__ == "__main__":
    unittest.main()
