"""
Document type model for Paperless-NgX.

This module provides the DocumentType model class for interacting with document types
in a Paperless-NgX instance. Document types are used to categorize documents and can
be configured with matching rules for automatic classification.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.document_type.queryset import DocumentTypeQuerySet
from paperap.models.mixins.models import MatcherMixin

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class DocumentType(StandardModel, MatcherMixin):
    """
    Represents a document type in Paperless-NgX.

    Document types are used to categorize documents and can be configured with
    matching rules for automatic classification of new documents during consumption.

    The MatcherMixin provides functionality for pattern matching against document
    content or metadata.

    Attributes:
        name (str): The name of the document type.
        slug (str, optional): A unique identifier for the document type,
            auto-generated from name if not provided.
        match (str, optional): The pattern used for matching documents.
            Only available when using the MatcherMixin methods.
        matching_algorithm (MatchingAlgorithmType, optional): The algorithm used for matching.
            Only available when using the MatcherMixin methods.
        is_insensitive (bool, optional): Whether the matching is case insensitive.
            Only available when using the MatcherMixin methods.
        document_count (int): The number of documents of this type (read-only).
        owner (int, optional): The ID of the user who owns this document type.
        user_can_change (bool, optional): Whether the current user can modify this document type.

    Examples:
        Create a new document type:

        >>> doc_type = client.document_types.create(
        ...     name="Invoice",
        ...     matching_algorithm="auto",
        ...     match="invoice"
        ... )

        Update an existing document type:

        >>> doc_type = client.document_types.get(1)
        >>> doc_type.name = "Receipt"
        >>> doc_type.save()

    """

    name: str
    slug: str | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        """
        Metadata for the DocumentType model.

        Defines read-only fields and the associated queryset class.
        """

        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = DocumentTypeQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get all documents associated with this document type.

        Returns:
            DocumentQuerySet: A queryset containing all documents that have
                this document type assigned.

        Examples:
            Get all documents of this type:

            >>> documents = doc_type.documents
            >>> for doc in documents:
            ...     print(doc.title)

            Filter documents of this type:

            >>> recent_docs = doc_type.documents.filter(created__gt="2023-01-01")

        """
        return self._client.documents().all().document_type_id(self.id)
