"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    test_queryset.py
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

import unittest
from datetime import datetime
from typing import Any, Dict, List, Optional, override
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
from paperap.tests import UnitTestCase


class DocumentQuerySetTestCase(UnitTestCase):
    """Base test case for DocumentQuerySet tests."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    @override
    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        self.resource = MagicMock(spec=DocumentResource)
        self.resource.model_class = Document
        self.queryset = DocumentQuerySet(self.resource)
        
        # Mock the filter method to return self for chaining
        self.filter_patcher = patch.object(DocumentQuerySet, 'filter', return_value=DocumentQuerySet(self.resource))
        self.mock_filter = self.filter_patcher.start()
        
        # Mock the filter_field_by_str method to return self for chaining
        self.filter_field_patcher = patch.object(
            DocumentQuerySet, 'filter_field_by_str', return_value=DocumentQuerySet(self.resource)
        )
        self.mock_filter_field = self.filter_field_patcher.start()
    
    @override
    def tearDown(self) -> None:
        """Clean up after the test."""
        super().tearDown()
        self.filter_patcher.stop()
        self.filter_field_patcher.stop()


class TestTagFilters(DocumentQuerySetTestCase):
    """Test tag filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_tag_id_single(self):
        """Test filtering by a single tag ID."""
        result = self.queryset.tag_id(1)
        self.mock_filter.assert_called_once_with(tags__id=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_tag_id_list(self):
        """Test filtering by a list of tag IDs."""
        result = self.queryset.tag_id([1, 2, 3])
        self.mock_filter.assert_called_once_with(tags__id__in=[1, 2, 3])
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_tag_name_exact_case_insensitive(self):
        """Test filtering by tag name with exact match and case insensitive."""
        result = self.queryset.tag_name("Invoice")
        self.mock_filter_field.assert_called_once_with("tags__name", "Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_tag_name_contains_case_sensitive(self):
        """Test filtering by tag name with contains and case sensitive."""
        result = self.queryset.tag_name("Invoice", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with("tags__name", "Invoice", exact=False, case_insensitive=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestTitleFilter(DocumentQuerySetTestCase):
    """Test title filtering method."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_title_exact_case_insensitive(self):
        """Test filtering by title with exact match and case insensitive."""
        result = self.queryset.title("Invoice")
        self.mock_filter_field.assert_called_once_with("title", "Invoice", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_title_contains_case_sensitive(self):
        """Test filtering by title with contains and case sensitive."""
        result = self.queryset.title("Invoice", exact=False, case_insensitive=False)
        self.mock_filter_field.assert_called_once_with("title", "Invoice", exact=False, case_insensitive=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestCorrespondentFilters(DocumentQuerySetTestCase):
    """Test correspondent filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_correspondent_with_id(self):
        """Test filtering by correspondent ID."""
        with patch.object(DocumentQuerySet, 'correspondent_id', return_value=self.queryset) as mock_id:
            result = self.queryset.correspondent(1)
            mock_id.assert_called_once_with(1)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_name(self):
        """Test filtering by correspondent name."""
        with patch.object(DocumentQuerySet, 'correspondent_name', return_value=self.queryset) as mock_name:
            result = self.queryset.correspondent("John Doe")
            mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_invalid_type(self):
        """Test filtering by correspondent with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.queryset.correspondent(1.5)
    
    def test_correspondent_with_id_kwarg(self):
        """Test filtering by correspondent ID as keyword argument."""
        with patch.object(DocumentQuerySet, 'correspondent_id', return_value=self.queryset) as mock_id:
            result = self.queryset.correspondent(id=1)
            mock_id.assert_called_once_with(1)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_name_kwarg(self):
        """Test filtering by correspondent name as keyword argument."""
        with patch.object(DocumentQuerySet, 'correspondent_name', return_value=self.queryset) as mock_name:
            result = self.queryset.correspondent(name="John Doe")
            mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_slug_kwarg(self):
        """Test filtering by correspondent slug as keyword argument."""
        with patch.object(DocumentQuerySet, 'correspondent_slug', return_value=self.queryset) as mock_slug:
            result = self.queryset.correspondent(slug="john-doe")
            mock_slug.assert_called_once_with("john-doe", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_multiple_kwargs(self):
        """Test filtering by correspondent with multiple keyword arguments."""
        with patch.object(DocumentQuerySet, 'correspondent_id', return_value=self.queryset) as mock_id:
            with patch.object(DocumentQuerySet, 'correspondent_name', return_value=self.queryset) as mock_name:
                result = self.queryset.correspondent(id=1, name="John Doe")
                mock_id.assert_called_once_with(1)
                mock_name.assert_called_once_with("John Doe", exact=True, case_insensitive=True)
                self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_with_no_filters(self):
        """Test filtering by correspondent with no filters raises ValueError."""
        with self.assertRaises(ValueError):
            self.queryset.correspondent()
    
    def test_correspondent_id(self):
        """Test filtering by correspondent ID."""
        result = self.queryset.correspondent_id(1)
        self.mock_filter.assert_called_once_with(correspondent__id=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_name(self):
        """Test filtering by correspondent name."""
        result = self.queryset.correspondent_name("John Doe")
        self.mock_filter_field.assert_called_once_with(
            "correspondent__name", "John Doe", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_correspondent_slug(self):
        """Test filtering by correspondent slug."""
        result = self.queryset.correspondent_slug("john-doe")
        self.mock_filter_field.assert_called_once_with(
            "correspondent__slug", "john-doe", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestDocumentTypeFilters(DocumentQuerySetTestCase):
    """Test document type filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_document_type_with_id(self):
        """Test filtering by document type ID."""
        with patch.object(DocumentQuerySet, 'document_type_id', return_value=self.queryset) as mock_id:
            result = self.queryset.document_type(1)
            mock_id.assert_called_once_with(1)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_with_name(self):
        """Test filtering by document type name."""
        with patch.object(DocumentQuerySet, 'document_type_name', return_value=self.queryset) as mock_name:
            result = self.queryset.document_type("Invoice")
            mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_with_invalid_type(self):
        """Test filtering by document type with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.queryset.document_type(1.5)
    
    def test_document_type_with_id_kwarg(self):
        """Test filtering by document type ID as keyword argument."""
        with patch.object(DocumentQuerySet, 'document_type_id', return_value=self.queryset) as mock_id:
            result = self.queryset.document_type(id=1)
            mock_id.assert_called_once_with(1)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_with_name_kwarg(self):
        """Test filtering by document type name as keyword argument."""
        with patch.object(DocumentQuerySet, 'document_type_name', return_value=self.queryset) as mock_name:
            result = self.queryset.document_type(name="Invoice")
            mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_with_multiple_kwargs(self):
        """Test filtering by document type with multiple keyword arguments."""
        with patch.object(DocumentQuerySet, 'document_type_id', return_value=self.queryset) as mock_id:
            with patch.object(DocumentQuerySet, 'document_type_name', return_value=self.queryset) as mock_name:
                result = self.queryset.document_type(id=1, name="Invoice")
                mock_id.assert_called_once_with(1)
                mock_name.assert_called_once_with("Invoice", exact=True, case_insensitive=True)
                self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_with_no_filters(self):
        """Test filtering by document type with no filters raises ValueError."""
        with self.assertRaises(ValueError):
            self.queryset.document_type()
    
    def test_document_type_id(self):
        """Test filtering by document type ID."""
        result = self.queryset.document_type_id(1)
        self.mock_filter.assert_called_once_with(document_type__id=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_document_type_name(self):
        """Test filtering by document type name."""
        result = self.queryset.document_type_name("Invoice")
        self.mock_filter_field.assert_called_once_with(
            "document_type__name", "Invoice", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestStoragePathFilters(DocumentQuerySetTestCase):
    """Test storage path filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_storage_path_with_id(self):
        """Test filtering by storage path ID."""
        with patch.object(DocumentQuerySet, 'storage_path_id', return_value=self.queryset) as mock_id:
            result = self.queryset.storage_path(1)
            mock_id.assert_called_once_with(1)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_storage_path_with_name(self):
        """Test filtering by storage path name."""
        with patch.object(DocumentQuerySet, 'storage_path_name', return_value=self.queryset) as mock_name:
            result = self.queryset.storage_path("Invoices")
            mock_name.assert_called_once_with("Invoices", exact=True, case_insensitive=True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_storage_path_id(self):
        """Test filtering by storage path ID."""
        result = self.queryset.storage_path_id(1)
        self.mock_filter.assert_called_once_with(storage_path__id=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_storage_path_name(self):
        """Test filtering by storage path name."""
        result = self.queryset.storage_path_name("Invoices")
        self.mock_filter_field.assert_called_once_with(
            "storage_path__name", "Invoices", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)


class TestContentFilter(DocumentQuerySetTestCase):
    """Test content filtering method."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_content(self):
        """Test filtering by content."""
        result = self.queryset.content("invoice")
        self.mock_filter.assert_called_once_with(content__contains="invoice")
        self.assertIsInstance(result, DocumentQuerySet)


class TestDateFilters(DocumentQuerySetTestCase):
    """Test date filtering methods."""
    
    def test_added_after(self):
        """Test filtering by added after date."""
        result = self.queryset.added_after("2025-01-01")
        self.mock_filter.assert_called_once_with(added__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_added_before(self):
        """Test filtering by added before date."""
        result = self.queryset.added_before("2025-01-01")
        self.mock_filter.assert_called_once_with(added__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_before_with_datetime(self):
        """Test filtering by created before date with datetime object."""
        date = datetime(2025, 1, 1)
        result = self.queryset.created_before(date)
        self.mock_filter.assert_called_once_with(created__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_before_with_string(self):
        """Test filtering by created before date with string."""
        result = self.queryset.created_before("2025-01-01")
        self.mock_filter.assert_called_once_with(created__lt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_after_with_datetime(self):
        """Test filtering by created after date with datetime object."""
        date = datetime(2025, 1, 1)
        result = self.queryset.created_after(date)
        self.mock_filter.assert_called_once_with(created__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_after_with_string(self):
        """Test filtering by created after date with string."""
        result = self.queryset.created_after("2025-01-01")
        self.mock_filter.assert_called_once_with(created__gt="2025-01-01")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_between_with_datetime(self):
        """Test filtering by created between dates with datetime objects."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        result = self.queryset.created_between(start, end)
        self.mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_between_with_string(self):
        """Test filtering by created between dates with strings."""
        result = self.queryset.created_between("2025-01-01", "2025-12-31")
        self.mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_created_between_with_mixed(self):
        """Test filtering by created between dates with mixed types."""
        start = datetime(2025, 1, 1)
        result = self.queryset.created_between(start, "2025-12-31")
        self.mock_filter.assert_called_once_with(created__range=("2025-01-01", "2025-12-31"))
        self.assertIsInstance(result, DocumentQuerySet)


class TestMiscFilters(DocumentQuerySetTestCase):
    """Test miscellaneous filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_asn(self):
        """Test filtering by archive serial number."""
        result = self.queryset.asn("123456")
        self.mock_filter_field.assert_called_once_with("asn", "123456", exact=True, case_insensitive=True)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_original_file_name(self):
        """Test filtering by original file name."""
        result = self.queryset.original_file_name("invoice.pdf")
        self.mock_filter_field.assert_called_once_with(
            "original_file_name", "invoice.pdf", exact=True, case_insensitive=True
        )
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_user_can_change(self):
        """Test filtering by user change permission."""
        result = self.queryset.user_can_change(True)
        self.mock_filter.assert_called_once_with(user_can_change=True)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_notes(self):
        """Test filtering by notes."""
        result = self.queryset.notes("important")
        self.mock_filter.assert_called_once_with(notes__contains="important")
        self.assertIsInstance(result, DocumentQuerySet)


class TestCustomFieldFilters(DocumentQuerySetTestCase):
    """Test custom field filtering methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_custom_field_fullsearch_case_insensitive(self):
        """Test full search of custom fields with case insensitive."""
        result = self.queryset.custom_field_fullsearch("invoice")
        self.mock_filter.assert_called_once_with(custom_fields__icontains="invoice")
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_fullsearch_case_sensitive(self):
        """Test full search of custom fields with case sensitive raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.queryset.custom_field_fullsearch("invoice", case_insensitive=False)
    
    def test_custom_field_exact_case_insensitive(self):
        """Test filtering by custom field with exact match and case insensitive."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field("amount", 100, exact=True)
            mock_query.assert_called_once_with("amount", "iexact", 100)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_exact_case_sensitive(self):
        """Test filtering by custom field with exact match and case sensitive."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field("amount", 100, exact=True, case_insensitive=False)
            mock_query.assert_called_once_with("amount", "exact", 100)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_contains_case_insensitive(self):
        """Test filtering by custom field with contains and case insensitive."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field("amount", 100, exact=False)
            mock_query.assert_called_once_with("amount", "icontains", 100)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_contains_case_sensitive(self):
        """Test filtering by custom field with contains and case sensitive."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field("amount", 100, exact=False, case_insensitive=False)
            mock_query.assert_called_once_with("amount", "contains", 100)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_has_custom_field_id_single(self):
        """Test filtering by custom field ID."""
        result = self.queryset.has_custom_field_id(1)
        self.mock_filter.assert_called_once_with(custom_fields__id__in=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_has_custom_field_id_list(self):
        """Test filtering by list of custom field IDs."""
        result = self.queryset.has_custom_field_id([1, 2, 3])
        self.mock_filter.assert_called_once_with(custom_fields__id__in=[1, 2, 3])
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_has_custom_field_id_exact(self):
        """Test filtering by custom field ID with exact match."""
        result = self.queryset.has_custom_field_id(1, exact=True)
        self.mock_filter.assert_called_once_with(custom_fields__id__all=1)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_has_custom_fields(self):
        """Test filtering for documents with custom fields."""
        result = self.queryset.has_custom_fields()
        self.mock_filter.assert_called_once_with(has_custom_fields=True)
        self.assertIsInstance(result, DocumentQuerySet)
    
    def test_no_custom_fields(self):
        """Test filtering for documents without custom fields."""
        result = self.queryset.no_custom_fields()
        self.mock_filter.assert_called_once_with(has_custom_fields=False)
        self.assertIsInstance(result, DocumentQuerySet)


class TestCustomFieldQueryNormalization(DocumentQuerySetTestCase):
    """Test custom field query normalization methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_normalize_custom_field_query_item_string(self):
        """Test normalizing a string query item."""
        result = self.queryset._normalize_custom_field_query_item("test")
        self.assertEqual(result, '"test"')
    
    def test_normalize_custom_field_query_item_list(self):
        """Test normalizing a list query item."""
        result = self.queryset._normalize_custom_field_query_item([1, "test"])
        self.assertEqual(result, '[1, "test"]')
    
    def test_normalize_custom_field_query_item_bool(self):
        """Test normalizing a boolean query item."""
        result = self.queryset._normalize_custom_field_query_item(True)
        self.assertEqual(result, "true")
        result = self.queryset._normalize_custom_field_query_item(False)
        self.assertEqual(result, "false")
    
    def test_normalize_custom_field_query_item_number(self):
        """Test normalizing a number query item."""
        result = self.queryset._normalize_custom_field_query_item(100)
        self.assertEqual(result, "100")
    
    def test_normalize_custom_field_query_tuple(self):
        """Test normalizing a tuple query item that's not a CustomFieldQuery."""
        result = self.queryset._normalize_custom_field_query_item((1, 2))
        self.assertEqual(result, "[1, 2]")
    
    def test_normalize_custom_field_query(self):
        """Test normalizing a CustomFieldQuery."""
        query = CustomFieldQuery("amount", "exact", 100)
        result = self.queryset._normalize_custom_field_query(query)
        self.assertEqual(result, '["amount", "exact", 100]')
    
    def test_normalize_custom_field_query_tuple(self):
        """Test normalizing a tuple as a CustomFieldQuery."""
        result = self.queryset._normalize_custom_field_query(("amount", "exact", 100))
        self.assertEqual(result, '["amount", "exact", 100]')
    
    def test_normalize_custom_field_query_invalid(self):
        """Test normalizing an invalid query raises TypeError."""
        with self.assertRaises(TypeError):
            self.queryset._normalize_custom_field_query("not a query")


class TestCustomFieldQueryMethods(DocumentQuerySetTestCase):
    """Test custom field query methods."""
    # TODO: All methods in this class are AI Generated tests. Will remove this message when they are reviews.
    
    def test_custom_field_query_with_query_object(self):
        """Test custom_field_query with a CustomFieldQuery object."""
        query = CustomFieldQuery("amount", "exact", 100)
        with patch.object(DocumentQuerySet, '_normalize_custom_field_query', return_value='["amount", "exact", 100]'):
            result = self.queryset.custom_field_query(query)
            self.mock_filter.assert_called_once_with(custom_field_query='["amount", "exact", 100]')
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_query_with_args(self):
        """Test custom_field_query with field, operation, and value arguments."""
        with patch.object(DocumentQuerySet, '_normalize_custom_field_query', return_value='["amount", "exact", 100]'):
            result = self.queryset.custom_field_query("amount", "exact", 100)
            self.mock_filter.assert_called_once_with(custom_field_query='["amount", "exact", 100]')
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_query_invalid(self):
        """Test custom_field_query with invalid arguments raises TypeError."""
        with self.assertRaises(TypeError):
            self.queryset.custom_field_query(100)
    
    def test_custom_field_range(self):
        """Test filtering by custom field range."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_range("amount", "50", "150")
            mock_query.assert_called_once_with("amount", "range", ["50", "150"])
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_exact(self):
        """Test filtering by custom field exact match."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_exact("amount", 100)
            mock_query.assert_called_once_with("amount", "exact", 100)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_in(self):
        """Test filtering by custom field in a list of values."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_in("amount", [50, 100, 150])
            mock_query.assert_called_once_with("amount", "in", [50, 100, 150])
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_isnull(self):
        """Test filtering by custom field is null."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_isnull("amount")
            mock_query.assert_called_once_with("OR", ("amount", "isnull", True), ["amount", "exact", ""])
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_exists(self):
        """Test filtering by custom field exists."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_exists("amount")
            mock_query.assert_called_once_with("amount", "exists", True)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_exists_false(self):
        """Test filtering by custom field does not exist."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_exists("amount", False)
            mock_query.assert_called_once_with("amount", "exists", False)
            self.assertIsInstance(result, DocumentQuerySet)
    
    def test_custom_field_contains(self):
        """Test filtering by custom field contains all values."""
        with patch.object(DocumentQuerySet, 'custom_field_query', return_value=self.queryset) as mock_query:
            result = self.queryset.custom_field_contains("tags", ["invoice", "receipt"])
            mock_query.assert_called_once_with("tags", "contains", ["invoice", "receipt"])
            self.assertIsInstance(result, DocumentQuerySet)


if __name__ == "__main__":
    unittest.main()
