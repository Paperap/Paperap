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
    """Resource for managing downloaded document content."""

    model_class = DownloadedDocument
    queryset_class = DownloadedDocumentQuerySet
    name = "document"
    endpoints = {
        RetrieveFileMode.PREVIEW: URLS.preview,
        RetrieveFileMode.THUMBNAIL: URLS.thumbnail,
        RetrieveFileMode.DOWNLOAD: URLS.download,
    }

    def load(self, downloaded_document: "DownloadedDocument") -> None:
        """
        Load the document file content from the API.

        This method fetches the binary content of the document file
        and updates the model with the response data.
        """
        mode = downloaded_document.mode or RetrieveFileMode.DOWNLOAD
        endpoint = self.endpoints[mode]

        params = {
            "original": "true" if downloaded_document.original else "false",
        }

        if not (response := self.client.request_raw("GET", endpoint, params=params, data=None)):
            raise ResourceNotFoundError(f"Unable to retrieve downloaded docuyment {downloaded_document.id}")

        content = response.content
        content_type = response.headers.get("Content-Type")
        content_disposition = response.headers.get("Content-Disposition")
        disposition_filename = None
        disposition_type = None

        # Parse Content-Disposition header
        if content_disposition:
            parts = content_disposition.split(";")
            disposition_type = parts[0].strip()

            for part in parts[1:]:
                if "filename=" in part:
                    filename_part = part.strip()
                    disposition_filename = filename_part.split("=", 1)[1].strip("\"'")

        # Update model
        downloaded_document.update_locally(
            from_db=True,
            content=content,
            content_type=content_type,
            disposition_filename=disposition_filename,
            disposition_type=disposition_type,
        )
