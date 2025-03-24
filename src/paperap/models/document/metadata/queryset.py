"""
Document metadata queryset module for interacting with document metadata in Paperless-ngx.

This module provides the DocumentMetadataQuerySet class, which extends StandardQuerySet
to handle document metadata-specific operations and filtering.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.metadata.model import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentMetadataQuerySet(StandardQuerySet["DocumentMetadata"]):
    """
    A specialized queryset for interacting with Paperless-NGX document metadata.

    This queryset extends StandardQuerySet to provide document metadata-specific
    filtering methods, making it easier to query metadata by their attributes.

    Document metadata contains information about documents such as original filename,
    media information, archive metadata, and other system-level properties that
    aren't part of the document's content or user-assigned metadata.

    The queryset is lazy-loaded, meaning API requests are only made when data is
    actually needed (when iterating, counting, or accessing specific items).

    Examples:
        >>> # Get metadata for a specific document
        >>> metadata = client.document_metadata.filter(document=123).first()
        >>> print(f"Original filename: {metadata.original_filename}")
        >>>
        >>> # Get metadata for documents with specific archive information
        >>> archived = client.document_metadata.filter(archive_checksum__isnull=False)

    """

    pass
