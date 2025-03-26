"""
Document download functionality for Paperless-NgX documents.

This module provides classes for handling document file downloads from a Paperless-NgX
server, including different retrieval modes (download, preview, thumbnail) and
metadata about the downloaded files.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from paperap.const import URLS
from paperap.models.abstract import StandardModel

if TYPE_CHECKING:
    from paperap.resources.document_download import DownloadedDocumentResource


class RetrieveFileMode(str, Enum):
    """
    Enum for document file retrieval modes.

    This enum defines the different ways a document can be retrieved from
    the Paperless-NgX server, each corresponding to a different endpoint
    and potentially different file format.

    Attributes:
        DOWNLOAD: Retrieve the full document file for downloading.
        PREVIEW: Retrieve a preview version of the document (typically PDF).
        THUMBNAIL: Retrieve a thumbnail image of the document.

    """

    DOWNLOAD = "download"
    PREVIEW = "preview"
    THUMBNAIL = "thumbnail"


class DownloadedDocument(StandardModel):
    """
    Represents a downloaded Paperless-NgX document file.

    This model stores both the binary content of a downloaded document file
    and metadata about the file, such as its content type and suggested filename.
    It is typically used as a return value from document download operations.

    Attributes:
        mode (RetrieveFileMode | None): The retrieval mode used (download, preview,
            or thumbnail). Determines which endpoint was used to retrieve the file.
        original (bool): Whether to retrieve the original file (True) or the archived
            version (False). Only applicable for DOWNLOAD mode.
        content (bytes | None): The binary content of the downloaded file.
        content_type (str | None): The MIME type of the file (e.g., "application/pdf").
        disposition_filename (str | None): The suggested filename from the
            Content-Disposition header.
        disposition_type (str | None): The disposition type from the Content-Disposition
            header (typically "attachment" or "inline").

    Examples:
        >>> # Download a document
        >>> doc = client.documents.get(123)
        >>> downloaded = doc.download_content()
        >>> print(f"Downloaded {len(downloaded.content)} bytes")
        >>> print(f"File type: {downloaded.content_type}")
        >>> print(f"Filename: {downloaded.disposition_filename}")

    """

    mode: RetrieveFileMode | None = None
    original: bool = False
    content: bytes | None = None
    content_type: str | None = None
    disposition_filename: str | None = None
    disposition_type: str | None = None
    _resource: "DownloadedDocumentResource"  # type: ignore # because mypy doesn't accept nested generics

    class Meta(StandardModel.Meta):
        """
        Metadata for the DownloadedDocument model.

        Defines which fields are read-only and should not be modified by the client.
        """

        read_only_fields = {"content", "content_type", "disposition_filename", "disposition_type"}
