"""
----------------------------------------------------------------------------

   METADATA:

       File:    documents.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Iterator, override

from typing_extensions import TypeVar

from paperap.const import URLS
from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.document import Document, DocumentNote, DocumentNoteQuerySet, DocumentQuerySet
from paperap.resources.base import BaseResource, StandardResource
from paperap.signals import registry

logger = logging.getLogger(__name__)

class DocumentResource(StandardResource[Document, DocumentQuerySet]):
    """Resource for managing documents."""

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
        url = self.get_endpoint("download", pk=document_id)
        params = {"original": str(original).lower()}
        # Request raw bytes by setting json_response to False
        response = self.client.request("GET", url, params=params, json_response=False)
        if not response:
            raise ResourceNotFoundError(f"Document {document_id} download failed", self.name)
        return response

    def preview(self, document_id: int) -> bytes:
        url = self.get_endpoint("preview", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} preview failed", self.name)
        return response

    def thumbnail(self, document_id: int) -> bytes:
        url = self.get_endpoint("thumbnail", pk=document_id)
        response = self.client.request("GET", url, json_response=False)
        if response is None:
            raise ResourceNotFoundError(f"Document {document_id} thumbnail failed", self.name)
        return response

    def upload(self, filepath: Path | str, **metadata) -> str:
        """
        Upload a document from a file to paperless ngx.

        Args:
            filepath: The path to the file to upload.

        Returns:
            A string that looks like this: ca6a6dc8-b434-4fcd-8436-8b2546465622
            This is likely a task id, or similar.

        Raises:
            FileNotFoundError: If the file does not exist.
            ResourceNotFoundError: If the upload fails.

        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        with filepath.open("rb") as f:
            return self.upload_content(f.read(), filepath.name, **metadata)

    def upload_content(self, file_content: bytes, filename: str, **metadata) -> str:
        """
        Upload a document with optional metadata.

        Args:
            file_content: The binary content of the file to upload
            filename: The name of the file
            **metadata: Additional metadata to include with the upload

        Returns:
            A string that looks like this: ca6a6dc8-b434-4fcd-8436-8b2546465622
            This is likely a task id, or similar.

        Raises:
            ResourceNotFoundError: If the upload fails

        """
        files = {"document": (filename, file_content)}
        endpoint = self.get_endpoint("upload")
        response = self.client.request("POST", endpoint, files=files, data=metadata, json_response=True)
        if not response:
            raise ResourceNotFoundError("Document upload failed", self.name)
        return str(response)


    def next_asn(self) -> int:
        url = self.get_endpoint("next_asn")
        response = self.client.request("GET", url)
        if not response or "next_asn" not in response:
            raise APIError("Failed to retrieve next ASN")
        return response["next_asn"]

    def bulk_action(self, action: str, ids: list[int], **kwargs: Any) -> dict[str, Any]:
        """
        Perform a bulk action on multiple documents.

        Args:
            action: The action to perform (e.g., "delete", "set_correspondent", etc.)
            ids: List of document IDs to perform the action on
            **kwargs: Additional parameters for the action

        Returns:
            The API response

        Raises:
            ConfigurationError: If the bulk edit endpoint is not defined

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
            ids: List of document IDs to delete

        Returns:
            The API response

        """
        return self.bulk_action("delete", ids)

    def bulk_reprocess(self, ids: list[int]) -> dict[str, Any]:
        """
        Reprocess multiple documents.

        Args:
            ids: List of document IDs to reprocess

        Returns:
            The API response

        """
        return self.bulk_action("reprocess", ids)

    def bulk_merge(
        self, ids: list[int], metadata_document_id: int = None, delete_originals: bool = False
    ) -> dict[str, Any]:
        """
        Merge multiple documents.

        Args:
            ids: List of document IDs to merge
            metadata_document_id: Apply metadata from this document to the merged document
            delete_originals: Whether to delete the original documents after merging

        Returns:
            The API response

        """
        params = {}
        if metadata_document_id is not None:
            params["metadata_document_id"] = metadata_document_id
        if delete_originals:
            params["delete_originals"] = True

        return self.bulk_action("merge", ids, **params)

    def bulk_split(self, document_id: int, pages: list, delete_originals: bool = False) -> dict[str, Any]:
        """
        Split a document.

        Args:
            document_id: Document ID to split
            pages: List of pages to split (can include ranges, e.g. "[1,2-3,4,5-7]")
            delete_originals: Whether to delete the original document after splitting

        Returns:
            The API response

        """
        params : dict[str, Any] = {"pages": pages}
        if delete_originals:
            params["delete_originals"] = True

        return self.bulk_action("split", [document_id], **params)

    def bulk_rotate(self, ids: list[int], degrees: int) -> dict[str, Any]:
        """
        Rotate documents.

        Args:
            ids: List of document IDs to rotate
            degrees: Degrees to rotate (must be 90, 180, or 270)

        Returns:
            The API response

        """
        if degrees not in (90, 180, 270):
            raise ValueError("Degrees must be 90, 180, or 270")

        return self.bulk_action("rotate", ids, degrees=degrees)

    def bulk_delete_pages(self, document_id: int, pages: list[int]) -> dict[str, Any]:
        """
        Delete pages from a document.

        Args:
            document_id: Document ID
            pages: List of page numbers to delete

        Returns:
            The API response

        """
        return self.bulk_action("delete_pages", [document_id], pages=pages)

    def bulk_modify_custom_fields(
        self, ids: list[int], add_custom_fields: dict[int, Any] = None, remove_custom_fields: list[int] = None
    ) -> dict[str, Any]:
        """
        Modify custom fields on multiple documents.

        Args:
            ids: List of document IDs to update
            add_custom_fields: Dictionary of custom field ID to value pairs to add
            remove_custom_fields: List of custom field IDs to remove

        Returns:
            The API response

        """
        params = {}
        if add_custom_fields:
            params["add_custom_fields"] = add_custom_fields
        if remove_custom_fields:
            params["remove_custom_fields"] = remove_custom_fields

        return self.bulk_action("modify_custom_fields", ids, **params)

    def bulk_modify_tags(
        self, ids: list[int],
        add_tags: list[int] = None,
        remove_tags: list[int] = None
    ) -> dict[str, Any]:
        """
        Modify tags on multiple documents.

        Args:
            ids: List of document IDs to update
            add_tags: List of tag IDs to add
            remove_tags: List of tag IDs to remove

        Returns:
            The API response

        """
        params = {}
        if add_tags:
            params["add_tags"] = add_tags
        if remove_tags:
            params["remove_tags"] = remove_tags

        return self.bulk_action("modify_tags", ids, **params)

    def bulk_add_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Add a tag to multiple documents.

        Args:
            ids: List of document IDs to update
            tag_id: Tag ID to add

        Returns:
            The API response

        """
        return self.bulk_action("add_tag", ids, tag=tag_id)

    def bulk_remove_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Remove a tag from multiple documents.

        Args:
            ids: List of document IDs to update
            tag_id: Tag ID to remove

        Returns:
            The API response

        """
        return self.bulk_action("remove_tag", ids, tag=tag_id)

    def bulk_set_correspondent(self, ids: list[int], correspondent_id: int) -> dict[str, Any]:
        """
        Set correspondent for multiple documents.

        Args:
            ids: List of document IDs to update
            correspondent_id: Correspondent ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_correspondent", ids, correspondent=correspondent_id)

    def bulk_set_document_type(self, ids: list[int], document_type_id: int) -> dict[str, Any]:
        """
        Set document type for multiple documents.

        Args:
            ids: List of document IDs to update
            document_type_id: Document type ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_document_type", ids, document_type=document_type_id)

    def bulk_set_storage_path(self, ids: list[int], storage_path_id: int) -> dict[str, Any]:
        """
        Set storage path for multiple documents.

        Args:
            ids: List of document IDs to update
            storage_path_id: Storage path ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_storage_path", ids, storage_path=storage_path_id)

    def bulk_set_permissions(
        self, ids: list[int], permissions: dict[str, Any] = None, owner_id: int = None, merge: bool = False
    ) -> dict[str, Any]:
        """
        Set permissions for multiple documents.

        Args:
            ids: List of document IDs to update
            permissions: Permissions object
            owner_id: Owner ID to assign
            merge: Whether to merge with existing permissions (True) or replace them (False)

        Returns:
            The API response

        """
        params : dict[str, Any] = {"merge": merge}
        if permissions:
            params["set_permissions"] = permissions
        if owner_id is not None:
            params["owner"] = owner_id

        return self.bulk_action("set_permissions", ids, **params)

    def empty_trash(self) -> dict[str, Any]:
        """
        Empty the trash.

        Returns:
            The API response.

        Raises:
            APIError: If the empty trash request fails.

        """
        endpoint = self.get_endpoint("empty_trash")
        logger.debug("Emptying trash")
        payload = {"action": "empty"}
        response = self.client.request("POST", endpoint, data=payload, json_response=True)
        if not response:
            raise APIError("Empty trash failed")
        return response # type: ignore # request should have returned correct response TODO

class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """Resource for managing document notes."""

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name = "notes"
    endpoints = {"list": Template("/api/document/${pk}/notes/")}
