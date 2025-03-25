"""
Document suggestions queryset module for interacting with document suggestions API.

This module provides the queryset implementation for document suggestions in Paperless-NgX,
allowing for efficient querying and filtering of document suggestions data.
Document suggestions are recommendations provided by Paperless-NgX for document metadata
such as correspondents, document types, and tags based on document content analysis.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.suggestions.model import DocumentSuggestions

logger = logging.getLogger(__name__)


class DocumentSuggestionsQuerySet(StandardQuerySet["DocumentSuggestions"]):
    """
    QuerySet for interacting with document suggestions in Paperless-NgX.

    This class extends StandardQuerySet to provide specialized functionality for
    retrieving and filtering document suggestions. Document suggestions are
    recommendations for metadata (correspondents, document types, tags) that
    Paperless-NgX generates based on document content analysis.

    The queryset is lazy-loaded, meaning API requests are only made when data
    is actually accessed, improving performance when working with large datasets.

    Examples:
        >>> # Get all suggestions for a document
        >>> suggestions = client.document_suggestions.filter(document=123)
        >>>
        >>> # Get suggestions with high confidence scores
        >>> high_confidence = client.document_suggestions.filter(
        ...     document=123,
        ...     confidence__gte=0.8
        ... )

    """

    pass
