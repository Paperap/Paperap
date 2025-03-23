

from __future__ import annotations

from enum import Enum
from typing import Any

from paperap.const import URLS
from paperap.models.abstract import StandardModel


class RetrieveFileMode(str, Enum):
    """Enum for document file retrieval modes."""

    DOWNLOAD = "download"
    PREVIEW = "preview"
    THUMBNAIL = "thumbnail"


class DownloadedDocument(StandardModel):
    """
    Represents a downloaded Paperless-NgX document file.

    Attributes:
        mode: The retrieval mode (download, preview, thumbnail).
        original: Whether to retrieve the original file.
        content: The binary content of the file.
        content_type: The MIME type of the file.
        disposition_filename: The filename from the Content-Disposition header.
        disposition_type: The type from the Content-Disposition header.

    """

    mode: RetrieveFileMode | None = None
    original: bool = False
    content: bytes | None = None
    content_type: str | None = None
    disposition_filename: str | None = None
    disposition_type: str | None = None

    class Meta(StandardModel.Meta):
        read_only_fields = {"content", "content_type", "disposition_filename", "disposition_type"}
