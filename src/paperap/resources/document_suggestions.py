"""




----------------------------------------------------------------------------

METADATA:

File:    document_suggestions.py
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
from paperap.models.document.suggestions import DocumentSuggestions, DocumentSuggestionsQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentSuggestionsResource(StandardResource[DocumentSuggestions, DocumentSuggestionsQuerySet]):
    """Resource for managing documents."""

    model_class = DocumentSuggestions
    name = "document"
