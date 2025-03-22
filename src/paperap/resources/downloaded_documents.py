"""
----------------------------------------------------------------------------

   METADATA:

       File:    downloaded_documents.py
        Project: paperap
       Created: 2025-03-21
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-21     By Jess Mann

"""

from __future__ import annotations

from paperap.models.document import DownloadedDocument, DownloadedDocumentQuerySet
from paperap.resources.base import StandardResource


class DownloadedDocumentResource(StandardResource[DownloadedDocument, DownloadedDocumentQuerySet]):
    """Resource for managing downloaded documents."""

    model_class = DownloadedDocument
    queryset_class = DownloadedDocumentQuerySet
    name: str = "downloaded_documents"
