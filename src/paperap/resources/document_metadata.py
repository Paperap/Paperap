"""




----------------------------------------------------------------------------

METADATA:

File:    document_metadata.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document.metadata import DocumentMetadata, DocumentMetadataQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentMetadataResource(StandardResource[DocumentMetadata, DocumentMetadataQuerySet]):
    model_class = DocumentMetadata
    queryset_class = DocumentMetadataQuerySet
    name: str = "document_metadata"
    endpoints = {
        # Override the detail endpoint to point to metadata
        "detail": URLS.meta,
    }

    def get_metadata(self, document_id: int) -> DocumentMetadata:
        url = self.get_endpoint("detail", pk=document_id)
        response = self.client.request("GET", url)
        if not response:
            raise ResourceNotFoundError(f"Metadata for document {document_id} not found", self.name)
        return self.parse_to_model(response)
