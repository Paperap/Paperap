"""
----------------------------------------------------------------------------

   METADATA:

       File:    document_notes.py
        Project: paperap
       Created: 2025-03-21
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-21     By Jess Mann

"""

from __future__ import annotations

from paperap.models.document import DocumentNote, DocumentNoteQuerySet
from paperap.resources.base import StandardResource


class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name: str = "document_notes"
