

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field, field_serializer

from paperap.const import ShareLinkFileVersionType
from paperap.models.abstract.model import StandardModel
from paperap.models.share_links.queryset import ShareLinksQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.document import Document
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag


class ShareLinks(StandardModel):
    expiration: datetime | None = None
    slug: str | None = None
    document: int | None = None
    created: datetime | None = Field(description="Creation timestamp", default=None, alias="created_on")
    file_version: ShareLinkFileVersionType | None = None
    owner: int | None = None

    class Meta(StandardModel.Meta):
        queryset = ShareLinksQuerySet

    @field_serializer("expiration", "created")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        Serialize a datetime object to an ISO 8601 formatted string

        Args:
            value (datetime): The datetime object to serialize

        Returns:
            str: The serialized datetime

        """
        return value.isoformat() if value else None

    def get_document(self) -> "Document":
        """
        Get the document associated with this share link

        Returns:
            Document: The document object

        """
        if not self.document:
            raise ValueError("Document ID not set")
        return self._client.documents().get(pk=self.document)
