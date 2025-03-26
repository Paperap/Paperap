"""
Document enrichment service using LLMs.

This module provides the core functionality for enriching documents with
descriptions, summaries, and other metadata using LLMs.

Services in this module can be used directly or through DocumentQuerySet methods
like `describe()`, `summarize()`, and `analyze()`.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict
from paperap.models.document import Document


class EnrichmentResult(BaseModel):
    """
    Result of a document enrichment operation.

    Attributes:
        document: The enriched document
        raw_response: The raw response from the enrichment service
        parsed_response: The parsed response as a dictionary
        success: Whether the enrichment was successful
        error: Error message if the enrichment failed

    """

    document: Document
    raw_response: str | None = None
    parsed_response: dict[str, Any] | None = None
    success: bool = True
    error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
