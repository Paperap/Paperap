"""




----------------------------------------------------------------------------

   METADATA:

       File:    document.py
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
from typing import Any, TYPE_CHECKING, Iterable, Iterator, Optional

from pydantic import BaseModel, Field, field_serializer
from yarl import URL

from paperap.models.abstract.model import StandardModel, FilteringStrategies
from paperap.models.document.queryset import DocumentQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag, TagQuerySet


class Document(StandardModel):
    """
    Represents a Paperless-NgX document.
    """
    added: datetime | None = None
    archive_serial_number: str | None = None
    archived_file_name: str | None = None
    content: str | None = None
    correspondent: int | None = None
    created: datetime = Field(description="Creation timestamp", default_factory=datetime.now, alias="created_on")
    created_date: str | None = None
    updated: datetime = Field(description="Last update timestamp", default_factory=datetime.now, alias="updated_on")
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)
    deleted_at: datetime | None = None
    document_type: int | None = None
    is_shared_by_requester: bool = False
    notes: list[Any] = Field(default_factory=list)  # TODO unknown subtype
    original_file_name: str | None = None
    owner: int | None = None
    page_count: int | None = None
    storage_path: int | None = None
    tags: list[int] = Field(default_factory=list)
    title: str
    user_can_change: bool = True

    class Meta(StandardModel.Meta):
        # NOTE: Filtering appears to be disabled by paperless on page_count
        queryset = DocumentQuerySet
        read_only_fields = {'page_count', 'deleted_at', 'updated', 'is_shared_by_requester'}
        filtering_disabled = {'page_count', 'deleted_at', 'updated', 'is_shared_by_requester'}
        filtering_strategies = {FilteringStrategies.WHITELIST}
        whitelist_filtering_params = {
            "id__in",
            "id",
            "title__istartswith",
            "title__iendswith",
            "title__icontains",
            "title__iexact",
            "content__istartswith",
            "content__iendswith",
            "content__icontains",
            "content__iexact",
            "archive_serial_number",
            "archive_serial_number__gt",
            "archive_serial_number__gte",
            "archive_serial_number__lt",
            "archive_serial_number__lte",
            "archive_serial_number__isnull",
            "content__contains",       # maybe?
            "correspondent__isnull",
            "correspondent__id__in",
            "correspondent__id",
            "correspondent__name__istartswith",
            "correspondent__name__iendswith",
            "correspondent__name__icontains",
            "correspondent__name__iexact",
            "correspondent__slug__iexact",     # maybe?
            "created__year",
            "created__month",
            "created__day",
            "created__date__gt",
            "created__gt",
            "created__date__lt",
            "created__lt",
            "added__year",
            "added__month",
            "added__day",
            "added__date__gt",
            "added__gt",
            "added__date__lt",
            "added__lt",
            "modified__year",
            "modified__month",
            "modified__day",
            "modified__date__gt",
            "modified__gt",
            "modified__date__lt",
            "modified__lt",
            "original_filename__istartswith",
            "original_filename__iendswith",
            "original_filename__icontains",
            "original_filename__iexact",
            "checksum__istartswith",
            "checksum__iendswith",
            "checksum__icontains",
            "checksum__iexact",
            "tags__id__in",
            "tags__id",
            "tags__name__istartswith",
            "tags__name__iendswith",
            "tags__name__icontains",
            "tags__name__iexact",
            "document_type__isnull",
            "document_type__id__in",
            "document_type__id",
            "document_type__name__istartswith",
            "document_type__name__iendswith",
            "document_type__name__icontains",
            "document_type__name__iexact",
            "storage_path__isnull",
            "storage_path__id__in",
            "storage_path__id",
            "storage_path__name__istartswith",
            "storage_path__name__iendswith",
            "storage_path__name__icontains",
            "storage_path__name__iexact",
            "owner__isnull",
            "owner__id__in",
            "owner__id",
            "is_tagged",
            "tags__id__all",
            "tags__id__none",
            "correspondent__id__none",
            "document_type__id__none",
            "storage_path__id__none",
            "is_in_inbox",
            "title_content",
            "owner__id__none",
            "custom_fields__icontains",
            "custom_fields__id__all",
            "custom_fields__id__none",   # ??
            "custom_fields__id__in",
            "custom_field_query",        # ??
            "has_custom_fields",
            "shared_by__id",
            "shared_by__id__in",
        }

    @field_serializer('added', 'created', 'updated', 'deleted_at')
    def serialize_datetime(self, value: datetime | None, _info):
        return value.isoformat() if value else None

    @property
    def custom_field_ids(self) -> list[int]:
        return [field['field'] for field in self.custom_fields]

    @property
    def custom_field_values(self) -> list[Any]:
        return [field['value'] for field in self.custom_fields]
    
    def get_tags(self) -> TagQuerySet:
        """
        Get the tags for this document.

        Returns:
            List of tags associated with this document.
        """
        if not self.tags:
            return self._meta.resource.client.tags().none()

        # Use the API's filtering capability to get only the tags with specific IDs
        # The paperless-ngx API supports id__in filter for retrieving multiple objects by ID
        return self._meta.resource.client.tags().id(self.tags)

    def get_correspondent(self) -> Optional["Correspondent"]:
        """
        Get the correspondent for this document.

        Returns:
            The correspondent or None if not set.
        """
        if not self.correspondent:
            return None
        return self._meta.resource.client.correspondents().get(self.correspondent)

    def get_document_type(self) -> Optional["DocumentType"]:
        """
        Get the document type for this document.

        Returns:
            The document type or None if not set.
        """
        if not self.document_type:
            return None
        return self._meta.resource.client.document_types.get(self.document_type)

    def get_storage_path(self) -> Optional["StoragePath"]:
        """
        Get the storage path for this document.

        Returns:
            The storage path or None if not set.
        """
        if not self.storage_path:
            return None
        return self._meta.resource.client.storage_paths.get(self.storage_path)

    def custom_field(self, field_id: int, default : Any = None, *, raise_errors : bool = False) -> Any:
        """
        Get the value of a custom field by ID.

        Args:
            field_id: The ID of the custom field.
            default: The value to return if the field is not found.
            raise_errors: Whether to raise an error if the field is not found.
        """
        for field in self.custom_fields:
            if field['field'] == field_id:
                return field['value']

        if raise_errors:
            raise ValueError(f"Custom field {field_id} not found")
        return default
            
    """
    def __getattr__(self, name: str) -> Any:
        # Allow easy access to custom fields
        for custom_field in self.custom_fields:
            if custom_field['field'] == name:
                return custom_field['value']
            
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    """