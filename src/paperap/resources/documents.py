"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    documents.py                                                                                         *
*        Project: resources                                                                                            *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

import os.path
from typing import Any, BinaryIO, Dict, Iterator, List, Optional

from paperap.exceptions import APIError
from paperap.models.document import Document
from paperap.resources.base import PaperlessResource


class DocumentResource(PaperlessResource[Document]):
    """Resource for managing documents."""

    model_class = Document
    name = "documents"

    def upload(
        self,
        file_path: str,
        title: str | None = None,
        correspondent: int | None = None,
        document_type: int | None = None,
        tags: Optional[list[int]] = None,
    ) -> Document:
        """
        Upload a document.

        Args:
            file_path: Path to the file to upload.
            title: Document title. If None, uses the filename.
            correspondent: Correspondent ID.
            document_type: Document type ID.
            tags: list of tag IDs.

        Returns:
            The created document.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            return self.upload_fileobj(
                f,
                filename,
                title=title or os.path.splitext(filename)[0],
                correspondent=correspondent,
                document_type=document_type,
                tags=tags,
            )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        filename: str,
        title: str | None = None,
        correspondent: int | None = None,
        document_type: int | None = None,
        tags: Optional[List[int]] = None,
    ) -> Document:
        """
        Upload a document from a file-like object.

        Args:
            fileobj: File-like object to upload.
            filename: Name of the file.
            title: Document title.
            correspondent: Correspondent ID.
            document_type: Document type ID.
            tags: list of tag IDs.

        Returns:
            The created document.
        """
        data: dict[str, Any] = {}
        if title:
            data["title"] = title
        if correspondent:
            data["correspondent"] = correspondent
        if document_type:
            data["document_type"] = document_type
        if tags:
            data["tags"] = tags

        files = {"document": (filename, fileobj, "application/octet-stream")}

        if not (
            response := self.client.request(
                "POST",
                "documents/post_document/",
                data=data,
                files=files,
            )
        ):
            raise APIError("Failed to upload document")

        return Document.from_dict(response, self)

    def download(self, document_id: int, original: bool = False) -> bytes:
        """
        Download a document.

        Args:
            document_id: Document ID.
            original: Whether to download the original file (True) or
                      the archived file (False).

        Returns:
            Document content as bytes.
        """
        endpoint = f"documents/{document_id}/{'download/' if original else 'preview/'}"
        response = self.client.session.get(
            f"{self.client.base_url}{endpoint}",
            headers=self.client._get_headers(),
            **self.client._get_auth_params(),
        )
        response.raise_for_status()
        return response.content

    def search(self, query: str) -> Iterator[Document]:
        """
        Search for documents.

        Args:
            query: Search query.

        Returns:
            List of matching documents.
        """
        params = {"query": query}
        return self.all()._request_iter(params=params)
