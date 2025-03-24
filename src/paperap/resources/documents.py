"""
Document resource module for interacting with Paperless-NgX document API.

This module provides classes for managing documents and document notes in a Paperless-NgX
system. It includes functionality for uploading, downloading, and manipulating documents,
as well as performing bulk operations on multiple documents.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Any, Iterator, override

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document import Document, DocumentNote, DocumentNoteQuerySet, DocumentQuerySet
from paperap.models.task import Task
from paperap.resources.base import BaseResource, StandardResource
from paperap.signals import registry

if TYPE_CHECKING:
    from paperap.models import Correspondent, DocumentType, StoragePath

logger = logging.getLogger(__name__)


class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """
    Resource for managing documents in Paperless-NgX.

    This class provides methods for interacting with the documents API endpoint,
    including uploading, downloading, and manipulating documents, as well as
    performing bulk operations on multiple documents.

    Attributes:
        model_class: The Document model class.
        queryset_class: The DocumentQuerySet class for query operations.
        name: The resource name used in API endpoints.
        endpoints: Dictionary mapping endpoint names to URL templates.

    """

    model_class = Document
    queryset_class = DocumentQuerySet
    name = "documents"
    endpoints = {
        "list": URLS.list,
        "detail": URLS.detail,
        "create": URLS.create,
        "update": URLS.update,
        "delete": URLS.delete,
        "download": URLS.download,
        "preview": URLS.preview,
        "thumbnail": URLS.thumbnail,
        # The upload endpoint does not follow the standard pattern, so we define it explicitly.
        "upload": Template("/api/documents/post_document/"),
        "next_asn": URLS.next_asn,
        "empty_trash": Template("/api/trash/empty/"),
    }

    def download(self, document_id: int, *, original: bool = False) -> bytes:
        """
        Download a document's file content.

        Args:
            document_id: The ID of the document to download.
            original: If True, download the original document file. If False,
                download the archived version.

        Returns:
            The document's file content as bytes.

        Raises:
            ResourceNotFoundError: If the document download fails.

        Example:
            >>> content = client.documents.download(123)
            >>> with open("document.pdf", "wb") as f:
            ...     f.write(content)

        """
        url = self.get_endpoint("download", pk=document_id)
        params = {"original": str(original).lower()}
        # Request raw bytes by setting json_response to False
        response = self.client.request("GET", url, params=params, json_response=False)
        if not response:
            raise ResourceNotFoundError(f"Document {document_id} download failed", self.name)
        return response

    def preview(self, document_id: int) -> bytes:
        """
        Download a document's preview image.

        Args:
            document_id: The ID of the document to get a preview for.

        Returns:
            The document's preview image content as bytes.

        Raises:
            ResourceNotFoundError: If the document preview fails.

        Example:
            >>> preview = client.documents.preview(123)
            >>> with open("preview.png", "wb") as f:
            ...     f.write(preview)

        """
        url = self.get_endpoint("preview", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} preview failed", self.name)
        return response

    def thumbnail(self, document_id: int) -> bytes:
        """
        Download a document's thumbnail image.

        Args:
            document_id: The ID of the document to get a thumbnail for.

        Returns:
            The document's thumbnail image content as bytes.

        Raises:
            ResourceNotFoundError: If the document thumbnail retrieval fails.

        Example:
            >>> thumbnail = client.documents.thumbnail(123)
            >>> with open("thumbnail.png", "wb") as f:
            ...     f.write(thumbnail)

        """
        url = self.get_endpoint("thumbnail", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} thumbnail failed", self.name)
        return response

    def upload_async(self, filepath: Path | str, **metadata) -> str:
        """
        Upload a document from a file to Paperless-NgX asynchronously.

        This method starts an asynchronous upload process and returns a task ID
        that can be used to track the upload progress.

        Args:
            filepath: The path to the file to upload.
            **metadata: Additional metadata for the document, such as:
                title: Document title
                created: Document creation date
                correspondent: Correspondent ID
                document_type: Document type ID
                tags: List of tag IDs
                archive_serial_number: Custom reference number

        Returns:
            A UUID string (task identifier) as returned by Paperless-NgX.
            e.g. "ca6a6dc8-b434-4fcd-8436-8b2546465622"

        Raises:
            FileNotFoundError: If the file does not exist.
            ResourceNotFoundError: If the upload fails.

        Example:
            >>> task_id = client.documents.upload_async("invoice.pdf",
            ...     title="Electric Bill March 2023",
            ...     correspondent=5,
            ...     tags=[1, 2])
            >>> # Later, check the task status
            >>> task = client.tasks.get(task_id)

        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        with filepath.open("rb") as f:
            return self.upload_content(f.read(), filepath.name, **metadata)

    def upload_sync(self, filepath: Path | str, max_wait: int = 300, poll_interval: float = 1.0, **metadata) -> Document:
        """
        Upload a document and wait until it has been processed.

        This method uploads a document and blocks until processing is complete,
        returning the created Document object.

        Args:
            filepath: Path to the file to upload.
            max_wait: Maximum time (in seconds) to wait for processing.
            poll_interval: Seconds between polling attempts.
            **metadata: Additional metadata for the document, such as:
                title: Document title
                created: Document creation date
                correspondent: Correspondent ID
                document_type: Document type ID
                tags: List of tag IDs
                archive_serial_number: Custom reference number

        Returns:
            A Document instance once available.

        Raises:
            FileNotFoundError: If the file does not exist.
            APIError: If the document is not processed within the max_wait.
            BadResponseError: If document processing succeeds but no document ID is returned.

        Example:
            >>> document = client.documents.upload_sync("invoice.pdf",
            ...     title="Electric Bill March 2023",
            ...     correspondent=5,
            ...     tags=[1, 2])
            >>> print(f"Uploaded document ID: {document.id}")

        """
        task_id = self.upload_async(filepath, **metadata)
        logger.debug("Upload async complete, task id: %s", task_id)

        # Define a success callback to handle document retrieval
        def on_success(task: Task) -> None:
            if not task.related_document:
                raise BadResponseError("Document processing succeeded but no document ID was returned")

        # Wait for the task to complete
        task = self.client.tasks.wait_for_task(task_id, max_wait=max_wait, poll_interval=poll_interval, success_callback=on_success)

        if not task.related_document:
            raise BadResponseError("Document processing succeeded but no document ID was returned")

        return self.get(task.related_document)

    def upload_content(self, file_content: bytes, filename: str, **metadata) -> str:
        """
        Upload document content with optional metadata.

        This method allows uploading a document from binary content rather than a file.

        Args:
            file_content: The binary content of the file to upload.
            filename: The name of the file (used for content type detection).
            **metadata: Additional metadata for the document, such as:
                title: Document title
                created: Document creation date
                correspondent: Correspondent ID
                document_type: Document type ID
                tags: List of tag IDs
                archive_serial_number: Custom reference number

        Returns:
            A task ID string (UUID) that can be used to track the upload progress.

        Raises:
            ResourceNotFoundError: If the upload fails.

        Example:
            >>> with open("document.pdf", "rb") as f:
            ...     content = f.read()
            >>> task_id = client.documents.upload_content(content, "document.pdf",
            ...     title="Important Document")

        """
        files = {"document": (filename, file_content)}
        endpoint = self.get_endpoint("upload")
        response = self.client.request("POST", endpoint, files=files, data=metadata, json_response=True)
        if not response:
            raise ResourceNotFoundError("Document upload failed", self.name)
        return str(response)

    def next_asn(self) -> int:
        """
        Get the next available archive serial number (ASN).

        Returns:
            The next available archive serial number as an integer.

        Raises:
            APIError: If the request fails or returns invalid data.

        Example:
            >>> next_number = client.documents.next_asn()
            >>> document = client.documents.upload_sync("invoice.pdf",
            ...     archive_serial_number=next_number)

        """
        url = self.get_endpoint("next_asn")
        response = self.client.request("GET", url)
        if not response or "next_asn" not in response:
            raise APIError("Failed to retrieve next ASN")
        return response["next_asn"]

    def bulk_action(self, action: str, ids: list[int], **kwargs: Any) -> dict[str, Any]:
        """
        Perform a bulk action on multiple documents.

        This is a generic method used by specific bulk operations to perform
        actions on multiple documents at once.

        Args:
            action: The action to perform (e.g., "delete", "set_correspondent", etc.)
            ids: List of document IDs to perform the action on.
            **kwargs: Additional parameters for the action, specific to each action type.

        Returns:
            The API response as a dictionary.

        Raises:
            ConfigurationError: If the bulk edit endpoint is not defined.
            APIError: If the bulk action fails.

        Example:
            >>> response = client.documents.bulk_action(
            ...     "set_correspondent",
            ...     [123, 124, 125],
            ...     correspondent=5
            ... )

        """
        # Signal before bulk action
        signal_params = {"resource": self.name, "action": action, "ids": ids, "kwargs": kwargs}
        registry.emit("resource.bulk_action:before", "Emitted before bulk action", args=[self], kwargs=signal_params)

        # Prepare the data for the bulk action
        data = {"method": action, "documents": ids, "parameters": kwargs}

        bulk_edit_url = f"{self.client.base_url}/api/documents/bulk_edit/"
        response = self.client.request("POST", bulk_edit_url, data=data)

        # Signal after bulk action
        registry.emit(
            "resource.bulk_action:after",
            "Emitted after bulk action",
            args=[self],
            kwargs={**signal_params, "response": response},
        )

        return response or {}

    def bulk_delete(self, ids: list[int]) -> dict[str, Any]:
        """
        Delete multiple documents at once.

        Args:
            ids: List of document IDs to delete.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the bulk delete operation fails.

        Example:
            >>> response = client.documents.bulk_delete([123, 124, 125])

        """
        return self.bulk_action("delete", ids)

    def bulk_reprocess(self, ids: list[int]) -> dict[str, Any]:
        """
        Reprocess multiple documents.

        Reprocessing documents will re-run the document consumer pipeline,
        including OCR, classification, and tagging.

        Args:
            ids: List of document IDs to reprocess.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the bulk reprocess operation fails.

        Example:
            >>> response = client.documents.bulk_reprocess([123, 124])

        """
        return self.bulk_action("reprocess", ids)

    def bulk_merge(self, ids: list[int], metadata_document_id: int | None = None, delete_originals: bool = False) -> bool:
        """
        Merge multiple documents into a single document.

        Args:
            ids: List of document IDs to merge.
            metadata_document_id: Apply metadata from this document to the merged document.
                If None, metadata from the first document will be used.
            delete_originals: Whether to delete the original documents after merging.

        Returns:
            True if submitting the merge was successful.

        Raises:
            BadResponseError: If the merge action returns an unexpected response.
            APIError: If the merge action fails.

        Example:
            >>> # Merge documents 123, 124, and 125, using metadata from 123
            >>> success = client.documents.bulk_merge(
            ...     [123, 124, 125],
            ...     metadata_document_id=123,
            ...     delete_originals=True
            ... )

        """
        params = {}
        if metadata_document_id is not None:
            params["metadata_document_id"] = metadata_document_id
        if delete_originals:
            params["delete_originals"] = True

        result = self.bulk_action("merge", ids, **params)
        # Expect {'result': 'OK'}
        if not result or "result" not in result:
            raise BadResponseError(f"Merge action returned unexpected response: {result}")

        if result.get("result", None) != "OK":
            raise APIError(f"Merge action failed: {result}")
        return True

    def bulk_split(self, document_id: int, pages: list, delete_originals: bool = False) -> dict[str, Any]:
        """
        Split a document into multiple documents based on page ranges.

        Args:
            document_id: Document ID to split.
            pages: List of pages to split into separate documents. Can include
                individual pages and page ranges (e.g., [1, "2-3", 4, "5-7"]).
            delete_originals: Whether to delete the original document after splitting.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the split operation fails.

        Example:
            >>> # Split document 123 into three documents: pages 1, 2-3, and 4
            >>> response = client.documents.bulk_split(
            ...     123,
            ...     [1, "2-3", 4],
            ...     delete_originals=True
            ... )

        """
        params: dict[str, Any] = {"pages": pages}
        if delete_originals:
            params["delete_originals"] = True

        return self.bulk_action("split", [document_id], **params)

    def bulk_rotate(self, ids: list[int], degrees: int) -> dict[str, Any]:
        """
        Rotate multiple documents by a specified angle.

        Args:
            ids: List of document IDs to rotate.
            degrees: Degrees to rotate (must be 90, 180, or 270).

        Returns:
            The API response as a dictionary.

        Raises:
            ValueError: If degrees is not 90, 180, or 270.
            APIError: If the rotation operation fails.

        Example:
            >>> # Rotate documents 123 and 124 by 90 degrees
            >>> response = client.documents.bulk_rotate([123, 124], 90)

        """
        if degrees not in (90, 180, 270):
            raise ValueError("Degrees must be 90, 180, or 270")

        return self.bulk_action("rotate", ids, degrees=degrees)

    def bulk_delete_pages(self, document_id: int, pages: list[int]) -> dict[str, Any]:
        """
        Delete specific pages from a document.

        Args:
            document_id: Document ID to modify.
            pages: List of page numbers to delete (1-based indexing).

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the page deletion operation fails.

        Example:
            >>> # Delete pages 2 and 4 from document 123
            >>> response = client.documents.bulk_delete_pages(123, [2, 4])

        """
        return self.bulk_action("delete_pages", [document_id], pages=pages)

    def bulk_modify_custom_fields(
        self,
        ids: list[int],
        add_custom_fields: dict[int, Any] | None = None,
        remove_custom_fields: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Modify custom fields on multiple documents.

        Args:
            ids: List of document IDs to update.
            add_custom_fields: Dictionary mapping custom field IDs to values to add or update.
            remove_custom_fields: List of custom field IDs to remove from the documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the custom field modification fails.

        Example:
            >>> # Add/update custom fields 3 and 5, remove custom field 7
            >>> response = client.documents.bulk_modify_custom_fields(
            ...     [123, 124, 125],
            ...     add_custom_fields={3: "High Priority", 5: "2023-04-15"},
            ...     remove_custom_fields=[7]
            ... )

        """
        params: dict[str, Any] = {}
        if add_custom_fields:
            params["add_custom_fields"] = add_custom_fields
        if remove_custom_fields:
            params["remove_custom_fields"] = remove_custom_fields

        return self.bulk_action("modify_custom_fields", ids, **params)

    def bulk_modify_tags(self, ids: list[int], add_tags: list[int] | None = None, remove_tags: list[int] | None = None) -> dict[str, Any]:
        """
        Modify tags on multiple documents.

        Args:
            ids: List of document IDs to update.
            add_tags: List of tag IDs to add to the documents.
            remove_tags: List of tag IDs to remove from the documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the tag modification fails.

        Example:
            >>> # Add tags 1 and 2, remove tag 3 from multiple documents
            >>> response = client.documents.bulk_modify_tags(
            ...     [123, 124, 125],
            ...     add_tags=[1, 2],
            ...     remove_tags=[3]
            ... )

        """
        params = {}
        if add_tags:
            params["add_tags"] = add_tags
        if remove_tags:
            params["remove_tags"] = remove_tags

        return self.bulk_action("modify_tags", ids, **params)

    def bulk_add_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Add a single tag to multiple documents.

        Args:
            ids: List of document IDs to update.
            tag_id: Tag ID to add to all specified documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the tag addition fails.

        Example:
            >>> # Add tag 5 to documents 123, 124, and 125
            >>> response = client.documents.bulk_add_tag([123, 124, 125], 5)

        """
        return self.bulk_action("add_tag", ids, tag=tag_id)

    def bulk_remove_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Remove a single tag from multiple documents.

        Args:
            ids: List of document IDs to update.
            tag_id: Tag ID to remove from all specified documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the tag removal fails.

        Example:
            >>> # Remove tag 3 from documents 123, 124, and 125
            >>> response = client.documents.bulk_remove_tag([123, 124, 125], 3)

        """
        return self.bulk_action("remove_tag", ids, tag=tag_id)

    def bulk_set_correspondent(self, ids: list[int], correspondent: "Correspondent | int") -> dict[str, Any]:
        """
        Set the correspondent for multiple documents.

        Args:
            ids: List of document IDs to update.
            correspondent: Correspondent object or ID to assign to all specified documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the correspondent update fails.

        Example:
            >>> # Set correspondent 5 for documents 123, 124, and 125
            >>> response = client.documents.bulk_set_correspondent([123, 124, 125], 5)
            >>>
            >>> # Or using a correspondent object
            >>> correspondent = client.correspondents.get(5)
            >>> response = client.documents.bulk_set_correspondent([123, 124, 125], correspondent)

        """
        if not isinstance(correspondent, int):
            correspondent = correspondent.id
        return self.bulk_action("set_correspondent", ids, correspondent=correspondent)

    def bulk_set_document_type(self, ids: list[int], document_type: "DocumentType | int") -> dict[str, Any]:
        """
        Set the document type for multiple documents.

        Args:
            ids: List of document IDs to update.
            document_type: DocumentType object or ID to assign to all specified documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the document type update fails.

        Example:
            >>> # Set document type 3 for documents 123, 124, and 125
            >>> response = client.documents.bulk_set_document_type([123, 124, 125], 3)
            >>>
            >>> # Or using a document type object
            >>> doc_type = client.document_types.get(3)
            >>> response = client.documents.bulk_set_document_type([123, 124, 125], doc_type)

        """
        if not isinstance(document_type, int):
            document_type = document_type.id
        return self.bulk_action("set_document_type", ids, document_type=document_type)

    def bulk_set_storage_path(self, ids: list[int], storage_path: "StoragePath | int") -> dict[str, Any]:
        """
        Set the storage path for multiple documents.

        Args:
            ids: List of document IDs to update.
            storage_path: StoragePath object or ID to assign to all specified documents.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the storage path update fails.

        Example:
            >>> # Set storage path 4 for documents 123, 124, and 125
            >>> response = client.documents.bulk_set_storage_path([123, 124, 125], 4)
            >>>
            >>> # Or using a storage path object
            >>> path = client.storage_paths.get(4)
            >>> response = client.documents.bulk_set_storage_path([123, 124, 125], path)

        """
        if not isinstance(storage_path, int):
            storage_path = storage_path.id
        return self.bulk_action("set_storage_path", ids, storage_path=storage_path)

    def bulk_set_permissions(
        self, ids: list[int], permissions: dict[str, Any] | None = None, owner_id: int | None = None, merge: bool = False
    ) -> dict[str, Any]:
        """
        Set permissions for multiple documents.

        Args:
            ids: List of document IDs to update.
            permissions: Permissions object defining user and group permissions.
            owner_id: Owner ID to assign to the documents.
            merge: Whether to merge with existing permissions (True) or replace them (False).

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the permissions update fails.

        Example:
            >>> # Set owner to user 2 for documents 123, 124, and 125
            >>> response = client.documents.bulk_set_permissions(
            ...     [123, 124, 125],
            ...     owner_id=2,
            ...     permissions={"users": {"2": "view"}, "groups": {"1": "edit"}},
            ...     merge=True
            ... )

        """
        params: dict[str, Any] = {"merge": merge}
        if permissions:
            params["set_permissions"] = permissions
        if owner_id is not None:
            params["owner"] = owner_id

        return self.bulk_action("set_permissions", ids, **params)

    def empty_trash(self) -> dict[str, Any]:
        """
        Empty the trash, permanently deleting all documents in the trash.

        Returns:
            The API response as a dictionary.

        Raises:
            APIError: If the empty trash request fails.

        Example:
            >>> response = client.documents.empty_trash()
            >>> print("Trash emptied successfully")

        """
        endpoint = self.get_endpoint("empty_trash")
        logger.debug("Emptying trash")
        payload = {"action": "empty"}
        response = self.client.request("POST", endpoint, data=payload, json_response=True)
        if not response:
            raise APIError("Empty trash failed")
        return response  # type: ignore # request should have returned correct response TODO


class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """
    Resource for managing document notes in Paperless-NgX.

    This class provides methods for interacting with the document notes API endpoint,
    allowing creation, retrieval, updating, and deletion of notes attached to documents.

    Attributes:
        model_class: The DocumentNote model class.
        queryset_class: The DocumentNoteQuerySet class for query operations.
        name: The resource name used in API endpoints.
        endpoints: Dictionary mapping endpoint names to URL templates.

    """

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name = "notes"
    endpoints = {"list": Template("/api/document/${pk}/notes/")}
