"""Document enrichment services for Paperap.

This package provides services for enriching documents with descriptions,
summaries, and other metadata using LLMs and other tools.
"""

from paperap.services.enrichment.service import DocumentEnrichmentService, EnrichmentConfig

__all__ = [
    "DocumentEnrichmentService",
    "EnrichmentConfig",
]
