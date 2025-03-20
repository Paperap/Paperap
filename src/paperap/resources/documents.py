"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.8
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional, override

from typing_extensions import TypeVar

from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document import Document, DocumentNote, DocumentNoteQuerySet, DocumentQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """Resource for managing documents."""

    model_class = Document
    queryset_class = DocumentQuerySet
    name = "documents"

    def download(self, document_id: int, *, original: bool = False) -> bytes | None:
        url = f"documents/{document_id}/download"
        params = {"original": str(original).lower()}
        response = self.client.request("GET", url, params=params)
        if not response:
            raise ResourceNotFoundError(f"Document {document_id} download failed", self.name)
        return response.get("content")

    def upload(self, filepath : Path | str) -> Document:
        """
        Upload a document from a file to paperless ngx.

        Args:
            filepath: The path to the file to upload.

        Returns:
            The uploaded document.

        Raises:
            FileNotFoundError: If the file does not exist.
            ResourceNotFoundError: If the upload fails.

        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)

        with filepath.open("rb") as f:
            return self.upload_content(f.read(), filepath.name)

    def upload_content(self, file_content: bytes, filename: str, **metadata) -> Document:
        """Upload a document with optional metadata."""
        files = {"document": (filename, file_content)}
        response = self.client.request("POST", "documents/post_document/", files=files, data=metadata)
        if not response:
            raise ResourceNotFoundError("Document upload failed")
        return self.parse_to_model(response)



class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name = "document_notes"
