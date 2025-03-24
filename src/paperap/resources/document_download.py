"""
Module for managing document download operations in the Paperless-NgX API.

This module provides functionality for downloading documents in various formats
(original, preview, thumbnail) from a Paperless-NgX server. It handles the API
requests, response parsing, and content extraction for document downloads.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document.download import DownloadedDocument, DownloadedDocumentQuerySet, RetrieveFileMode
from paperap.resources.base import BaseResource, StandardResource


class DownloadedDocumentResource(StandardResource[DownloadedDocument, DownloadedDocumentQuerySet]):
    """
    Resource for managing downloaded document content from Paperless-NgX.

    This resource handles retrieving document files in various formats (original,
    preview, thumbnail) from the Paperless-NgX API. It provides methods to load
    binary content and associated metadata for documents.

    Attributes:
        model_class: The DownloadedDocument model class used by this resource.
        queryset_class: The DownloadedDocumentQuerySet class for query operations.
        name: The resource name used in API endpoints.
        endpoints: Mapping of retrieval modes to their corresponding API endpoints.

    """

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

        This method fetches the binary content of the document file from the Paperless-NgX
        API and updates the model with the response data. It handles different retrieval
        modes (download, preview, thumbnail) and parses response headers to extract
        metadata such as content type and filename.

        Args:
            downloaded_document: The DownloadedDocument model to load content for.
                This model will be updated with the fetched content and metadata.

        Raises:
            ResourceNotFoundError: If the document cannot be retrieved from the API.

        Example:
            # Get a document reference
            doc = client.documents.get(123)

            # Create a download request
            download = client.document_downloads.create(
                id=doc.id,
                mode=RetrieveFileMode.DOWNLOAD,
                original=True
            )

            # Load the actual content
            client.document_downloads.load(download)

            # Now download.content contains the binary data
            with open("my_document.pdf", "wb") as f:
                f.write(download.content)

        """
        mode = downloaded_document.mode or RetrieveFileMode.DOWNLOAD
        endpoint = self.get_endpoint(mode)

        params = {
            "original": "true" if downloaded_document.original else "false",
        }

        if not (response := self.client.request_raw("GET", endpoint, params=params, data=None)):
            raise ResourceNotFoundError(f"Unable to retrieve downloaded document {downloaded_document.id}")

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
