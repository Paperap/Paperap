

from __future__ import annotations

import unittest
from datetime import datetime
from typing import Any, Dict, List, override
from unittest.mock import MagicMock, Mock, patch

from paperap.exceptions import FilterDisabledError
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.models.correspondent import Correspondent
from paperap.models.document.model import Document
from paperap.models.document.queryset import CustomFieldQuery, DocumentQuerySet
from paperap.models.document_type import DocumentType
from paperap.models.storage_path import StoragePath
from paperap.models.tag import Tag
from paperap.resources.documents import DocumentResource
from tests.lib import UnitTestCase


class DocumentQuerySetTestCase(UnitTestCase):

    """Base test case for DocumentQuerySet tests."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def create_queryset(self):
        """Create a new queryset with a mocked resource."""
        resource = MagicMock(spec=DocumentResource)
        resource.model_class = Document
        return DocumentQuerySet(resource)


class TestTagFilters(DocumentQuerySetTestCase):

    """Test tag filtering methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_tag_id_single(self, mock_filter):
        """Test filtering by a single tag ID."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.tag_id(1)
        mock_filter.assert_called_once_with(tags__id=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_tag_id_list(self, mock_filter):
        """Test filtering by a list of tag IDs."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.tag_id([1, 2, 3])
        mock_filter.assert_called_once_with(tags__id__in=[1, 2, 3])
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_tag_name_exact_case_insensitive(self, mock_filter_field):
        """Test filtering by tag name with exact match and case insensitive."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.tag_name("Invoice")
        mock_filter_field.assert_called_once_with("tags__name", "Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_tag_name_contains_case_sensitive(self, mock_filter_field):
        """Test filtering by tag name with contains and case sensitive."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.tag_name("Invoice", exact=False, case_insensitive=False)
        mock_filter_field.assert_called_once_with("tags__name", "Invoice", exact=False, case_insensitive=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestTitleFilter(DocumentQuerySetTestCase):

    """Test title filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_title_exact_case_insensitive(self, mock_filter_field):
        """Test filtering by title with exact match and case insensitive."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.title("Invoice")
        mock_filter_field.assert_called_once_with("title", "Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_title_contains_case_sensitive(self, mock_filter_field):
        """Test filtering by title with contains and case sensitive."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.title("Invoice", exact=False, case_insensitive=False)
        mock_filter_field.assert_called_once_with("title", "Invoice", exact=False, case_insensitive=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestCorrespondentFilters(DocumentQuerySetTestCase):

    """Test correspondent filtering methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_id')
    def test_correspondent_with_id(self, mock_id):
        """Test filtering by correspondent ID."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.correspondent(1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_name')
    def test_correspondent_with_name(self, mock_name):
        """Test filtering by correspondent name."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.correspondent("John Doe")
        mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_correspondent_with_invalid_type(self):
        """Test filtering by correspondent with invalid type raises TypeError."""
        queryset = self.create_queryset()
        with self.assertRaises(TypeError):
            queryset.correspondent(1.5) # type: ignore

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_id')
    def test_correspondent_with_id_kwarg(self, mock_id):
        """Test filtering by correspondent ID as keyword argument."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.correspondent(id=1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_name')
    def test_correspondent_with_name_kwarg(self, mock_name):
        """Test filtering by correspondent name as keyword argument."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.correspondent(name="John Doe")
        mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_slug')
    def test_correspondent_with_slug_kwarg(self, mock_slug):
        """Test filtering by correspondent slug as keyword argument."""
        queryset = self.create_queryset()
        mock_slug.return_value = queryset

        result = queryset.correspondent(slug="john-doe")
        mock_slug.assert_called_once_with("john-doe", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_id')
    @patch('paperap.models.document.queryset.DocumentQuerySet.correspondent_name')
    def test_correspondent_with_multiple_kwargs(self, mock_name, mock_id):
        """Test filtering by correspondent with multiple keyword arguments."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset
        mock_name.return_value = queryset

        result = queryset.correspondent(id=1, name="John Doe")
        mock_id.assert_called_once_with(1)
        mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_correspondent_with_no_filters(self):
        """Test filtering by correspondent with no filters raises ValueError."""
        queryset = self.create_queryset()
        with self.assertRaises(ValueError):
            queryset.correspondent()

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_correspondent_id(self, mock_filter):
        """Test filtering by correspondent ID."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.correspondent_id(1)
        mock_filter.assert_called_once_with(correspondent__id=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_correspondent_name(self, mock_filter_field):
        """Test filtering by correspondent name."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.correspondent_name("John Doe")
        mock_filter_field.assert_called_once_with(
            "correspondent__name", "John Doe", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_correspondent_slug(self, mock_filter_field):
        """Test filtering by correspondent slug."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.correspondent_slug("john-doe")
        mock_filter_field.assert_called_once_with(
            "correspondent__slug", "john-doe", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestDocumentTypeFilters(DocumentQuerySetTestCase):

    """Test document type filtering methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_id')
    def test_document_type_with_id(self, mock_id):
        """Test filtering by document type ID."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.document_type(1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_name')
    def test_document_type_with_name(self, mock_name):
        """Test filtering by document type name."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.document_type("Invoice")
        mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_document_type_with_invalid_type(self):
        """Test filtering by document type with invalid type raises TypeError."""
        queryset = self.create_queryset()
        with self.assertRaises(TypeError):
            queryset.document_type(1.5) # type: ignore

    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_id')
    def test_document_type_with_id_kwarg(self, mock_id):
        """Test filtering by document type ID as keyword argument."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.document_type(id=1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_name')
    def test_document_type_with_name_kwarg(self, mock_name):
        """Test filtering by document type name as keyword argument."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.document_type(name="Invoice")
        mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_id')
    @patch('paperap.models.document.queryset.DocumentQuerySet.document_type_name')
    def test_document_type_with_multiple_kwargs(self, mock_name, mock_id):
        """Test filtering by document type with multiple keyword arguments."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset
        mock_name.return_value = queryset

        result = queryset.document_type(id=1, name="Invoice")
        mock_id.assert_called_once_with(1)
        mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_document_type_with_no_filters(self):
        """Test filtering by document type with no filters raises ValueError."""
        queryset = self.create_queryset()
        with self.assertRaises(ValueError):
            queryset.document_type()

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_document_type_id(self, mock_filter):
        """Test filtering by document type ID."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.document_type_id(1)
        mock_filter.assert_called_once_with(document_type__id=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_document_type_name(self, mock_filter_field):
        """Test filtering by document type name."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.document_type_name("Invoice")
        mock_filter_field.assert_called_once_with(
            "document_type__name", "Invoice", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestStoragePathFilters(DocumentQuerySetTestCase):

    """Test storage path filtering methods."""

    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_id')
    def test_storage_path_with_id(self, mock_id):
        """Test filtering by storage path ID."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.storage_path(1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_name')
    def test_storage_path_with_name(self, mock_name):
        """Test filtering by storage path name."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.storage_path("Invoices")
        mock_name.assert_called_once_with("Invoices", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_storage_path_with_invalid_type(self):
        """Test filtering by storage path with invalid type raises TypeError."""
        queryset = self.create_queryset()
        with self.assertRaises(TypeError):
            queryset.storage_path(1.5) # type: ignore

    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_id')
    def test_storage_path_with_id_kwarg(self, mock_id):
        """Test filtering by storage path ID as keyword argument."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset

        result = queryset.storage_path(id=1)
        mock_id.assert_called_once_with(1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_name')
    def test_storage_path_with_name_kwarg(self, mock_name):
        """Test filtering by storage path name as keyword argument."""
        queryset = self.create_queryset()
        mock_name.return_value = queryset

        result = queryset.storage_path(name="Invoices")
        mock_name.assert_called_once_with("Invoices", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_id')
    @patch('paperap.models.document.queryset.DocumentQuerySet.storage_path_name')
    def test_storage_path_with_multiple_kwargs(self, mock_name, mock_id):
        """Test filtering by storage path with multiple keyword arguments."""
        queryset = self.create_queryset()
        mock_id.return_value = queryset
        mock_name.return_value = queryset

        result = queryset.storage_path(id=1, name="Invoices")
        mock_id.assert_called_once_with(1)
        mock_name.assert_called_once_with("Invoices", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    def test_storage_path_with_no_filters(self):
        """Test filtering by storage path with no filters raises ValueError."""
        queryset = self.create_queryset()
        with self.assertRaises(ValueError):
            queryset.storage_path()

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_storage_path_id(self, mock_filter):
        """Test filtering by storage path ID."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.storage_path_id(1)
        mock_filter.assert_called_once_with(storage_path__id=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_storage_path_name(self, mock_filter_field):
        """Test filtering by storage path name."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.storage_path_name("Invoices")
        mock_filter_field.assert_called_once_with(
            "storage_path__name", "Invoices", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestContentFilter(DocumentQuerySetTestCase):

    """Test content filtering method."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_content(self, mock_filter):
        """Test filtering by content."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.content("invoice")
        mock_filter.assert_called_once_with(content__contains="invoice")
        self.assertIsInstance(result, DocumentQuerySet)


class TestDateFilters(DocumentQuerySetTestCase):

    """Test date filtering methods."""

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_added_after(self, mock_filter):
        """Test filtering by added after date."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.added_after("2025-01-01")
        mock_filter.assert_called_once_with(added__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_added_before(self, mock_filter):
        """Test filtering by added before date."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.added_before("2025-01-01")
        mock_filter.assert_called_once_with(added__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_before_with_datetime(self, mock_filter):
        """Test filtering by created before date with datetime object."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        date = datetime(2025, 1, 1)
        result = queryset.created_before(date)
        mock_filter.assert_called_once_with(created__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_before_with_string(self, mock_filter):
        """Test filtering by created before date with string."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.created_before("2025-01-01")
        mock_filter.assert_called_once_with(created__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_after_with_datetime(self, mock_filter):
        """Test filtering by created after date with datetime object."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        date = datetime(2025, 1, 1)
        result = queryset.created_after(date)
        mock_filter.assert_called_once_with(created__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_after_with_string(self, mock_filter):
        """Test filtering by created after date with string."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.created_after("2025-01-01")
        mock_filter.assert_called_once_with(created__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_between_with_datetime(self, mock_filter):
        """Test filtering by created between dates with datetime objects."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        result = queryset.created_between(start, end)
        mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_between_with_string(self, mock_filter):
        """Test filtering by created between dates with strings."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.created_between("2025-01-01", "2025-12-31")
        mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_created_between_with_mixed(self, mock_filter):
        """Test filtering by created between dates with mixed types."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        start = datetime(2025, 1, 1)
        result = queryset.created_between(start, "2025-12-31")
        mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)

class TestMiscFilters(DocumentQuerySetTestCase):

    """Test miscellaneous filtering methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_asn(self, mock_filter_field):
        """Test filtering by archive serial number."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.asn("123456")
        mock_filter_field.assert_called_once_with("asn", "123456", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter_field_by_str')
    def test_original_filename(self, mock_filter_field):
        """Test filtering by original file name."""
        queryset = self.create_queryset()
        mock_filter_field.return_value = queryset

        result = queryset.original_filename("invoice.pdf")
        mock_filter_field.assert_called_once_with(
            "original_filename", "invoice.pdf", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_user_can_change(self, mock_filter):
        """Test filtering by user change permission."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.user_can_change(True)
        mock_filter.assert_called_once_with(user_can_change=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_notes(self, mock_filter):
        """Test filtering by notes."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.notes("important")
        mock_filter.assert_called_once_with(notes__contains="important")
        self.assertIsInstance(result, DocumentQuerySet)


class TestCustomFieldFilters(DocumentQuerySetTestCase):

    """Test custom field filtering methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_custom_field_fullsearch_case_insensitive(self, mock_filter):
        """Test full search of custom fields with case insensitive."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.custom_field_fullsearch("invoice")
        mock_filter.assert_called_once_with(custom_fields__icontains="invoice")
        self.assertIsInstance(result, DocumentQuerySet)

    def test_custom_field_fullsearch_case_sensitive(self):
        """Test full search of custom fields with case sensitive raises NotImplementedError."""
        queryset = self.create_queryset()
        with self.assertRaises(NotImplementedError):
            queryset.custom_field_fullsearch("invoice", case_insensitive=False)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_exact_case_insensitive(self, mock_query):
        """Test filtering by custom field with exact match and case insensitive."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field("amount", 100, exact=True)
        mock_query.assert_called_once_with("amount", "iexact", 100)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_exact_case_sensitive(self, mock_query):
        """Test filtering by custom field with exact match and case sensitive."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field("amount", 100, exact=True, case_insensitive=False)
        mock_query.assert_called_once_with("amount", "exact", 100)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_contains_case_insensitive(self, mock_query):
        """Test filtering by custom field with contains and case insensitive."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field("amount", 100, exact=False)
        mock_query.assert_called_once_with("amount", "icontains", 100)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_contains_case_sensitive(self, mock_query):
        """Test filtering by custom field with contains and case sensitive."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field("amount", 100, exact=False, case_insensitive=False)
        mock_query.assert_called_once_with("amount", "contains", 100)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_has_custom_field_id_single(self, mock_filter):
        """Test filtering by custom field ID."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.has_custom_field_id(1)
        mock_filter.assert_called_once_with(custom_fields__id__in=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_has_custom_field_id_list(self, mock_filter):
        """Test filtering by list of custom field IDs."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.has_custom_field_id([1, 2, 3])
        mock_filter.assert_called_once_with(custom_fields__id__in=[1, 2, 3])
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_has_custom_field_id_exact(self, mock_filter):
        """Test filtering by custom field ID with exact match."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.has_custom_field_id(1, exact=True)
        mock_filter.assert_called_once_with(custom_fields__id__all=1)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_has_custom_fields(self, mock_filter):
        """Test filtering for documents with custom fields."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.has_custom_fields()
        mock_filter.assert_called_once_with(has_custom_fields=True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_no_custom_fields(self, mock_filter):
        """Test filtering for documents without custom fields."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset

        result = queryset.no_custom_fields()
        mock_filter.assert_called_once_with(has_custom_fields=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestCustomFieldQueryNormalization(DocumentQuerySetTestCase):

    """Test custom field query normalization methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    def test_normalize_custom_field_query_item_string(self):
        """Test normalizing a string query item."""
        queryset = self.create_queryset()
        result = queryset._normalize_custom_field_query_item("test") # type: ignore
        self.assertEqual(result, '"test"')

    def test_normalize_custom_field_query_item_list(self):
        """Test normalizing a list query item."""
        queryset = self.create_queryset()
        result = queryset._normalize_custom_field_query_item([1, "test"]) # type: ignore
        self.assertEqual(result, '[1, "test"]')

    def test_normalize_custom_field_query_item_bool(self):
        """Test normalizing a boolean query item."""
        queryset = self.create_queryset()
        result = queryset._normalize_custom_field_query_item(True) # type: ignore
        self.assertEqual(result, "true")
        result = queryset._normalize_custom_field_query_item(False) # type: ignore
        self.assertEqual(result, "false")

    def test_normalize_custom_field_query_item_number(self):
        """Test normalizing a number query item."""
        queryset = self.create_queryset()
        result = queryset._normalize_custom_field_query_item(100) # type: ignore
        self.assertEqual(result, "100")

    def test_normalize_custom_field_query(self):
        """Test normalizing a CustomFieldQuery."""
        queryset = self.create_queryset()
        query = CustomFieldQuery("amount", "exact", 100)
        result = queryset._normalize_custom_field_query(query) # type: ignore
        self.assertEqual(result, '["amount", "exact", 100]')

    def test_normalize_custom_field_query_tuple(self):
        """Test normalizing a tuple as a CustomFieldQuery."""
        queryset = self.create_queryset()
        result = queryset._normalize_custom_field_query(("amount", "exact", 100)) # type: ignore
        self.assertEqual(result, '["amount", "exact", 100]')

    def test_normalize_custom_field_query_invalid(self):
        """Test normalizing an invalid query raises TypeError."""
        queryset = self.create_queryset()
        with self.assertRaises(TypeError):
            queryset._normalize_custom_field_query("not a query") # type: ignore


class TestCustomFieldQueryMethods(DocumentQuerySetTestCase):

    """Test custom field query methods."""

    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.

    @patch('paperap.models.document.queryset.DocumentQuerySet._normalize_custom_field_query')
    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_custom_field_query_with_query_object(self, mock_filter, mock_normalize):
        """Test custom_field_query with a CustomFieldQuery object."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset
        mock_normalize.return_value = '["amount", "exact", 100]'

        query = CustomFieldQuery("amount", "exact", 100)
        result = queryset.custom_field_query(query)
        mock_normalize.assert_called_once_with(query)
        mock_filter.assert_called_once_with(custom_field_query='["amount", "exact", 100]')
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet._normalize_custom_field_query')
    @patch('paperap.models.document.queryset.DocumentQuerySet.filter')
    def test_custom_field_query_with_args(self, mock_filter, mock_normalize):
        """Test custom_field_query with field, operation, and value arguments."""
        queryset = self.create_queryset()
        mock_filter.return_value = queryset
        mock_normalize.return_value = '["amount", "exact", 100]'

        result = queryset.custom_field_query("amount", "exact", 100)
        mock_filter.assert_called_once_with(custom_field_query='["amount", "exact", 100]')
        self.assertIsInstance(result, DocumentQuerySet)

    def test_custom_field_query_invalid(self):
        """Test custom_field_query with invalid arguments raises TypeError."""
        queryset = self.create_queryset()
        with self.assertRaises(TypeError):
            queryset.custom_field_query(100) # type: ignore

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_range(self, mock_query):
        """Test filtering by custom field range."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_range("amount", "50", "150")
        mock_query.assert_called_once_with("amount", "range", ["50", "150"])
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_exact(self, mock_query):
        """Test filtering by custom field exact match."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_exact("amount", 100)
        mock_query.assert_called_once_with("amount", "exact", 100)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_in(self, mock_query):
        """Test filtering by custom field in a list of values."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_in("amount", [50, 100, 150])
        mock_query.assert_called_once_with("amount", "in", [50, 100, 150])
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_isnull(self, mock_query):
        """Test filtering by custom field is null."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_isnull("amount")
        mock_query.assert_called_once_with("OR", ("amount", "isnull", True), ["amount", "exact", ""])
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_exists(self, mock_query):
        """Test filtering by custom field exists."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_exists("amount")
        mock_query.assert_called_once_with("amount", "exists", True)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_exists_false(self, mock_query):
        """Test filtering by custom field does not exist."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_exists("amount", False)
        mock_query.assert_called_once_with("amount", "exists", False)
        self.assertIsInstance(result, DocumentQuerySet)

    @patch('paperap.models.document.queryset.DocumentQuerySet.custom_field_query')
    def test_custom_field_contains(self, mock_query):
        """Test filtering by custom field contains all values."""
        queryset = self.create_queryset()
        mock_query.return_value = queryset

        result = queryset.custom_field_contains("tags", ["invoice", "receipt"])
        mock_query.assert_called_once_with("tags", "contains", ["invoice", "receipt"])
        self.assertIsInstance(result, DocumentQuerySet)


if __name__ == "__main__":
    unittest.main()
