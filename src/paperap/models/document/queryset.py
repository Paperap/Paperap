"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from functools import singledispatchmethod
from typing import Any, NamedTuple, Self, Union, Optional, TYPE_CHECKING, overload
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner

if TYPE_CHECKING:
    from paperap.models.document.model import Document
    from paperap.models.correspondent import Correspondent

logger = logging.getLogger(__name__)

_OperationType = Union[str, "_QueryParam"]
_QueryParam = Union["CustomFieldQuery", tuple[str, _OperationType, Any]]


class CustomFieldQuery(NamedTuple):
    field: str
    operation: _OperationType
    value: Any


class DocumentQuerySet(StandardQuerySet["Document"], HasOwner):
    """
    QuerySet for Paperless-ngx documents with specialized filtering methods.
    """

    def tag_id(self, tag_id: int | list[int]) -> Self:
        """
        Filter documents that have the specified tag ID(s).

        Args:
            tag_id: A single tag ID or list of tag IDs

        Returns:
            Filtered DocumentQuerySet
        """
        if isinstance(tag_id, list):
            return self.filter(tags__id__in=tag_id)
        return self.filter(tags__id=tag_id)

    def tag_name(self, tag_name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents that have a tag with the specified name.

        Args:
            tag_name: The name of the tag
            exact: If True, match the exact tag name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("tags__name", tag_name, exact=exact, case_insensitive=case_insensitive)

    def title(self, title: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by title.

        Args:
            title: The document title to filter by
            exact: If True, match the exact title, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("title", title, exact=exact, case_insensitive=case_insensitive)

    def correspondent(
        self, value: int | str | None = None, *, exact: bool = True, case_insensitive: bool = True, **kwargs
    ) -> Self:
        """
        Filter documents by correspondent.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The correspondent ID or name to filter by
            exact: If True, match the exact value, otherwise use contains
            **kwargs: Additional filters (slug, id, name)

        Returns:
            Filtered DocumentQuerySet

        Raises:
            ValueError: If no valid filters are provided

        Examples:
            # Filter by ID
            client.documents().all().correspondent(1)
            client.documents().all().correspondent(id=1)

            # Filter by name
            client.documents().all().correspondent("John Doe")
            client.documents().all().correspondent(name="John Doe")

            # Filter by name (exact match)
            client.documents().all().correspondent("John Doe", exact=True)
            client.documents().all().correspondent(name="John Doe", exact=True)

            # Filter by slug
            client.documents().all().correspondent(slug="john-doe")

            # Filter by ID and name
            client.documents().all().correspondent(1, name="John Doe")
            client.documents().all().correspondent(id=1, name="John Doe")
            client.documents().all().correspondent("John Doe", id=1)
        """
        qs = self
        if value is not None:
            if isinstance(value, int):
                qs = qs.correspondent_id(value)
            elif isinstance(value, str):
                qs = qs.correspondent_name(value, exact=exact, case_insensitive=case_insensitive)
            else:
                raise TypeError("Invalid value type for correspondent filter")

        if (slug := kwargs.get("slug")) is not None:
            qs = qs.correspondent_slug(slug, exact=exact, case_insensitive=case_insensitive)
        if (id := kwargs.get("id")) is not None:
            qs = qs.correspondent_id(id)
        if (name := kwargs.get("name")) is not None:
            qs = qs.correspondent_name(name, exact=exact, case_insensitive=case_insensitive)

        # If no filters have been applied, raise an error
        if qs is self:
            raise ValueError("No valid filters provided for correspondent")

        return qs

    def correspondent_id(self, correspondent_id: int) -> Self:
        """
        Filter documents by correspondent ID.

        Args:
            correspondent_id: The correspondent ID to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(correspondent__id=correspondent_id)

    def correspondent_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by correspondent name.

        Args:
            name: The correspondent name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("correspondent__name", name, exact=exact, case_insensitive=case_insensitive)

    def correspondent_slug(self, slug: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by correspondent slug.

        Args:
            slug: The correspondent slug to filter by
            exact: If True, match the exact slug, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("correspondent__slug", slug, exact=exact, case_insensitive=case_insensitive)

    def document_type(
        self, value: int | str | None = None, *, exact: bool = True, case_insensitive: bool = True, **kwargs
    ) -> Self:
        """
        Filter documents by document type.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The document type ID or name to filter by
            exact: If True, match the exact value, otherwise use contains
            **kwargs: Additional filters (id, name)

        Returns:
            Filtered DocumentQuerySet

        Raises:
            ValueError: If no valid filters are provided

        Examples:
            # Filter by ID
            client.documents().all().document_type(1)
            client.documents().all().document_type(id=1)

            # Filter by name
            client.documents().all().document_type("Invoice")
            client.documents().all().document_type(name="Invoice")

            # Filter by name (exact match)
            client.documents().all().document_type("Invoice", exact=True)
            client.documents().all().document_type(name="Invoice", exact=True)

            # Filter by ID and name
            client.documents().all().document_type(1, name="Invoice")
            client.documents().all().document_type(id=1, name="Invoice")
            client.documents().all().document_type("Invoice", id=1)
        """
        qs = self
        if value is not None:
            if isinstance(value, int):
                qs = qs.document_type_id(value)
            elif isinstance(value, str):
                qs = qs.document_type_name(value, exact=exact, case_insensitive=case_insensitive)
            else:
                raise TypeError("Invalid value type for document type filter")

        if (id := kwargs.get("id")) is not None:
            qs = qs.document_type_id(id)
        if (name := kwargs.get("name")) is not None:
            qs = qs.document_type_name(name, exact=exact, case_insensitive=case_insensitive)

        # If no filters have been applied, raise an error
        if qs is self:
            raise ValueError("No valid filters provided for document type")

        return qs

    def document_type_id(self, document_type_id: int) -> Self:
        """
        Filter documents by document type ID.

        Args:
            document_type_id: The document type ID to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(document_type__id=document_type_id)

    def document_type_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by document type name.

        Args:
            name: The document type name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("document_type__name", name, exact=exact, case_insensitive=case_insensitive)

    def storage_path(
        self, value: int | str | None = None, *, exact: bool = True, case_insensitive: bool = True, **kwargs
    ) -> Self:
        """
        Filter documents by storage path.

        Any number of filter arguments can be provided, but at least one must be specified.

        Args:
            value: The storage path ID or name to filter by
            exact: If True, match the exact value, otherwise use contains
            **kwargs: Additional filters (id, name)

        Returns:
            Filtered DocumentQuerySet

        Raises:
            ValueError: If no valid filters are provided

        Examples:
            # Filter by ID
            client.documents().all().storage_path(1)
            client.documents().all().storage_path(id=1)

            # Filter by name
            client.documents().all().storage_path("Invoices")
            client.documents().all().storage_path(name="Invoices")

            # Filter by name (exact match)
            client.documents().all().storage_path("Invoices", exact=True)
            client.documents().all().storage_path(name="Invoices", exact=True)

            # Filter by ID and name
            client.documents().all().storage_path(1, name="Invoices")
            client.documents().all().storage_path(id=1, name="Invoices")
            client.documents().all().storage_path("Invoices", id=1)
        """
        qs = self
        if value is not None:
            if isinstance(value, int):
                qs = qs.storage_path_id(value)
            elif isinstance(value, str):
                qs = qs.storage_path_name(value, exact=exact, case_insensitive=case_insensitive)
            else:
                raise TypeError("Invalid value type for storage path filter")

        if (id := kwargs.get("id")) is not None:
            qs = qs.storage_path_id(id)
        if (name := kwargs.get("name")) is not None:
            qs = qs.storage_path_name(name, exact=exact, case_insensitive=case_insensitive)

        # If no filters have been applied, raise an error
        if qs is self:
            raise ValueError("No valid filters provided for storage path")

        return qs

    def storage_path_id(self, storage_path_id: int) -> Self:
        """
        Filter documents by storage path ID.

        Args:
            storage_path_id: The storage path ID to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(storage_path__id=storage_path_id)

    def storage_path_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by storage path name.

        Args:
            name: The storage path name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("storage_path__name", name, exact=exact, case_insensitive=case_insensitive)

    def content(self, text: str) -> Self:
        """
        Filter documents whose content contains the specified text.

        Args:
            text: The text to search for in document content

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(content__contains=text)

    def added_after(self, date_str: str) -> Self:
        """
        Filter documents added after the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(added__gt=date_str)

    def added_before(self, date_str: str) -> Self:
        """
        Filter documents added before the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(added__lt=date_str)

    def asn(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by archive serial number.

        Args:
            value: The archive serial number to filter by
            exact: If True, match the exact value, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("asn", value, exact=exact, case_insensitive=case_insensitive)

    def original_file_name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by original file name.

        Args:
            name: The original file name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter_field_by_str("original_file_name", name, exact=exact, case_insensitive=case_insensitive)

    def user_can_change(self, value: bool) -> Self:
        """
        Filter documents by user change permission.

        Args:
            value: True to filter documents the user can change

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(user_can_change=value)

    def custom_field_fullsearch(self, value: str, *, case_insensitive: bool = True) -> Self:
        """
        Filter documents by searching through both custom field name and value.

        Args:
            value: The search string

        Returns:
            Filtered DocumentQuerySet
        """
        if case_insensitive:
            return self.filter(custom_fields__icontains=value)
        raise NotImplementedError("Case-sensitive custom field search is not supported by Paperless NGX")

    def custom_field(self, field: str, value: Any, *, exact: bool = False, case_insensitive: bool = True) -> Self:
        """
        Filter documents by custom field.

        Args:
            field: The name of the custom field
            value: The value to filter by
            exact: If True, match the exact value, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            if case_insensitive:
                return self.custom_field_query(field, "iexact", value)
            return self.custom_field_query(field, "exact", value)
        if case_insensitive:
            return self.custom_field_query(field, "icontains", value)
        return self.custom_field_query(field, "contains", value)

    def has_custom_field_id(self, id: int | list[int], *, exact: bool = False) -> Self:
        """
        Filter documents that have a custom field with the specified ID(s).

        Args:
            id: A single custom field ID or list of custom field IDs
            exact: If True, return results that have exactly these ids and no others

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            return self.filter(custom_fields__id__all=id)
        return self.filter(custom_fields__id__in=id)

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
        except TypeError:
            raise TypeError("Invalid custom field query format")

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

        Args:
            field: The name of the custom field
            operation: The operation to perform
            value: The value to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        ...

    @singledispatchmethod
    def custom_field_query(self, *args, **kwargs) -> Self:
        raise TypeError("Invalid custom field query format")

    @custom_field_query.register
    def _(self, query: CustomFieldQuery) -> Self:
        query_str = self._normalize_custom_field_query(query)
        return self.filter(custom_field_query=query_str)

    @custom_field_query.register
    def _(self, field: str, operation: str | CustomFieldQuery | tuple[str, Any, Any], value: Any) -> Self:
        query = CustomFieldQuery(field, operation, value)
        query_str = self._normalize_custom_field_query(query)
        return self.filter(custom_field_query=query_str)

    def custom_field_range(self, field: str, start: str, end: str) -> Self:
        """
        Filter documents with a custom field value within a specified range.

        Args:
            field: The name of the custom field
            start: The start value of the range
            end: The end value of the range

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query(field, "range", [start, end])

    def custom_field_exact(self, field: str, value: Any) -> Self:
        """
        Filter documents with a custom field value that matches exactly.

        Args:
            field: The name of the custom field
            value: The exact value to match

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query(field, "exact", value)

    def custom_field_in(self, field: str, values: list[Any]) -> Self:
        """
        Filter documents with a custom field value in a list of values.

        Args:
            field: The name of the custom field
            values: The list of values to match

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query(field, "in", values)

    def custom_field_isnull(self, field: str) -> Self:
        """
        Filter documents with a custom field that is null or empty.

        Args:
            field: The name of the custom field

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query("OR", (field, "isnull", True), [field, "exact", ""])

    def custom_field_exists(self, field: str, exists: bool = True) -> Self:
        """
        Filter documents based on the existence of a custom field.

        Args:
            field: The name of the custom field
            exists: True to filter documents where the field exists, False otherwise

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query(field, "exists", exists)

    def custom_field_contains(self, field: str, values: list[Any]) -> Self:
        """
        Filter documents with a custom field that contains all specified values.

        Args:
            field: The name of the custom field
            values: The list of values that the field should contain

        Returns:
            Filtered DocumentQuerySet
        """
        return self.custom_field_query(field, "contains", values)
        return self.filter(has_custom_fields=True)

    def no_custom_fields(self) -> Self:
        return self.filter(has_custom_fields=False)

    def notes(self, text: str) -> Self:
        """
        Filter documents whose notes contain the specified text.

        Args:
            text: The text to search for in document notes

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(notes__contains=text)

    def created_before(self, date: datetime | str) -> Self:
        """
        Filter models created before a given date.

        Args:
            date: The date to filter by

        Returns:
            Filtered QuerySet
        """
        if isinstance(date, datetime):
            return self.filter(created__lt=date.strftime("%Y-%m-%d"))
        return self.filter(created__lt=date)

    def created_after(self, date: datetime | str) -> Self:
        """
        Filter models created after a given date.

        Args:
            date: The date to filter by

        Returns:
            Filtered QuerySet
        """
        if isinstance(date, datetime):
            return self.filter(created__gt=date.strftime("%Y-%m-%d"))
        return self.filter(created__gt=date)

    def created_between(self, start: datetime | str, end: datetime | str) -> Self:
        """
        Filter models created between two dates.

        Args:
            start: The start date to filter by
            end: The end date to filter by

        Returns:
            Filtered QuerySet
        """
        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d")

        return self.filter(created__range=(start, end))
