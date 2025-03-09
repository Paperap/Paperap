"""




----------------------------------------------------------------------------

   METADATA:

       File:    document_type.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.document_type.queryset import DocumentTypeQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class DocumentType(StandardModel):
    """
    Represents a document type in Paperless-NgX.

    Attributes:
        name: The name of the document type.
        slug: A unique identifier for the document type.
        match: The pattern used for matching documents.
        matching_algorithm: The algorithm used for matching.
        is_insensitive: Whether the matching is case insensitive.
        document_count: The number of documents of this type.
        owner: The owner of the document type.
        user_can_change: Whether the user can change the document type.

    Returns:
        A new instance of DocumentType.

    Examples:
        # Create a new DocumentType instance
        doc_type = DocumentType(name="Invoice", slug="invoice", match="INV-*")
    """

    name: str
    slug: str | None = None
    match: str | None = None
    matching_algorithm: int | None = None
    is_insensitive: bool
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = DocumentTypeQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents with this document type.

        Returns:
            A DocumentQuerySet containing documents of this type.

        Examples:
            # Get all documents of this type
            documents = doc_type.documents
        Get documents with this document type.
        """
        return self._client.documents().all().document_type_id(self.id)
