"""
Document enrichment services.

This package provides services for enriching documents with descriptions,
summaries, and other metadata using language models.
"""

from paperap.services.enrichment.service import (
    DocumentEnrichmentService,
    TEMPLATE_DIR_ENV,
    ACCEPTED_IMAGE_FORMATS,
    OPENAI_ACCEPTED_FORMATS,
    DEFAULT_TEMPLATES_PATH,
)

__all__ = [
    "DocumentEnrichmentService",
    "TEMPLATE_DIR_ENV",
]
