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

from pydantic import BaseModel, Field
from yarl import URL

from paperap.models.abstract.model import StandardModel
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
        read_only_fields = {'page_count'}
        filtering_disabled = {'page_count'}

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
