

from __future__ import annotations

from paperap.models.document_type import DocumentType, DocumentTypeQuerySet
from paperap.resources.base import BaseResource, BulkEditing, StandardResource


class DocumentTypeResource(StandardResource[DocumentType, DocumentTypeQuerySet], BulkEditing):
    """Resource for managing document types."""

    model_class = DocumentType
    queryset_class = DocumentTypeQuerySet
    name: str = "document_types"
