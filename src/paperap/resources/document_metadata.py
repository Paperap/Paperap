"""




----------------------------------------------------------------------------

METADATA:

File:    document_metadata.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.8
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

from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document.metadata import DocumentMetadata, DocumentMetadataQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentMetadataResource(StandardResource[DocumentMetadata, DocumentMetadataQuerySet]):
    """Resource for managing documents."""

    model_class = DocumentMetadata
    name = "document"
