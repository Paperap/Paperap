"""
Document suggestions resource for the Paperless-NgX API.

This module provides the DocumentSuggestionsResource class, which is responsible for
interacting with the document suggestions endpoint of the Paperless-NgX API. Document
suggestions are recommendations for metadata (such as correspondents, document types,
and tags) that Paperless-NgX generates based on document content analysis.

The resource extends StandardResource to provide specific functionality for retrieving
document suggestions by document ID.

Example:
    >>> suggestions = client.document_suggestions.get_suggestions(document_id=123)
    >>> print(f"Suggested correspondent: {suggestions.correspondent_id}")
    >>> print(f"Suggested tags: {suggestions.tags}")

"""

from __future__ import annotations

from typing import Any

from paperap.const import URLS
from paperap.exceptions import ResourceNotFoundError
from paperap.models.document.suggestions import DocumentSuggestions, DocumentSuggestionsQuerySet
from paperap.resources.base import StandardResource


class DocumentSuggestionsResource(StandardResource[DocumentSuggestions, DocumentSuggestionsQuerySet]):
    """
    Resource class for managing document suggestions in Paperless-NgX.

    This class provides methods to interact with the document suggestions endpoint
    of the Paperless-NgX API. Document suggestions are AI-generated recommendations
    for metadata fields like correspondent, document type, and tags based on the
    document's content.

    The resource primarily offers the get_suggestions method to retrieve suggestions
    for a specific document by its ID.

    Attributes:
        queryset_class (type): The queryset class for document suggestions.
        name (str): The name of the resource used in API paths.
        endpoints (dict): A dictionary mapping endpoint names to their URLs.

    Note:
        This resource overrides the standard detail endpoint to point to the
        suggestions endpoint in the Paperless-NgX API.

    Example:
        >>> suggestions = client.document_suggestions.get_suggestions(document_id=123)
        >>> if suggestions.correspondent_id:
        ...     correspondent = client.correspondents.get(suggestions.correspondent_id)
        ...     print(f"Suggested correspondent: {correspondent.name}")

    """

    model_class = DocumentSuggestions
    queryset_class = DocumentSuggestionsQuerySet
    name: str = "document_suggestions"
    endpoints = {
        # Override the detail endpoint to point to suggestions
        "detail": URLS.suggestions,
    }

    def get_suggestions(self, document_id: int) -> DocumentSuggestions:
        """
        Retrieve document suggestions for a specific document ID.

        This method sends a GET request to the document suggestions endpoint to
        retrieve AI-generated metadata suggestions for the specified document.
        These suggestions typically include correspondent, document type, storage path,
        and tags that Paperless-NgX thinks are appropriate for the document based on
        its content analysis.

        Args:
            document_id: The ID of the document for which to retrieve suggestions.

        Returns:
            A DocumentSuggestions model containing the suggested metadata for the document.

        Raises:
            ResourceNotFoundError: If the document with the specified ID doesn't exist
                or if suggestions cannot be generated for it.
            APIError: If the API returns an error response.
            ConnectionError: If there's a network issue connecting to the Paperless-NgX server.

        Example:
            >>> suggestions = client.document_suggestions.get_suggestions(document_id=123)
            >>>
            >>> # Apply suggestions to the document
            >>> doc = client.documents.get(123)
            >>> if suggestions.correspondent_id:
            ...     doc.correspondent = suggestions.correspondent_id
            >>> if suggestions.document_type_id:
            ...     doc.document_type = suggestions.document_type_id
            >>> if suggestions.tags:
            ...     doc.tags = suggestions.tags
            >>> doc.save()

        """
        url = self.get_endpoint("detail", pk=document_id)
        response = self.client.request("GET", url)
        if not response:
            raise ResourceNotFoundError(f"Suggestions for document {document_id} not found", self.name)
        return self.parse_to_model(response)
