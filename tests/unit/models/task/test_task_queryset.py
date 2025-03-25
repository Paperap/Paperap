

from __future__ import annotations

import unittest
from typing import Any, Dict, List, override
from unittest.mock import MagicMock, Mock, patch

from paperap.models.abstract.queryset import StandardQuerySet
from paperap.models.task.model import Task
from paperap.models.task.queryset import TaskQuerySet
from paperap.resources.tasks import TaskResource
from tests.lib import UnitTestCase


class TaskQuerySetTestCase(UnitTestCase):

    """Base test case for TaskQuerySet tests."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @override
    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        self.resource = MagicMock(spec=TaskResource)
        self.resource.model_class = Task
        self.queryset = TaskQuerySet(self.resource)

        # Mock the filter method to return self for chaining
        self.filter_patcher = patch.object(TaskQuerySet, 'filter', return_value=TaskQuerySet(self.resource))
        self.mock_filter = self.filter_patcher.start()

        # Mock the filter_field_by_str method to return self for chaining
        self.filter_field_patcher = patch.object(
            TaskQuerySet, 'filter_field_by_str', return_value=TaskQuerySet(self.resource)
        )
        self.mock_filter_field = self.filter_field_patcher.start()

    @override
    def tearDown(self) -> None:
        """Clean up after the test."""
        super().tearDown()
        self.filter_patcher.stop()
        self.filter_field_patcher.stop()


class TestTaskIdFilter(TaskQuerySetTestCase):

    """Test task_id filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_task_id(self):
        """Test filtering by task_id."""
        result = self.queryset.task_id(123)
        self.mock_filter.assert_called_once_with(task_id=123)
        self.assertIsInstance(result, TaskQuerySet)


class TestTaskFileNameFilter(TaskQuerySetTestCase):

    """Test task_file_name filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_task_file_name_default(self):
        """Test filtering by task_file_name with default parameters."""
        result = self.queryset.task_file_name("document.pdf")
        self.mock_filter_field.assert_called_once_with(
            "task_file_name", "document.pdf", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_task_file_name_contains(self):
        """Test filtering by task_file_name with contains."""
        result = self.queryset.task_file_name("document", exact=False)
        self.mock_filter_field.assert_called_once_with(
            "task_file_name", "document", exact=False, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_task_file_name_case_sensitive(self):
        """Test filtering by task_file_name with case sensitivity."""
        result = self.queryset.task_file_name("Document.pdf", case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "task_file_name", "Document.pdf", exact=True, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_task_file_name_contains_case_sensitive(self):
        """Test filtering by task_file_name with contains and case sensitivity."""
        result = self.queryset.task_file_name("Document", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "task_file_name", "Document", exact=False, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)


class TestDateDoneFilter(TaskQuerySetTestCase):

    """Test date_done filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_date_done_with_date(self):
        """Test filtering by date_done with a date string."""
        result = self.queryset.date_done("2025-03-13")
        self.mock_filter.assert_called_once_with(date_done="2025-03-13")
        self.assertIsInstance(result, TaskQuerySet)

    def test_date_done_with_none(self):
        """Test filtering by date_done with None."""
        result = self.queryset.date_done(None)
        self.mock_filter.assert_called_once_with(date_done=None)
        self.assertIsInstance(result, TaskQuerySet)


class TestTypeFilter(TaskQuerySetTestCase):

    """Test type filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_type_default(self):
        """Test filtering by type with default parameters."""
        result = self.queryset.type("consume")
        self.mock_filter_field.assert_called_once_with(
            "type", "consume", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_type_contains(self):
        """Test filtering by type with contains."""
        result = self.queryset.type("cons", exact=False)
        self.mock_filter_field.assert_called_once_with(
            "type", "cons", exact=False, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_type_case_sensitive(self):
        """Test filtering by type with case sensitivity."""
        result = self.queryset.type("Consume", case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "type", "Consume", exact=True, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_type_contains_case_sensitive(self):
        """Test filtering by type with contains and case sensitivity."""
        result = self.queryset.type("Cons", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "type", "Cons", exact=False, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)


class TestStatusFilter(TaskQuerySetTestCase):

    """Test status filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_status_default(self):
        """Test filtering by status with default parameters."""
        result = self.queryset.status("SUCCESS")
        self.mock_filter_field.assert_called_once_with(
            "status", "SUCCESS", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_status_contains(self):
        """Test filtering by status with contains."""
        result = self.queryset.status("SUCC", exact=False)
        self.mock_filter_field.assert_called_once_with(
            "status", "SUCC", exact=False, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_status_case_sensitive(self):
        """Test filtering by status with case sensitivity."""
        result = self.queryset.status("Success", case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "status", "Success", exact=True, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_status_contains_case_sensitive(self):
        """Test filtering by status with contains and case sensitivity."""
        result = self.queryset.status("Succ", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "status", "Succ", exact=False, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)


class TestResultFilter(TaskQuerySetTestCase):

    """Test result filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_result_with_string(self):
        """Test filtering by result with a string."""
        result = self.queryset.result("Document processed successfully")
        self.mock_filter_field.assert_called_once_with(
            "result", "Document processed successfully", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_result_with_none(self):
        """Test filtering by result with None."""
        result = self.queryset.result(None)
        self.mock_filter.assert_called_once_with(result__isnull=True)
        self.assertIsInstance(result, TaskQuerySet)

    def test_result_contains(self):
        """Test filtering by result with contains."""
        result = self.queryset.result("processed", exact=False)
        self.mock_filter_field.assert_called_once_with(
            "result", "processed", exact=False, case_insensitive=True
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_result_case_sensitive(self):
        """Test filtering by result with case sensitivity."""
        result = self.queryset.result("Document", case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "result", "Document", exact=True, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)

    def test_result_contains_case_sensitive(self):
        """Test filtering by result with contains and case sensitivity."""
        result = self.queryset.result("Document", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with(
            "result", "Document", exact=False, case_insensitive=False
        )
        self.assertIsInstance(result, TaskQuerySet)


class TestAcknowledgedFilter(TaskQuerySetTestCase):

    """Test acknowledged filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_acknowledged_true(self):
        """Test filtering by acknowledged=True."""
        result = self.queryset.acknowledged(True)
        self.mock_filter.assert_called_once_with(acknowledged=True)
        self.assertIsInstance(result, TaskQuerySet)

    def test_acknowledged_false(self):
        """Test filtering by acknowledged=False."""
        result = self.queryset.acknowledged(False)
        self.mock_filter.assert_called_once_with(acknowledged=False)
        self.assertIsInstance(result, TaskQuerySet)


class TestRelatedDocumentFilter(TaskQuerySetTestCase):

    """Test related_document filtering method."""

    def test_related_document_with_single_id(self):
        """Test filtering by related_document with a single ID."""
        result = self.queryset.related_document(123)
        self.mock_filter.assert_called_once_with(related_document=123)
        self.assertIsInstance(result, TaskQuerySet)

    def test_related_document_with_list(self):
        """Test filtering by related_document with a list of IDs."""
        result = self.queryset.related_document([123, 456, 789])
        self.mock_filter.assert_called_once_with(related_document__in=[123, 456, 789])
        self.assertIsInstance(result, TaskQuerySet)


class TestChaining(TaskQuerySetTestCase):

    """Test method chaining."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_method_chaining(self):
        """Test that methods can be chained."""
        # Reset the mocks to return the queryset for chaining
        self.mock_filter.return_value = self.queryset
        self.mock_filter_field.return_value = self.queryset

        # Chain multiple filter methods
        result = (
            self.queryset
            .task_id(123)
            .task_file_name("document.pdf")
            .type("consume")
            .status("SUCCESS")
            .acknowledged(True)
        )

        # Verify all methods were called
        self.assertEqual(self.mock_filter.call_count, 2)  # task_id and acknowledged
        self.assertEqual(self.mock_filter_field.call_count, 3)  # task_file_name, type, and status

        # Verify the result is the same queryset
        self.assertIs(result, self.queryset)


if __name__ == "__main__":
    unittest.main()
