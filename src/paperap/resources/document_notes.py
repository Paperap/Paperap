

from __future__ import annotations

from paperap.models.document import DocumentNote, DocumentNoteQuerySet
from paperap.resources.base import StandardResource


class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name: str = "document_notes"
