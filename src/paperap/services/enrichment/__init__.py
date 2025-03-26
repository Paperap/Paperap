"""
Document enrichment services.

This package provides services for enriching documents with descriptions,
summaries, and other metadata using language models.
"""

from paperap.services.enrichment.service import (
    DocumentEnrichmentService,
    EnrichmentConfig,
    EnrichmentResult,
    TEMPLATE_DIR_ENV,
)

__all__ = [
    "DocumentEnrichmentService",
    "EnrichmentConfig",
    "EnrichmentResult",
    "TEMPLATE_DIR_ENV",
]
