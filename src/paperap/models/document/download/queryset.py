"""
Module for handling document download operations through querysets.

This module provides the queryset implementation for downloaded documents,
enabling efficient querying and manipulation of document download operations
in Paperless-NgX.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.download.model import DownloadedDocument

logger = logging.getLogger(__name__)


class DownloadedDocumentQuerySet(StandardQuerySet["DownloadedDocument"]):
    """
    A specialized queryset for handling downloaded document operations.

    This queryset extends StandardQuerySet to provide functionality specific to
    downloaded documents from Paperless-NgX. It enables efficient querying,
    filtering, and manipulation of document download operations.

    The queryset is lazy-loaded, meaning API requests are only made when data
    is actually needed, improving performance when working with large document
    collections.

    Examples:
        >>> # Download original documents
        >>> client.documents.filter(title__contains="invoice").download("invoices/")
        >>>
        >>> # Download archive versions
        >>> client.documents.filter(archived=True).download(
        ...     "archives/", archive_version=True
        ... )

    """

    pass
