"""
Module for managing share links in Paperless-NgX.

This module provides the ShareLinks model for creating, retrieving, and managing
document share links in Paperless-NgX. Share links allow documents to be shared
with users who don't have access to the Paperless-NgX instance.
"""

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
    """
    Model representing a share link in Paperless-NgX.

    Share links allow documents to be shared with users who don't have access to the
    Paperless-NgX instance. Each share link has a unique slug that can be used to access
    the document without authentication.

    Attributes:
        expiration (datetime | None): When the share link expires. If None, the link never expires.
        slug (str | None): Unique identifier for the share link URL.
        document (int | None): ID of the document being shared.
        created (datetime | None): When the share link was created.
        file_version (ShareLinkFileVersionType | None): Which version of the document to share.
        owner (int | None): ID of the user who created the share link.

    Examples:
        >>> # Create a new share link for document with ID 123
        >>> share_link = client.share_links.create(document=123)
        >>> print(f"Share link created: {share_link.slug}")
        >>>
        >>> # Create a share link that expires in 7 days
        >>> from datetime import datetime, timedelta
        >>> expiry = datetime.now() + timedelta(days=7)
        >>> share_link = client.share_links.create(
        ...     document=123,
        ...     expiration=expiry
        ... )

    """

    expiration: datetime | None = None
    slug: str | None = None
    document: int | None = None
    created: datetime | None = Field(description="Creation timestamp", default=None, alias="created_on")
    file_version: ShareLinkFileVersionType | None = None
    owner: int | None = None

    class Meta(StandardModel.Meta):
        """
        Metadata for the ShareLinks model.

        This class defines the queryset class to use for ShareLinks queries.
        """

        queryset = ShareLinksQuerySet

    @field_serializer("expiration", "created")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        Serialize a datetime object to an ISO 8601 formatted string.

        This serializer converts datetime objects to ISO 8601 formatted strings
        for JSON serialization when sending data to the Paperless-NgX API.

        Args:
            value (datetime | None): The datetime object to serialize.

        Returns:
            str | None: The ISO 8601 formatted string representation of the datetime,
                or None if the input is None.

        Examples:
            >>> share_link = ShareLinks()
            >>> from datetime import datetime
            >>> dt = datetime(2023, 1, 15, 12, 30, 45)
            >>> share_link.serialize_datetime(dt)
            '2023-01-15T12:30:45'
            >>> share_link.serialize_datetime(None)
            None

        """
        return value.isoformat() if value else None

    def get_document(self) -> "Document":
        """
        Get the document associated with this share link.

        Retrieves the full Document object associated with this share link
        by querying the Paperless-NgX API using the document ID stored in
        this share link.

        Returns:
            Document: The document object associated with this share link.

        Raises:
            ValueError: If the document ID is not set on this share link.
            ResourceNotFoundError: If the document doesn't exist in Paperless-NgX.

        Examples:
            >>> share_link = client.share_links.get(5)
            >>> document = share_link.get_document()
            >>> print(f"Shared document title: {document.title}")

        """
        if not self.document:
            raise ValueError("Document ID not set")
        return self._client.documents().get(pk=self.document)
