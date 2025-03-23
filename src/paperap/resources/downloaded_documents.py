

from __future__ import annotations

from paperap.models.document import DownloadedDocument, DownloadedDocumentQuerySet
from paperap.resources.base import StandardResource


class DownloadedDocumentResource(StandardResource[DownloadedDocument, DownloadedDocumentQuerySet]):
    """Resource for managing downloaded documents."""

    model_class = DownloadedDocument
    queryset_class = DownloadedDocumentQuerySet
    name: str = "downloaded_documents"
