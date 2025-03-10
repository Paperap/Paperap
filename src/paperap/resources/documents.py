"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import os.path
from datetime import datetime
from typing import Any, BinaryIO, Iterator, Optional, override

from typing_extensions import TypeVar

from paperap.exceptions import APIError, BadResponseError
from paperap.models.document import Document, DocumentNote, DocumentQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """Resource for managing documents."""

    model_class = Document
    name = "documents"

    """
    # Untested functionality
    def upload(
        self,
        file_path: str,
        title: str | None = None,
        correspondent: int | None = None,
        document_type: int | None = None,
        tags: Optional[list[int]] = None,
    ) -> Document:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            return self.upload_fileobj(
                f,
                filename,
                title=title or os.path.splitext(filename)[0],
                correspondent=correspondent,
                document_type=document_type,
                tags=tags,
            )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        filename: str,
        title: str | None = None,
        correspondent: int | None = None,
        document_type: int | None = None,
        tags: Optional[list[int]] = None,
    ) -> Document:
        data: dict[str, Any] = {}
        if title:
            data["title"] = title
        if correspondent:
            data["correspondent"] = correspondent
        if document_type:
            data["document_type"] = document_type
        if tags:
            data["tags"] = tags

        files = {"document": (filename, fileobj, "application/octet-stream")}

        if not (
            response := self.client.request(
                "POST",
                "documents/post_document/",
                data=data,
                files=files,
            )
        ):
            raise BadResponseError("Failed to upload document")

        return Document.from_dict(response)

    def download(self, document_id: int, original: bool = False) -> bytes:
        endpoint = f"documents/{document_id}/{'download/' if original else 'preview/'}"
        response = self.client.session.get(
            f"{self.client.base_url}{endpoint}",
            headers=self.client._get_headers(),
            **self.client._get_auth_params(),
        )
        response.raise_for_status()
        return response.content

    def search(self, query: str) -> DocumentQuerySet:
        return self.all().filter(query=query)
    """

class DocumentNoteResource(StandardResource[DocumentNote]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    name = "document_notes"
