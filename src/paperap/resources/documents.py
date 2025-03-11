"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator, Optional, override

from typing_extensions import TypeVar

from paperap.exceptions import APIError, BadResponseError
from paperap.models.document import Document, DocumentNote, DocumentQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """Resource for managing documents."""

    model_class = Document
    name = "documents"


class DocumentNoteResource(StandardResource[DocumentNote]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    name = "document_notes"
