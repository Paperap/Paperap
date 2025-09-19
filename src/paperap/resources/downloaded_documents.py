"""
Resource module for managing downloaded documents in Paperless-NgX.

This module provides the DownloadedDocumentResource class, which serves as an interface
for interacting with downloaded document records in the Paperless-NgX system. It allows
for retrieving, filtering, and managing documents that have been downloaded from the server.

Typical usage example:
    client = PaperlessClient()
    downloaded_docs = client.downloaded_documents.all()
    for doc in downloaded_docs:
        print(f"{doc.title} - Downloaded on {doc.downloaded_at}")
"""

from __future__ import annotations

from paperap.models.document import DownloadedDocument, DownloadedDocumentQuerySet
from paperap.resources.base import StandardResource


class DownloadedDocumentResource(StandardResource[DownloadedDocument, DownloadedDocumentQuerySet]):
    """
    Resource for managing downloaded documents in Paperless-NgX.

    This class provides methods for interacting with the downloaded documents
    API endpoint, allowing for operations such as retrieval, filtering, and management
    of downloaded document records. It inherits from StandardResource and implements
    the standard CRUD operations for downloaded documents.

    Attributes:
        model_class (type): The DownloadedDocument model class associated with this resource.
        queryset_class (type): The DownloadedDocumentQuerySet class used for query operations.
        name (str): The resource name used in API endpoints ("downloaded_documents").

    Example:
        >>> # Get all downloaded documents
        >>> downloaded_docs = client.downloaded_documents.all()
        >>>
        >>> # Get a specific downloaded document by ID
        >>> doc = client.downloaded_documents.get(123)
        >>> print(f"Downloaded: {doc.title}")
        >>>
        >>> # Filter downloaded documents
        >>> recent_downloads = client.downloaded_documents.filter(
        ...     downloaded_at__gt="2023-01-01T00:00:00Z"
        ... )

    """

    model_class = DownloadedDocument
    queryset_class = DownloadedDocumentQuerySet
    name: str = "downloaded_documents"
