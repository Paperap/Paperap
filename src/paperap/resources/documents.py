"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
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
from string import Template
from typing import Any, Iterator, override

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document import Document, DocumentNote, DocumentNoteQuerySet, DocumentQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """Resource for managing documents."""

    model_class = Document
    queryset_class = DocumentQuerySet
    name = "documents"
    endpoints = {
        "list": URLS.list,
        "detail": URLS.detail,
        "create": URLS.create,
        "update": URLS.update,
        "delete": URLS.delete,
        "download": URLS.download,
        "preview": URLS.preview,
        "thumbnail": URLS.thumbnail,
        # The upload endpoint does not follow the standard pattern, so we define it explicitly.
        "upload": Template("/api/document/post_document/"),
        "next_asn": URLS.next_asn,
    }

    def download(self, document_id: int, *, original: bool = False) -> bytes:
        url = self.get_endpoint("download", pk=document_id)
        params = {"original": str(original).lower()}
        # Request raw bytes by setting json_response to False
        response = self.client.request("GET", url, params=params, json_response=False)
        if not response:
            raise ResourceNotFoundError(f"Document {document_id} download failed", self.name)
        return response

    def preview(self, document_id: int) -> bytes:
        url = self.get_endpoint("preview", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} preview failed", self.name)
        return response

    def thumbnail(self, document_id: int) -> bytes:
        url = self.get_endpoint("thumbnail", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} thumbnail failed", self.name)
        return response

    def upload(self, filepath: Path | str, **metadata) -> str:
        """
        Upload a document from a file to paperless ngx.

        Args:
            filepath: The path to the file to upload.

        Returns:
            A string that looks like this: ca6a6dc8-b434-4fcd-8436-8b2546465622
            This is likely a task id, or similar.

        Raises:
            FileNotFoundError: If the file does not exist.
            ResourceNotFoundError: If the upload fails.

        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        with filepath.open("rb") as f:
            return self.upload_content(f.read(), filepath.name, **metadata)

    def upload_content(self, file_content: bytes, filename: str, **metadata) -> str:
        """
        Upload a document with optional metadata.

        Args:
            file_content: The binary content of the file to upload
            filename: The name of the file
            **metadata: Additional metadata to include with the upload

        Returns:
            A string that looks like this: ca6a6dc8-b434-4fcd-8436-8b2546465622
            This is likely a task id, or similar.

        Raises:
            ResourceNotFoundError: If the upload fails

        """
        files = {"document": (filename, file_content)}
        endpoint = self.get_endpoint("upload")
        response = self.client.request("POST", endpoint, files=files, data=metadata, json_response=True)
        if not response:
            raise ResourceNotFoundError("Document upload failed", self.name)
        return str(response)


    def next_asn(self) -> int:
        url = self.get_endpoint("next_asn")
        response = self.client.request("GET", url)
        if not response or "next_asn" not in response:
            raise APIError("Failed to retrieve next ASN")
        return response["next_asn"]

class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name = "notes"
    endpoints = {"list": Template("/api/document/${pk}/notes/")}
