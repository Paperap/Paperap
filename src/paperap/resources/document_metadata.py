"""
Provide resources for interacting with document metadata in the Paperless-NgX API.

The document metadata endpoints expose additional information about documents
that isn't included in standard document responses, such as detailed OCR text,
archive metadata, and system-level information.

Classes:
    DocumentMetadataResource: Resource for retrieving and managing document metadata.

Exceptions:
    ResourceNotFoundError: Raised when requested metadata is not found.
    APIError: Raised when the API returns an error response.
    BadResponseError: Raised when the API response cannot be parsed.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document.metadata import DocumentMetadata, DocumentMetadataQuerySet
from paperap.resources.base import BaseResource, StandardResource


class DocumentMetadataResource(StandardResource[DocumentMetadata, DocumentMetadataQuerySet]):
    """
    Manage document metadata in Paperless-NgX.

    Provides methods to interact with document metadata API endpoints,
    allowing retrieval of extended metadata associated with documents. Document metadata
    includes information such as OCR text, archive metadata, and system-level details
    that aren't included in standard document responses.

    Unlike most resources, DocumentMetadataResource uses a specialized endpoint
    structure that retrieves metadata for a specific document by ID.

    Attributes:
        model_class (Type[DocumentMetadata]): The model class for document metadata.
        queryset_class (Type[DocumentMetadataQuerySet]): The queryset class for metadata queries.
        name (str): The resource name identifier.
        endpoints (dict): Mapping of endpoint names to their URL patterns.

    Example:
        >>> client = PaperlessClient()
        >>> metadata_resource = client.document_metadata
        >>> # or directly
        >>> metadata_resource = DocumentMetadataResource(client)

    """

    model_class = DocumentMetadata
    queryset_class = DocumentMetadataQuerySet
    name: str = "document_metadata"
    endpoints = {
        # Override the detail endpoint to point to metadata
        "detail": URLS.meta,
    }

    def get_metadata(self, document_id: int) -> DocumentMetadata:
        """
        Retrieve metadata for a specific document.

        Fetches extended metadata for a document that isn't included
        in the standard document response, such as detailed OCR text, archive
        metadata, and system-level information.

        Args:
            document_id (int): The ID of the document for which to retrieve metadata.

        Returns:
            DocumentMetadata: A model containing the document's metadata.

        Raises:
            ResourceNotFoundError: If the document or its metadata doesn't exist.
            APIError: If the API returns an error response.
            BadResponseError: If the API response cannot be parsed.

        Example:
            >>> client = PaperlessClient()
            >>> metadata = client.document_metadata.get_metadata(123)
            >>> print(f"Original filename: {metadata.original_filename}")
            >>> print(f"Archive Size: {metadata.archive_size} bytes")

        """
        url = self.get_endpoint("detail", pk=document_id)
        response = self.client.request("GET", url)
        if not response:
            raise ResourceNotFoundError(f"Metadata for document {document_id} not found", self.name)
        return self.parse_to_model(response)
