"""
Document QuerySet module for Paperless-ngx API interactions.

This module provides specialized QuerySet classes for Document and DocumentNote models,
with methods for filtering, searching, and performing bulk operations on documents.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, NamedTuple, Self, Union, overload, override

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner
from paperap.const import ClientResponse, EnrichmentConfig

if TYPE_CHECKING:
    from paperap.models import Correspondent, Document, DocumentNote, DocumentType, StoragePath
    from paperap.resources.documents import DocumentResource
    from paperap.services.enrichment import DocumentEnrichmentService

logger = logging.getLogger(__name__)

_OperationType = Union[str, "_QueryParam"]
_QueryParam = Union["CustomFieldQuery", tuple[str, _OperationType, Any]]


class CustomFieldQuery(NamedTuple):
    """
    A named tuple representing a custom field query.

    Used to construct complex queries for document custom fields.

    Attributes:
        field: The name of the custom field to query.
        operation: The operation to perform (e.g., "exact", "contains", "range").
        value: The value to compare against.

    """

    field: str
    operation: _OperationType
    value: Any


class DocumentNoteQuerySet(StandardQuerySet["DocumentNote"]):
    """
    QuerySet for document notes.

    Provides standard querying capabilities for DocumentNote objects.
    Inherits all functionality from StandardQuerySet without additional specialization.
    """

    pass


class DocumentQuerySet(StandardQuerySet["Document"], HasOwner):
    """
    QuerySet for Paperless-ngx documents with specialized filtering methods.

    This class extends StandardQuerySet to provide document-specific filtering,
    searching, and bulk operations. It includes methods for filtering by document
    metadata, content, custom fields, and more, as well as bulk operations like
    merging, rotating, and updating document properties.

    Examples:
        >>> # Search for documents
        >>> docs = client.documents().search("invoice")
        >>> for doc in docs:
        ...     print(doc.title)

        >>> # Find documents similar to a specific document
        >>> similar_docs = client.documents().more_like(42)
        >>> for doc in similar_docs:
        ...     print(doc.title)

        >>> # Filter by correspondent and document type
        >>> filtered_docs = client.documents().correspondent(5).document_type("Invoice")
        >>> for doc in filtered_docs:
        ...     print(f"{doc.title} - {doc.created}")

    """

    resource: "DocumentResource"  # type: ignore # because nested generics are not allowed
    _enrichment_service: "DocumentEnrichmentService"

    @property
    def enrichment_service(self) -> "DocumentEnrichmentService":
        if not self._enrichment_service:
            # Avoid circular ref. # TODO
            from paperap.services.enrichment import DocumentEnrichmentService  # type: ignore

            self._enrichment_service = DocumentEnrichmentService()
        return self._enrichment_service

    def tag_id(self, tag_id: int | list[int]) -> Self:
        """
        Filter documents that have the specified tag ID(s).

        Args:
            tag_id: A single tag ID or list of tag IDs.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Filter by a single tag ID
            >>> docs = client.documents().tag_id(5)
            >>>
            >>> # Filter by multiple tag IDs
            >>> docs = client.documents().tag_id([5, 7, 9])

        """
        if isinstance(tag_id, list):
            return self.filter(tags__id__in=tag_id)
        return self.filter(tags__id=tag_id)

    def tag_name(self, tag_name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents that have a tag with the specified name.

        Args:
            tag_name: The name of the tag to filter by.
            exact: If True, match the exact tag name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().tag_name("Tax")
            >>>
            >>> # Contains match
            >>> docs = client.documents().tag_name("invoice", exact=False)
            >>>
            >>> # Case-sensitive match
            >>> docs = client.documents().tag_name("Receipt", case_insensitive=False)

        """
        return self.filter_field_by_str("tags__name", tag_name, exact=exact, case_insensitive=case_insensitive)

    def title(self, title: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by title.

        Args:
            title: The document title to filter by.
            exact: If True, match the exact title, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().title("Electric Bill March 2023")
            >>>
            >>> # Contains match
            >>> docs = client.documents().title("invoice", exact=False)

        """
        return self.filter_field_by_str("title", title, exact=exact, case_insensitive=case_insensitive)

    def search(self, query: str) -> "DocumentQuerySet":
        """
        Search for documents using a query string.

        This method uses the Paperless-ngx full-text search functionality to find
        documents matching the query string in their content or metadata.

        Args:
            query: The search query string.

        Returns:
            A queryset with the search results.

        Examples:
            >>> # Search for documents containing "invoice"
            >>> docs = client.documents().search("invoice")
            >>> for doc in docs:
            ...     print(doc.title)
            >>>
            >>> # Search with multiple terms
            >>> docs = client.documents().search("electric bill 2023")

        """
        return self.filter(query=query)

    def more_like(self, document_id: int) -> "DocumentQuerySet":
        """
        Find documents similar to the specified document.

        Uses Paperless-ngx's similarity algorithm to find documents with content
        or metadata similar to the specified document.

        Args:
            document_id: The ID of the document to find similar documents for.

        Returns:
            A queryset with similar documents.

        Examples:
            >>> # Find documents similar to document with ID 42
            >>> similar_docs = client.documents().more_like(42)
            >>> for doc in similar_docs:
            ...     print(doc.title)
            >>>
            >>> # Chain with other filters
            >>> recent_similar = client.documents().more_like(42).created_after("2023-01-01")

        """
        return self.filter(more_like_id=document_id)

    def correspondent(
        self,
        value: int | str | None = None,
        *,
        exact: bool = True,
        case_insensitive: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Filter documents by correspondent.

        This method provides a flexible interface for filtering documents by correspondent,
        supporting filtering by ID, name, or slug, with options for exact or partial matching.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The correspondent ID or name to filter by.
            exact: If True, match the exact value, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching for string values.
            **kwargs: Additional filters (slug, id, name).

        Returns:
            Filtered DocumentQuerySet.

        Raises:
            ValueError: If no valid filters are provided.
            TypeError: If value is not an int or str.

        Examples:
            >>> # Filter by ID
            >>> client.documents().correspondent(1)
            >>> client.documents().correspondent(id=1)
            >>>
            >>> # Filter by name
            >>> client.documents().correspondent("John Doe")
            >>> client.documents().correspondent(name="John Doe")
            >>>
            >>> # Filter by name (partial match)
            >>> client.documents().correspondent("John", exact=False)
            >>>
            >>> # Filter by slug
            >>> client.documents().correspondent(slug="john-doe")
            >>>
            >>> # Filter by ID and name
            >>> client.documents().correspondent(1, name="John Doe")

        """
        # Track if any filters were applied
        filters_applied = False
        result = self

        if value is not None:
            if isinstance(value, int):
                result = self.correspondent_id(value)
                filters_applied = True
            elif isinstance(value, str):
                result = self.correspondent_name(value, exact=exact, case_insensitive=case_insensitive)
                filters_applied = True
            else:
                raise TypeError("Invalid value type for correspondent filter")

        if (slug := kwargs.get("slug")) is not None:
            result = result.correspondent_slug(slug, exact=exact, case_insensitive=case_insensitive)
            filters_applied = True
        if (pk := kwargs.get("id")) is not None:
            result = result.correspondent_id(pk)
            filters_applied = True
        if (name := kwargs.get("name")) is not None:
            result = result.correspondent_name(name, exact=exact, case_insensitive=case_insensitive)
            filters_applied = True

        # If no filters have been applied, raise an error
        if not filters_applied:
            raise ValueError("No valid filters provided for correspondent")

        return result

    def correspondent_id(self, correspondent_id: int) -> Self:
        """
        Filter documents by correspondent ID.

        Args:
            correspondent_id: The correspondent ID to filter by.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Filter documents with correspondent ID 5
            >>> docs = client.documents().correspondent_id(5)

        """
        return self.filter(correspondent__id=correspondent_id)

    def correspondent_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by correspondent name.

        Args:
            name: The correspondent name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().correspondent_name("Electric Company")
            >>>
            >>> # Contains match
            >>> docs = client.documents().correspondent_name("Electric", exact=False)

        """
        return self.filter_field_by_str("correspondent__name", name, exact=exact, case_insensitive=case_insensitive)

    def correspondent_slug(self, slug: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by correspondent slug.

        Args:
            slug: The correspondent slug to filter by.
            exact: If True, match the exact slug, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().correspondent_slug("electric-company")
            >>>
            >>> # Contains match
            >>> docs = client.documents().correspondent_slug("electric", exact=False)

        """
        return self.filter_field_by_str("correspondent__slug", slug, exact=exact, case_insensitive=case_insensitive)

    def document_type(
        self,
        value: int | str | None = None,
        *,
        exact: bool = True,
        case_insensitive: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Filter documents by document type.

        This method provides a flexible interface for filtering documents by document type,
        supporting filtering by ID or name, with options for exact or partial matching.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The document type ID or name to filter by.
            exact: If True, match the exact value, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching for string values.
            **kwargs: Additional filters (id, name).

        Returns:
            Filtered DocumentQuerySet.

        Raises:
            ValueError: If no valid filters are provided.
            TypeError: If value is not an int or str.

        Examples:
            >>> # Filter by ID
            >>> client.documents().document_type(1)
            >>> client.documents().document_type(id=1)
            >>>
            >>> # Filter by name
            >>> client.documents().document_type("Invoice")
            >>> client.documents().document_type(name="Invoice")
            >>>
            >>> # Filter by name (partial match)
            >>> client.documents().document_type("Inv", exact=False)
            >>>
            >>> # Filter by ID and name
            >>> client.documents().document_type(1, name="Invoice")

        """
        # Track if any filters were applied
        filters_applied = False
        result = self

        if value is not None:
            if isinstance(value, int):
                result = self.document_type_id(value)
                filters_applied = True
            elif isinstance(value, str):
                result = self.document_type_name(value, exact=exact, case_insensitive=case_insensitive)
                filters_applied = True
            else:
                raise TypeError("Invalid value type for document type filter")

        if (pk := kwargs.get("id")) is not None:
            result = result.document_type_id(pk)
            filters_applied = True
        if (name := kwargs.get("name")) is not None:
            result = result.document_type_name(name, exact=exact, case_insensitive=case_insensitive)
            filters_applied = True

        # If no filters have been applied, raise an error
        if not filters_applied:
            raise ValueError("No valid filters provided for document type")

        return result

    def document_type_id(self, document_type_id: int) -> Self:
        """
        Filter documents by document type ID.

        Args:
            document_type_id: The document type ID to filter by.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Filter documents with document type ID 3
            >>> docs = client.documents().document_type_id(3)

        """
        return self.filter(document_type__id=document_type_id)

    def document_type_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by document type name.

        Args:
            name: The document type name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().document_type_name("Invoice")
            >>>
            >>> # Contains match
            >>> docs = client.documents().document_type_name("bill", exact=False)

        """
        return self.filter_field_by_str("document_type__name", name, exact=exact, case_insensitive=case_insensitive)

    def storage_path(
        self,
        value: int | str | None = None,
        *,
        exact: bool = True,
        case_insensitive: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Filter documents by storage path.

        This method provides a flexible interface for filtering documents by storage path,
        supporting filtering by ID or name, with options for exact or partial matching.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The storage path ID or name to filter by.
            exact: If True, match the exact value, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching for string values.
            **kwargs: Additional filters (id, name).

        Returns:
            Filtered DocumentQuerySet.

        Raises:
            ValueError: If no valid filters are provided.
            TypeError: If value is not an int or str.

        Examples:
            >>> # Filter by ID
            >>> client.documents().storage_path(1)
            >>> client.documents().storage_path(id=1)
            >>>
            >>> # Filter by name
            >>> client.documents().storage_path("Invoices")
            >>> client.documents().storage_path(name="Invoices")
            >>>
            >>> # Filter by name (partial match)
            >>> client.documents().storage_path("Tax", exact=False)
            >>>
            >>> # Filter by ID and name
            >>> client.documents().storage_path(1, name="Invoices")

        """
        # Track if any filters were applied
        filters_applied = False
        result = self

        if value is not None:
            if isinstance(value, int):
                result = self.storage_path_id(value)
                filters_applied = True
            elif isinstance(value, str):
                result = self.storage_path_name(value, exact=exact, case_insensitive=case_insensitive)
                filters_applied = True
            else:
                raise TypeError("Invalid value type for storage path filter")

        if (pk := kwargs.get("id")) is not None:
            result = result.storage_path_id(pk)
            filters_applied = True
        if (name := kwargs.get("name")) is not None:
            result = result.storage_path_name(name, exact=exact, case_insensitive=case_insensitive)
            filters_applied = True

        # If no filters have been applied, raise an error
        if not filters_applied:
            raise ValueError("No valid filters provided for storage path")

        return result

    def storage_path_id(self, storage_path_id: int) -> Self:
        """
        Filter documents by storage path ID.

        Args:
            storage_path_id: The storage path ID to filter by.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Filter documents with storage path ID 2
            >>> docs = client.documents().storage_path_id(2)

        """
        return self.filter(storage_path__id=storage_path_id)

    def storage_path_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by storage path name.

        Args:
            name: The storage path name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().storage_path_name("Tax Documents")
            >>>
            >>> # Contains match
            >>> docs = client.documents().storage_path_name("Tax", exact=False)

        """
        return self.filter_field_by_str("storage_path__name", name, exact=exact, case_insensitive=case_insensitive)

    def content(self, text: str) -> Self:
        """
        Filter documents whose content contains the specified text.

        This method searches the OCR-extracted text content of documents.

        Args:
            text: The text to search for in document content.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents containing "invoice amount"
            >>> docs = client.documents().content("invoice amount")
            >>>
            >>> # Chain with other filters
            >>> recent_with_text = client.documents().content("tax").created_after("2023-01-01")

        """
        return self.filter(content__contains=text)

    def added_after(self, date_str: str) -> Self:
        """
        Filter documents added after the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD).

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents added after January 1, 2023
            >>> docs = client.documents().added_after("2023-01-01")

        """
        return self.filter(added__gt=date_str)

    def added_before(self, date_str: str) -> Self:
        """
        Filter documents added before the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD).

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents added before December 31, 2022
            >>> docs = client.documents().added_before("2022-12-31")

        """
        return self.filter(added__lt=date_str)

    def asn(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by archive serial number (ASN).

        The archive serial number is a unique identifier assigned to documents
        in Paperless-ngx, often used for referencing physical documents.

        Args:
            value: The archive serial number to filter by.
            exact: If True, match the exact value, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().asn("2023-0042")
            >>>
            >>> # Contains match
            >>> docs = client.documents().asn("2023", exact=False)

        """
        return self.filter_field_by_str("asn", value, exact=exact, case_insensitive=case_insensitive)

    def original_filename(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by original file name.

        This filters based on the original filename of the document when it was uploaded.

        Args:
            name: The original file name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match (default)
            >>> docs = client.documents().original_filename("scan_001.pdf")
            >>>
            >>> # Contains match
            >>> docs = client.documents().original_filename("invoice", exact=False)

        """
        return self.filter_field_by_str("original_filename", name, exact=exact, case_insensitive=case_insensitive)

    def user_can_change(self, value: bool) -> Self:
        """
        Filter documents by user change permission.

        This filter is useful for finding documents that the current authenticated
        user has permission to modify.

        Args:
            value: True to filter documents the user can change, False for those they cannot.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents the current user can change
            >>> docs = client.documents().user_can_change(True)
            >>>
            >>> # Find documents the current user cannot change
            >>> docs = client.documents().user_can_change(False)

        """
        return self.filter(user_can_change=value)

    def custom_field_fullsearch(self, value: str, *, case_insensitive: bool = True) -> Self:
        """
        Filter documents by searching through both custom field name and value.

        This method searches across all custom fields (both names and values)
        for the specified text.

        Args:
            value: The search string to look for in custom fields.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Filtered DocumentQuerySet.

        Raises:
            NotImplementedError: If case_insensitive is False, as Paperless NGX
                                 doesn't support case-sensitive custom field search.

        Examples:
            >>> # Find documents with custom fields containing "reference"
            >>> docs = client.documents().custom_field_fullsearch("reference")

        """
        if case_insensitive:
            return self.filter(custom_fields__icontains=value)
        raise NotImplementedError("Case-sensitive custom field search is not supported by Paperless NGX")

    def custom_field(self, field: str, value: Any, *, exact: bool = False, case_insensitive: bool = True) -> Self:
        """
        Filter documents by custom field.

        This method filters documents based on a specific custom field's value.

        Args:
            field: The name of the custom field to filter by.
            value: The value to filter by.
            exact: If True, match the exact value, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching for string values.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Contains match (default)
            >>> docs = client.documents().custom_field("Reference Number", "INV")
            >>>
            >>> # Exact match
            >>> docs = client.documents().custom_field("Status", "Paid", exact=True)
            >>>
            >>> # Case-sensitive contains match
            >>> docs = client.documents().custom_field("Notes", "Important",
            ...                                      case_insensitive=False)

        """
        if exact:
            if case_insensitive:
                return self.custom_field_query(field, "iexact", value)
            return self.custom_field_query(field, "exact", value)
        if case_insensitive:
            return self.custom_field_query(field, "icontains", value)
        return self.custom_field_query(field, "contains", value)

    def has_custom_field_id(self, pk: int | list[int], *, exact: bool = False) -> Self:
        """
        Filter documents that have a custom field with the specified ID(s).

        This method filters documents based on the presence of specific custom fields,
        regardless of their values.

        Args:
            pk: A single custom field ID or list of custom field IDs.
            exact: If True, return results that have exactly these IDs and no others.
                  If False, return results that have at least these IDs.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Documents with custom field ID 5
            >>> docs = client.documents().has_custom_field_id(5)
            >>>
            >>> # Documents with custom field IDs 5 and 7
            >>> docs = client.documents().has_custom_field_id([5, 7])
            >>>
            >>> # Documents with exactly custom field IDs 5 and 7 and no others
            >>> docs = client.documents().has_custom_field_id([5, 7], exact=True)

        """
        if exact:
            return self.filter(custom_fields__id__all=pk)
        return self.filter(custom_fields__id__in=pk)

    def _normalize_custom_field_query_item(self, value: Any) -> str:
        if isinstance(value, tuple):
            # Check if it's a CustomFieldQuery
            try:
                converted_value = CustomFieldQuery(*value)
                return self._normalize_custom_field_query(converted_value)
            except TypeError:
                # It's a tuple, not a CustomFieldQuery
                pass

        if isinstance(value, str):
            return f'"{value}"'
        if isinstance(value, (list, tuple)):
            values = [str(self._normalize_custom_field_query_item(v)) for v in value]
            return f"[{', '.join(values)}]"
        if isinstance(value, bool):
            return str(value).lower()

        return str(value)

    def _normalize_custom_field_query(self, query: _QueryParam) -> str:
        try:
            if not isinstance(query, CustomFieldQuery):
                query = CustomFieldQuery(*query)
        except TypeError as te:
            raise TypeError("Invalid custom field query format") from te

        field, operation, value = query
        operation = self._normalize_custom_field_query_item(operation)
        value = self._normalize_custom_field_query_item(value)
        return f'["{field}", {operation}, {value}]'

    @overload
    def custom_field_query(self, query: _QueryParam) -> Self:
        """
        Filter documents by custom field query.

        Args:
            query: A list representing a custom field query

        Returns:
            Filtered DocumentQuerySet

        """
        ...

    @overload
    def custom_field_query(self, field: str, operation: _OperationType, value: Any) -> Self:
        """
        Filter documents by custom field query.

        This method provides advanced filtering capabilities for custom fields,
        allowing for complex operations like range queries, existence checks, etc.

        Args:
            field: The name of the custom field.
            operation: The operation to perform (e.g., "exact", "contains", "range").
            value: The value to filter by.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Exact match
            >>> docs = client.documents().custom_field_query("Status", "exact", "Paid")
            >>>
            >>> # Range query for dates
            >>> docs = client.documents().custom_field_query("Due Date", "range",
            ...                                            ["2023-01-01", "2023-12-31"])
            >>>
            >>> # Check if field exists
            >>> docs = client.documents().custom_field_query("Priority", "exists", True)

        """
        ...

    @singledispatchmethod  # type: ignore # mypy does not handle singledispatchmethod with overloads correctly
    def custom_field_query(self, *args: Any, **kwargs: Any) -> Self:
        """
        Filter documents by custom field query.
        """
        raise TypeError("Invalid custom field query format")

    @custom_field_query.register  # type: ignore # mypy does not handle singledispatchmethod with overloads correctly
    def _(self, query: CustomFieldQuery) -> Self:
        query_str = self._normalize_custom_field_query(query)
        return self.filter(custom_field_query=query_str)

    @custom_field_query.register  # type: ignore # mypy does not handle singledispatchmethod with overloads correctly
    def _(self, field: str, operation: str | CustomFieldQuery | tuple[str, Any, Any], value: Any) -> Self:
        query = CustomFieldQuery(field, operation, value)
        query_str = self._normalize_custom_field_query(query)
        return self.filter(custom_field_query=query_str)

    def custom_field_range(self, field: str, start: str, end: str) -> Self:
        """
        Filter documents with a custom field value within a specified range.

        This is particularly useful for date or numeric custom fields.

        Args:
            field: The name of the custom field.
            start: The start value of the range.
            end: The end value of the range.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Date range
            >>> docs = client.documents().custom_field_range("Invoice Date", "2023-01-01", "2023-12-31")
            >>>
            >>> # Numeric range
            >>> docs = client.documents().custom_field_range("Amount", "100", "500")

        """
        return self.custom_field_query(field, "range", [start, end])

    def custom_field_exact(self, field: str, value: Any) -> Self:
        """
        Filter documents with a custom field value that matches exactly.

        This method is a shorthand for custom_field_query with the "exact" operation.

        Args:
            field: The name of the custom field.
            value: The exact value to match.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Match exact status
            >>> docs = client.documents().custom_field_exact("Status", "Paid")
            >>>
            >>> # Match exact date
            >>> docs = client.documents().custom_field_exact("Due Date", "2023-04-15")

        """
        return self.custom_field_query(field, "exact", value)

    def custom_field_in(self, field: str, values: list[Any]) -> Self:
        """
        Filter documents with a custom field value in a list of values.

        This method is a shorthand for custom_field_query with the "in" operation.

        Args:
            field: The name of the custom field.
            values: The list of values to match against.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Match documents with status in a list
            >>> docs = client.documents().custom_field_in("Status", ["Paid", "Pending"])
            >>>
            >>> # Match documents with specific reference numbers
            >>> docs = client.documents().custom_field_in("Reference", ["INV-001", "INV-002", "INV-003"])

        """
        return self.custom_field_query(field, "in", values)

    def custom_field_isnull(self, field: str) -> Self:
        """
        Filter documents with a custom field that is null or empty.

        This method finds documents where the specified custom field either
        doesn't exist or has an empty value.

        Args:
            field: The name of the custom field.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents with missing or empty "Status" field
            >>> docs = client.documents().custom_field_isnull("Status")
            >>>
            >>> # Chain with other filters
            >>> recent_missing_field = client.documents().custom_field_isnull("Priority").created_after("2023-01-01")

        """
        return self.custom_field_query("OR", (field, "isnull", True), [field, "exact", ""])

    def custom_field_exists(self, field: str, exists: bool = True) -> Self:
        """
        Filter documents based on the existence of a custom field.

        This method is a shorthand for custom_field_query with the "exists" operation.

        Args:
            field: The name of the custom field.
            exists: True to filter documents where the field exists, False otherwise.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents that have the "Priority" field
            >>> docs = client.documents().custom_field_exists("Priority")
            >>>
            >>> # Find documents that don't have the "Review Date" field
            >>> docs = client.documents().custom_field_exists("Review Date", exists=False)

        """
        return self.custom_field_query(field, "exists", exists)

    def custom_field_contains(self, field: str, values: list[Any]) -> Self:
        """
        Filter documents with a custom field that contains all specified values.

        This method is useful for custom fields that can hold multiple values,
        such as array or list-type fields.

        Args:
            field: The name of the custom field.
            values: The list of values that the field should contain.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents with tags field containing both "important" and "tax"
            >>> docs = client.documents().custom_field_contains("Tags", ["important", "tax"])
            >>>
            >>> # Find documents with categories containing specific values
            >>> docs = client.documents().custom_field_contains("Categories", ["Finance", "Tax"])

        """
        return self.custom_field_query(field, "contains", values)

    def has_custom_fields(self) -> Self:
        """
        Filter documents that have any custom fields.

        This method returns documents that have at least one custom field defined,
        regardless of the field name or value.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find all documents with any custom fields
            >>> docs = client.documents().has_custom_fields()

        """
        return self.filter(has_custom_fields=True)

    def no_custom_fields(self) -> Self:
        """
        Filter documents that do not have any custom fields.

        This method returns documents that have no custom fields defined.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find all documents without any custom fields
            >>> docs = client.documents().no_custom_fields()

        """
        return self.filter(has_custom_fields=False)

    def notes(self, text: str) -> Self:
        """
        Filter documents whose notes contain the specified text.

        This method searches through the document notes for the specified text.

        Args:
            text: The text to search for in document notes.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Find documents with "follow up" in notes
            >>> docs = client.documents().notes("follow up")
            >>>
            >>> # Chain with other filters
            >>> important_notes = client.documents().notes("important").tag_name("tax")

        """
        return self.filter(notes__contains=text)

    def created_before(self, date: datetime | str) -> Self:
        """
        Filter models created before a given date.

        This method filters documents based on their creation date in Paperless-ngx.

        Args:
            date: The date to filter by. Can be a datetime object or an ISO format string.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Using string date
            >>> docs = client.documents().created_before("2023-01-01")
            >>>
            >>> # Using datetime object
            >>> from datetime import datetime
            >>> date = datetime(2023, 1, 1)
            >>> docs = client.documents().created_before(date)

        """
        if isinstance(date, datetime):
            return self.filter(created__lt=date.strftime("%Y-%m-%d"))
        return self.filter(created__lt=date)

    def created_after(self, date: datetime | str) -> Self:
        """
        Filter models created after a given date.

        This method filters documents based on their creation date in Paperless-ngx.

        Args:
            date: The date to filter by. Can be a datetime object or an ISO format string.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Using string date
            >>> docs = client.documents().created_after("2023-01-01")
            >>>
            >>> # Using datetime object
            >>> from datetime import datetime
            >>> date = datetime(2023, 1, 1)
            >>> docs = client.documents().created_after(date)

        """
        if isinstance(date, datetime):
            return self.filter(created__gt=date.strftime("%Y-%m-%d"))
        return self.filter(created__gt=date)

    def created_between(self, start: datetime | str, end: datetime | str) -> Self:
        """
        Filter models created between two dates.

        This method filters documents with creation dates falling within the specified range.

        Args:
            start: The start date to filter by. Can be a datetime object or an ISO format string.
            end: The end date to filter by. Can be a datetime object or an ISO format string.

        Returns:
            Filtered DocumentQuerySet.

        Examples:
            >>> # Using string dates
            >>> docs = client.documents().created_between("2023-01-01", "2023-12-31")
            >>>
            >>> # Using datetime objects
            >>> from datetime import datetime
            >>> start = datetime(2023, 1, 1)
            >>> end = datetime(2023, 12, 31)
            >>> docs = client.documents().created_between(start, end)

        """
        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d")

        return self.filter(created__range=(start, end))

    # Bulk operations
    def _get_ids(self) -> list[int]:
        """
        Get the IDs of all documents in the current queryset.

        Returns:
            List of document IDs

        """
        return [doc.id for doc in self]

    @override
    def delete(self) -> ClientResponse:
        """
        Delete all documents in the current queryset.

        This method performs a bulk delete operation on all documents matching
        the current queryset filters.

        Returns:
            None

        Examples:
            >>> # Delete all documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).delete()
            >>>
            >>> # Delete old documents
            >>> client.documents().created_before("2020-01-01").delete()

        """
        if ids := self._get_ids():
            return self.resource.delete(ids)  # type: ignore # Not sure why pyright is complaining
        return None

    def reprocess(self) -> ClientResponse:
        """
        Reprocess all documents in the current queryset.

        This method triggers Paperless-ngx to re-run OCR and classification
        on all documents matching the current queryset filters.

        Returns:
            ClientResponse: The API response from the reprocess operation.
            None if there are no documents to reprocess.

        Examples:
            >>> # Reprocess documents added in the last week
            >>> from datetime import datetime, timedelta
            >>> week_ago = datetime.now() - timedelta(days=7)
            >>> client.documents().added_after(week_ago.strftime("%Y-%m-%d")).reprocess()
            >>>
            >>> # Reprocess documents with empty content
            >>> client.documents().filter(content="").reprocess()

        """
        if ids := self._get_ids():
            return self.resource.reprocess(ids)
        return None

    def merge(self, metadata_document_id: int | None = None, delete_originals: bool = False) -> bool:
        """
        Merge all documents in the current queryset into a single document.

        This method combines multiple documents into a single PDF document.

        Args:
            metadata_document_id: Apply metadata from this document to the merged document.
                                 If None, metadata from the first document will be used.
            delete_originals: Whether to delete the original documents after merging.

        Returns:
            bool: True if submitting the merge succeeded, False if there are no documents to merge.

        Raises:
            BadResponseError: If the merge operation returns an unexpected response.
            APIError: If the merge operation fails.

        Examples:
            >>> # Merge all documents with tag "merge_me"
            >>> client.documents().tag_name("merge_me").merge(delete_originals=True)
            >>>
            >>> # Merge documents and use metadata from document ID 42
            >>> client.documents().correspondent_name("Electric Company").merge(
            ...     metadata_document_id=42, delete_originals=False
            ... )

        """
        if ids := self._get_ids():
            return self.resource.merge(ids, metadata_document_id, delete_originals)
        return False

    def rotate(self, degrees: int) -> ClientResponse:
        """
        Rotate all documents in the current queryset.

        This method rotates the PDF files of all documents matching the current
        queryset filters.

        Args:
            degrees: Degrees to rotate (must be 90, 180, or 270).

        Returns:
            ClientResponse: The API response from the rotate operation.
            None if there are no documents to rotate.

        Examples:
            >>> # Rotate all documents with "sideways" in title by 90 degrees
            >>> client.documents().title("sideways", exact=False).rotate(90)
            >>>
            >>> # Rotate upside-down documents by 180 degrees
            >>> client.documents().tag_name("upside-down").rotate(180)

        """
        if ids := self._get_ids():
            return self.resource.rotate(ids, degrees)
        return None

    @override
    def update(
        self,
        *,
        # Document metadata
        correspondent: "Correspondent | int | None" = None,
        document_type: "DocumentType | int | None" = None,
        storage_path: "StoragePath | int | None" = None,
        owner: int | None = None,
        **kwargs: Any,
    ) -> Self:
        """
        Perform bulk updates on all documents in the current queryset.

        This method allows for updating multiple document metadata fields in a single
        API call for all documents matching the current queryset filters.

        Args:
            correspondent: Set correspondent for all documents. Can be a Correspondent object or ID.
            document_type: Set document type for all documents. Can be a DocumentType object or ID.
            storage_path: Set storage path for all documents. Can be a StoragePath object or ID.
            owner: Owner ID to assign to all documents.

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Update correspondent for all invoices
            >>> client.documents().title("invoice", exact=False).update(
            ...     correspondent=5,
            ...     document_type=3
            ... )
            >>>
            >>> # Set owner for documents without an owner
            >>> client.documents().filter(owner__isnull=True).update(owner=1)

        """
        if not (ids := self._get_ids()):
            return self

        # Handle correspondent update
        if correspondent is not None:
            self.resource.set_correspondent(ids, correspondent)

        # Handle document type update
        if document_type is not None:
            self.resource.set_document_type(ids, document_type)

        # Handle storage path update
        if storage_path is not None:
            self.resource.set_storage_path(ids, storage_path)

        return self._chain()

    def modify_custom_fields(
        self,
        add_custom_fields: dict[int, Any] | None = None,
        remove_custom_fields: list[int] | None = None,
    ) -> Self:
        """
        Modify custom fields on all documents in the current queryset.

        This method allows for adding, updating, and removing custom fields in bulk
        for all documents matching the current queryset filters.

        Args:
            add_custom_fields: Dictionary of custom field ID to value pairs to add or update.
            remove_custom_fields: List of custom field IDs to remove.

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Add a custom field to documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).modify_custom_fields(
            ...     add_custom_fields={5: "Processed"}
            ... )
            >>>
            >>> # Add one field and remove another
            >>> client.documents().correspondent_id(3).modify_custom_fields(
            ...     add_custom_fields={7: "2023-04-15"},
            ...     remove_custom_fields=[9]
            ... )

        """
        ids = self._get_ids()
        if ids:
            self.resource.modify_custom_fields(ids, add_custom_fields, remove_custom_fields)
        return self

    def modify_tags(self, add_tags: list[int] | None = None, remove_tags: list[int] | None = None) -> Self:
        """
        Modify tags on all documents in the current queryset.

        This method allows for adding and removing tags in bulk for all documents
        matching the current queryset filters.

        Args:
            add_tags: List of tag IDs to add to the documents.
            remove_tags: List of tag IDs to remove from the documents.

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Add tag 3 and remove tag 4 from all documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).modify_tags(
            ...     add_tags=[3], remove_tags=[4]
            ... )
            >>>
            >>> # Add multiple tags to recent documents
            >>> from datetime import datetime, timedelta
            >>> month_ago = datetime.now() - timedelta(days=30)
            >>> client.documents().created_after(month_ago.strftime("%Y-%m-%d")).modify_tags(
            ...     add_tags=[5, 7, 9]
            ... )

        """
        ids = self._get_ids()
        if ids:
            self.resource.modify_tags(ids, add_tags, remove_tags)
        return self

    def add_tag(self, tag_id: int) -> Self:
        """
        Add a tag to all documents in the current queryset.

        This is a convenience method that calls modify_tags with a single tag ID to add.

        Args:
            tag_id: Tag ID to add to all documents in the queryset.

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Add tag 3 to all documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).add_tag(3)
            >>>
            >>> # Add tag to documents from a specific correspondent
            >>> client.documents().correspondent_name("Electric Company").add_tag(5)

        """
        ids = self._get_ids()
        if ids:
            self.resource.add_tag(ids, tag_id)
        return self

    def remove_tag(self, tag_id: int) -> Self:
        """
        Remove a tag from all documents in the current queryset.

        This is a convenience method that calls modify_tags with a single tag ID to remove.

        Args:
            tag_id: Tag ID to remove from all documents in the queryset.

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Remove tag 4 from all documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).remove_tag(4)
            >>>
            >>> # Remove tag from old documents
            >>> client.documents().created_before("2020-01-01").remove_tag(7)

        """
        ids = self._get_ids()
        if ids:
            self.resource.remove_tag(ids, tag_id)
        return self

    def set_permissions(
        self,
        permissions: dict[str, Any] | None = None,
        owner_id: int | None = None,
        merge: bool = False,
    ) -> Self:
        """
        Set permissions for all documents in the current queryset.

        This method allows for updating document permissions in bulk for all documents
        matching the current queryset filters.

        Args:
            permissions: Permissions object defining user and group permissions.
            owner_id: Owner ID to assign to the documents.
            merge: Whether to merge with existing permissions (True) or replace them (False).

        Returns:
            Self: The current queryset for method chaining.

        Examples:
            >>> # Set owner to user 2 for all documents with "invoice" in title
            >>> client.documents().title("invoice", exact=False).set_permissions(owner_id=2)
            >>>
            >>> # Set complex permissions
            >>> permissions = {
            ...     "view": {"users": [1, 2], "groups": [1]},
            ...     "change": {"users": [1], "groups": []}
            ... }
            >>> client.documents().tag_name("confidential").set_permissions(
            ...     permissions=permissions,
            ...     owner_id=1,
            ...     merge=True
            ... )

        """
        ids = self._get_ids()
        if ids:
            self.resource.set_permissions(ids, permissions, owner_id, merge)
        return self

    def summarize(
        self,
        model: str = "gpt-4o-mini",
        template_name: str = "summarize",
        template_dir: str | None = None,
        batch_size: int = 10,
        api_key: str | None = None,
        api_url: str | None = None,
    ) -> Self:
        """
        Summarize documents in the queryset using an LLM.

        Args:
            model: The model to use
            template_name: The template to use
            template_dir: Optional custom directory for templates
            batch_size: Number of documents to process at once
            api_key: Optional OpenAI API key
            api_url: Optional custom OpenAI API URL

        Returns:
            Itself, for chainability

        """
        config = EnrichmentConfig(
            template_name=template_name,
            template_dir=template_dir,
            model=model,
            api_key=api_key,
            api_url=api_url,
            vision=False,  # No need for vision for summarization
        )

        results = []

        # Process documents in batches
        documents: list[Document] = list(self[:])  # type: ignore # TODO
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            for doc in batch:
                result = self.enrichment_service.process_document(doc, config)
                if result.success:
                    results.append(result.document)
                else:
                    logger.error(f"Failed to summarize document {doc.id}: {result.error}")

        return self._chain()

    def describe(
        self,
        model: str = "gpt-4o-mini",
        template_name: str = "describe",
        template_dir: str | None = None,
        batch_size: int = 10,
        max_images: int = 2,
        api_key: str | None = None,
        api_url: str | None = None,
        expanded_description: bool = True,
    ) -> Self:
        """
        Describe documents in the queryset using an LLM with vision capabilities.

        Args:
            model: The model to use
            template_name: The template to use
            template_dir: Optional custom directory for templates
            batch_size: Number of documents to process at once
            max_images: Maximum number of images to extract per document
            api_key: Optional OpenAI API key
            api_url: Optional custom OpenAI API URL

        Returns:
            Itself, for chainability

        """
        config = EnrichmentConfig(
            template_name=template_name,
            template_dir=template_dir,
            model=model,
            api_key=api_key,
            api_url=api_url,
            vision=True,
            extract_images=True,
            max_images=max_images,
        )

        results = []

        # Process documents in batches
        documents: list[Document] = list(self[:])  # type: ignore # TODO
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            for doc in batch:
                result = self.enrichment_service.process_document(doc, config, expand_descriptions=expanded_description)
                if result.success:
                    results.append(result.document)
                else:
                    logger.error(f"Failed to describe document {doc.id}: {result.error}")

        return self._chain()
