"""




----------------------------------------------------------------------------

METADATA:

File:    document_suggestions.py
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
from paperap.models.document.suggestions import DocumentSuggestions, DocumentSuggestionsQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentSuggestionsResource(StandardResource[DocumentSuggestions, DocumentSuggestionsQuerySet]):
    model_class = DocumentSuggestions
    queryset_class = DocumentSuggestionsQuerySet
    name: str = "document_suggestions"
    endpoints = {
        # Override the detail endpoint to point to suggestions
        "detail": URLS.suggestions,
    }

    def get_suggestions(self, document_id: int) -> DocumentSuggestions:
        url = self.get_endpoint("detail", pk=document_id)
        response = self.client.request("GET", url)
        if not response:
            raise ResourceNotFoundError(f"Suggestions for document {document_id} not found", self.name)
        return self.parse_to_model(response)
