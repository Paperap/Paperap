"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from typing import Any, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner

if TYPE_CHECKING:
    from paperap.models.document.model import Document
    from paperap.models.correspondent import Correspondent

logger = logging.getLogger(__name__)


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
        return self.filter(correspondent=correspondent_id)

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
        return self.filter(document_type=document_type_id)

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
        return self.filter(storage_path=storage_path_id)

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

    def deleted_before(self, date_str: str) -> Self:
        """
        Filter documents deleted before the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(deleted_at__lt=date_str)

    def deleted_after(self, date_str: str) -> Self:
        """
        Filter documents deleted after the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(deleted_at__gt=date_str)

    def shared(self, value: bool) -> Self:
        """
        Filter documents by shared status.

        Args:
            value: True to filter shared documents, False for unshared

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(is_shared_by_requester=value)

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

    def page_count(self, page_count: int) -> Self:
        """
        Filter documents by page count.

        Args:
            page_count: The page count to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(page_count=page_count)

    def page_count_over(self, page_count: int) -> Self:
        """
        Filter documents with more pages than the specified count.

        Args:
            page_count: The minimum page count

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(page_count__gt=page_count)

    def page_count_under(self, page_count: int) -> Self:
        """
        Filter documents with fewer pages than the specified count.

        Args:
            page_count: The maximum page count

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(page_count__lt=page_count)

    def page_count_between(self, min_pages: int, max_pages: int) -> Self:
        """
        Filter documents with a page count between the specified range.

        Args:
            min_pages: The minimum page count
            max_pages: The maximum page count

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(page_count__range=(min_pages, max_pages))

    def user_can_change(self, value: bool) -> Self:
        """
        Filter documents by user change permission.

        Args:
            value: True to filter documents the user can change

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(user_can_change=value)

    def custom_field(self, field_name: str, value: Any, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter documents by custom field value.

        Args:
            field_name: The name of the custom field
            value: The value to filter by
            exact: If True, match the exact value, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            return self.filter(custom_fields__contains={field_name: value})
        return self.filter(custom_fields__contains={field_name: {"$regex": value}})

    def has_custom_field(self, field_name: str) -> Self:
        """
        Filter documents that have a custom field with the specified name.

        Args:
            field_name: The name of the custom field

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(custom_fields__has_key=field_name)

    def custom_field_over(self, field_name: str, value: Any) -> Self:
        """
        Filter documents with a custom field value greater than the specified value.

        Args:
            field_name: The name of the custom field
            value: The minimum value

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(custom_fields__contains={field_name: {"$gt": value}})

    def custom_field_under(self, field_name: str, value: Any) -> Self:
        """
        Filter documents with a custom field value less than the specified value.

        Args:
            field_name: The name of the custom field
            value: The maximum value

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(custom_fields__contains={field_name: {"$lt": value}})

    def custom_field_between(self, field_name: str, min_value: Any, max_value: Any) -> Self:
        """
        Filter documents with a custom field value between the specified range.

        Args:
            field_name: The name of the custom field
            min_value: The minimum value
            max_value: The maximum value

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(custom_fields__contains={field_name: {"$gte": min_value, "$lte": max_value}})

    def notes(self, text: str) -> Self:
        """
        Filter documents whose notes contain the specified text.

        Args:
            text: The text to search for in document notes

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(notes__contains=text)
