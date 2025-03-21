"""
----------------------------------------------------------------------------

METADATA:

File:    metadata.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

from __future__ import annotations

from paperap.models.abstract import StandardModel


class MetadataElement(StandardModel):
    """
    Represents metadata for a document in Paperless-NgX.

    This is a key-value pair of metadata information.
    """

    key: str
    value: str

    class Meta(StandardModel.Meta):
        read_only_fields = {"key", "value"}


class DocumentMetadata(StandardModel):
    """
    Represents a Paperless-NgX document's metadata.

    Attributes:
        original_checksum: The checksum of the original document.
        original_size: The size of the original document in bytes.
        original_mime_type: The MIME type of the original document.
        media_filename: The filename of the media file.
        has_archive_version: Whether the document has an archive version.
        original_metadata: Metadata of the original document.
        archive_checksum: The checksum of the archived document.
        archive_media_filename: The filename of the archived media file.
        original_filename: The original filename of the document.
        lang: The language of the document.
        archive_size: The size of the archived document in bytes.
        archive_metadata: Metadata of the archived document.

    """

    original_checksum: str | None = None
    original_size: int | None = None
    original_mime_type: str | None = None
    media_filename: str | None = None
    has_archive_version: bool | None = None
    original_metadata: list[MetadataElement] = []
    archive_checksum: str | None = None
    archive_media_filename: str | None = None
    original_filename: str | None = None
    lang: str | None = None
    archive_size: int | None = None
    archive_metadata: list[MetadataElement] = []

    class Meta(StandardModel.Meta):
        read_only_fields = {
            "original_checksum",
            "original_size",
            "original_mime_type",
            "media_filename",
            "has_archive_version",
            "original_metadata",
            "archive_checksum",
            "archive_media_filename",
            "original_filename",
            "lang",
            "archive_size",
            "archive_metadata",
        }
