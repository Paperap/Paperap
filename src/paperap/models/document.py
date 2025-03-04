"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    document.py                                                                                          *
*        Project: models                                                                                               *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING, Iterable, Iterator, Optional

from pydantic import BaseModel, Field
from yarl import URL

from paperap.models.base import PaperlessModel
from paperap.models.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag


class Document(PaperlessModel):
    """
    Represents a Paperless-NgX document.
    """

    title: str
    content: str | None = None
    added: datetime | None = None
    archive_serial_number: str | None = None
    original_file_name: str | None = None
    correspondent: int | None = None
    document_type: int | None = None
    storage_path: int | None = None
    tags: list[int] = Field(default_factory=list)

    def get_tags(self) -> QuerySet["Tag"]:
        """
        Get the tags for this document.

        Returns:
            List of tags associated with this document.
        """
        if not self.tags:
            return self._meta.resource.client.tags().none()

        # Use the API's filtering capability to get only the tags with specific IDs
        # The paperless-ngx API supports id__in filter for retrieving multiple objects by ID
        tag_ids_param = ",".join(str(tag_id) for tag_id in self.tags)
        return self._meta.resource.client.tags(params={"id__in": tag_ids_param})

    def get_correspondent(self) -> Optional["Correspondent"]:
        """
        Get the correspondent for this document.

        Returns:
            The correspondent or None if not set.
        """
        if not self.correspondent:
            return None
        return self._meta.resource.client.correspondents.get(self.correspondent)

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
