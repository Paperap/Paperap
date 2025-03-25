"""
Define the StoragePath model for managing document storage locations in Paperless-NgX.

This module provides the StoragePath model class, which represents physical storage
locations where documents are stored in the Paperless-NgX file system. Storage paths
allow for organizing documents into different directories based on document type,
date, or other criteria.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.mixins.models import MatcherMixin
from paperap.models.storage_path.queryset import StoragePathQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class StoragePath(StandardModel, MatcherMixin):
    """
    Represent a storage path in Paperless-NgX.

    A storage path defines where documents are physically stored in the Paperless-NgX
    file system. Each document can be assigned to a specific storage path, allowing
    for organized file storage based on document type, date, or other criteria.

    Storage paths can also be configured with matching rules to automatically assign
    documents to specific paths based on their content or metadata.

    Attributes:
        name: The display name of the storage path.
        slug: The URL-friendly version of the name (auto-generated, read-only).
        path: The actual filesystem path where documents will be stored.
        document_count: The number of documents using this storage path (read-only).
        owner: The ID of the user who owns this storage path, if applicable.
        user_can_change: Whether the current user has permission to modify this path.

    Examples:
        Create a new storage path:
            >>> tax_path = client.storage_paths.create(
            ...     name="Tax Documents",
            ...     path="/documents/taxes/"
            ... )

        Assign a storage path to a document:
            >>> doc = client.documents.get(123)
            >>> doc.storage_path = tax_path.id
            >>> doc.save()

        Create a storage path with automatic matching:
            >>> invoice_path = client.storage_paths.create(
            ...     name="Invoices",
            ...     path="/documents/invoices/",
            ...     matching_algorithm="auto",
            ...     match="invoice bill receipt"
            ... )

    """

    name: str
    slug: str | None = None
    path: str | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        """
        Define metadata for the StoragePath model.

        This class defines metadata properties that control how the StoragePath
        model interacts with the Paperless-NgX API, including which fields are
        read-only and which QuerySet class to use for queries.

        Attributes:
            read_only_fields: Set of field names that cannot be modified by the client.
            queryset: The QuerySet class to use for this model.

        """

        read_only_fields = {"slug", "document_count"}
        queryset = StoragePathQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get all documents assigned to this storage path.

        Retrieve a queryset containing all documents that use this storage path.
        The queryset is lazy-loaded, meaning API requests are only made when the
        results are actually needed (when iterating, slicing, or calling terminal
        methods like count() or get()).

        Returns:
            DocumentQuerySet: A queryset containing all documents that use this
                storage path. The queryset can be further filtered or ordered.

        Examples:
            Get all documents in a storage path:
                >>> tax_path = client.storage_paths.get(5)
                >>> tax_docs = tax_path.documents
                >>> print(f"Found {tax_docs.count()} tax documents")

            Filter documents in a storage path:
                >>> recent_tax_docs = tax_path.documents.filter(
                ...     created__gt="2023-01-01"
                ... )
                >>> for doc in recent_tax_docs:
                ...     print(f"{doc.title} - {doc.created}")

        """
        return self._client.documents().all().storage_path_id(self.id)
