"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.8
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document.download import DownloadedDocument, DownloadedDocumentQuerySet, RetrieveFileMode
from paperap.resources.base import BaseResource, StandardResource


class DownloadedDocumentResource(StandardResource[DownloadedDocument, DownloadedDocumentQuerySet]):
    """Resource for managing documents."""

    model_class = DownloadedDocument
    name = "downloaded_documents"

    def load(self, downloaded_document : "DownloadedDocument") -> None:
        """
        Load the document file content from the API.

        This method fetches the binary content of the document file
        and updates the model with the response data.
        """
        endpoint = URLS.download
        if downloaded_document.mode == RetrieveFileMode.PREVIEW:
            endpoint = URLS.preview
        elif downloaded_document.mode == RetrieveFileMode.THUMBNAIL:
            endpoint = URLS.thumbnail

        params = {
            "original": "true" if downloaded_document.original else "false",
        }

        response = self.client.request(
            "GET",
            endpoint,
            params=params,
            json_response=False
        )

        self.content = response.content
        self.content_type = response.headers.get("Content-Type")

        content_disposition = response.headers.get("Content-Disposition")
        if content_disposition:
            # Parse Content-Disposition header
            parts = content_disposition.split(";")
            self.disposition_type = parts[0].strip()

            for part in parts[1:]:
                if "filename=" in part:
                    filename_part = part.strip()
                    self.disposition_filename = filename_part.split("=", 1)[1].strip('"\'')
