

from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

from paperap.client import PaperlessClient
from paperap.exceptions import APIError, ResourceNotFoundError
from paperap.models.document import Document, DocumentNote, DocumentNoteQuerySet, DocumentQuerySet
from paperap.resources import DocumentNoteResource, DocumentResource


class TestDocumentResource(unittest.TestCase):
    """
    Test suite for DocumentResource class.

    Written By claude
    """

    def setUp(self):
        """
        Set up test fixtures.

        Written By claude
        """
        self.mock_client = mock.create_autospec(PaperlessClient)
        self.resource = DocumentResource(self.mock_client)

        # Mock get_endpoint to return string URLs instead of MagicMock objects
        self.resource.get_endpoint = MagicMock()

    def test_init(self):
        """
        Test initialization of DocumentResource.

        Written By claude
        """
        self.assertEqual(self.resource.model_class, Document)
        self.assertEqual(self.resource.queryset_class, DocumentQuerySet)
        self.assertEqual(self.resource.name, "documents")
        self.assertIn("upload", self.resource.endpoints)

        # Mock the get_endpoint return value
        self.resource.get_endpoint.return_value = "/api/documents/post_document/"
        self.assertEqual(self.resource.get_endpoint("upload"), "/api/documents/post_document/")

    def test_download(self):
        """
        Test download method returns bytes when successful.

        Written By claude
        """
        # Setup
        document_id = 123
        expected_bytes = b"test document content"
        self.mock_client.request.return_value = expected_bytes

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/123/download/"

        # Execute
        result = self.resource.download(document_id)

        # Verify
        self.mock_client.request.assert_called_once_with(
            "GET",
            self.resource.get_endpoint("download", pk=document_id),
            params={"original": "false"},
            json_response=False
        )
        self.assertEqual(result, expected_bytes)

    def test_download_original(self):
        """
        Test download method with original=True parameter.

        Written By claude
        """
        # Setup
        document_id = 123
        expected_bytes = b"original document content"
        self.mock_client.request.return_value = expected_bytes

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/123/download/"

        # Execute
        result = self.resource.download(document_id, original=True)

        # Verify
        self.mock_client.request.assert_called_once_with(
            "GET",
            self.resource.get_endpoint("download", pk=document_id),
            params={"original": "true"},
            json_response=False
        )
        self.assertEqual(result, expected_bytes)

    def test_download_not_found(self):
        """
        Test download method raises ResourceNotFoundError when document not found.

        Written By claude
        """
        # Setup
        document_id = 999
        self.mock_client.request.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/999/download/"

        # Execute and Verify
        with self.assertRaises(ResourceNotFoundError) as context:
            self.resource.download(document_id)

        self.assertIn(f"Document {document_id} download failed", str(context.exception))

    def test_preview(self):
        """
        Test preview method returns bytes when successful.

        Written By claude
        """
        # Setup
        document_id = 123
        expected_bytes = b"preview content"
        self.mock_client.request.return_value = expected_bytes

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/123/preview/"

        # Execute
        result = self.resource.preview(document_id)

        # Verify
        self.mock_client.request.assert_called_once_with(
            "GET",
            self.resource.get_endpoint("preview", pk=document_id),
            json_response=False
        )
        self.assertEqual(result, expected_bytes)

    def test_preview_not_found(self):
        """
        Test preview method raises ResourceNotFoundError when document not found.

        Written By claude
        """
        # Setup
        document_id = 999
        self.mock_client.request.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/999/preview/"

        # Execute and Verify
        with self.assertRaises(ResourceNotFoundError) as context:
            self.resource.preview(document_id)

        self.assertIn(f"Document {document_id} preview failed", str(context.exception))

    def test_thumbnail(self):
        """
        Test thumbnail method returns bytes when successful.

        Written By claude
        """
        # Setup
        document_id = 123
        expected_bytes = b"thumbnail content"
        self.mock_client.request.return_value = expected_bytes

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/123/thumb/"

        # Execute
        result = self.resource.thumbnail(document_id)

        # Verify
        self.mock_client.request.assert_called_once_with(
            "GET",
            self.resource.get_endpoint("thumbnail", pk=document_id),
            json_response=False
        )
        self.assertEqual(result, expected_bytes)

    def test_thumbnail_not_found(self):
        """
        Test thumbnail method raises ResourceNotFoundError when document not found.

        Written By claude
        """
        # Setup
        document_id = 999
        self.mock_client.request.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/999/thumb/"

        # Execute and Verify
        with self.assertRaises(ResourceNotFoundError) as context:
            self.resource.thumbnail(document_id)

        self.assertIn(f"Document {document_id} thumbnail failed", str(context.exception))

    @patch("pathlib.Path.open", new_callable=mock.mock_open, read_data=b"test file content")
    def test_upload(self, mock_open):
        """
        Test upload method with file path.

        Written By claude
        """
        # Setup
        filepath = Path("/path/to/test.pdf")
        expected_task_id = "ca6a6dc8-b434-4fcd-8436-8b2546465622"
        self.mock_client.request.return_value = expected_task_id
        metadata = {"title": "Test Document", "correspondent": 1}

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/post_document/"

        # Execute
        result = self.resource.upload_async(filepath, **metadata)

        # Verify
        mock_open.assert_called_once_with("rb")
        self.mock_client.request.assert_called_once()
        call_args = self.mock_client.request.call_args
        self.assertEqual(call_args[0][0], "POST")
        self.assertEqual(call_args[0][1], self.resource.get_endpoint("upload"))
        self.assertEqual(call_args[1]["data"], metadata)
        self.assertIn("files", call_args[1])
        self.assertIn("document", call_args[1]["files"])
        self.assertEqual(call_args[1]["files"]["document"][0], filepath.name)
        self.assertEqual(result, expected_task_id)

    def test_upload_content(self):
        """
        Test upload_content method with binary content.

        Written By claude
        """
        # Setup
        file_content = b"test file content"
        filename = "test.pdf"
        expected_task_id = "ca6a6dc8-b434-4fcd-8436-8b2546465622"
        self.mock_client.request.return_value = expected_task_id
        metadata = {"title": "Test Document", "correspondent": 1}

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/post_document/"

        # Execute
        result = self.resource.upload_content(file_content, filename, **metadata)

        # Verify
        self.mock_client.request.assert_called_once()
        call_args = self.mock_client.request.call_args
        self.assertEqual(call_args[0][0], "POST")
        self.assertEqual(call_args[0][1], self.resource.get_endpoint("upload"))
        self.assertEqual(call_args[1]["data"], metadata)
        self.assertIn("files", call_args[1])
        self.assertIn("document", call_args[1]["files"])
        self.assertEqual(call_args[1]["files"]["document"][0], filename)
        self.assertEqual(call_args[1]["files"]["document"][1], file_content)
        self.assertEqual(result, expected_task_id)

    def test_upload_content_failure(self):
        """
        Test upload_content method raises ResourceNotFoundError on failure.

        Written By claude
        """
        # Setup
        file_content = b"test file content"
        filename = "test.pdf"
        self.mock_client.request.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "documents/post_document/"

        # Execute and Verify
        with self.assertRaises(ResourceNotFoundError) as context:
            self.resource.upload_content(file_content, filename)

        self.assertIn("Document upload failed", str(context.exception))

    def test_next_asn(self):
        """
        Test next_asn method returns integer when successful.

        Written By claude
        """
        # Setup
        expected_asn = 42
        self.mock_client.request.return_value = {"next_asn": expected_asn}

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/next_asn/"

        # Execute
        result = self.resource.next_asn()

        # Verify
        self.mock_client.request.assert_called_once_with(
            "GET",
            self.resource.get_endpoint("next_asn")
        )
        self.assertEqual(result, expected_asn)

    def test_next_asn_failure(self):
        """
        Test next_asn method raises APIError on failure.

        Written By claude
        """
        # Setup
        self.mock_client.request.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/next_asn/"

        # Execute and Verify
        with self.assertRaises(APIError) as context:
            self.resource.next_asn()

        self.assertIn("Failed to retrieve next ASN", str(context.exception))

    def test_next_asn_missing_key(self):
        """
        Test next_asn method raises APIError when response is missing next_asn key.

        Written By claude
        """
        # Setup
        self.mock_client.request.return_value = {"something_else": 42}

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/next_asn/"

        # Execute and Verify
        with self.assertRaises(APIError) as context:
            self.resource.next_asn()

        self.assertIn("Failed to retrieve next ASN", str(context.exception))


class TestDocumentNoteResource(unittest.TestCase):
    """
    Test suite for DocumentNoteResource class.

    Written By claude
    """

    def setUp(self):
        """
        Set up test fixtures.

        Written By claude
        """
        self.mock_client = mock.create_autospec(PaperlessClient)
        self.resource = DocumentNoteResource(self.mock_client)

        # Mock get_endpoint to return string URLs instead of MagicMock objects
        self.resource.get_endpoint = MagicMock()

    def test_init(self):
        """
        Test initialization of DocumentNoteResource.

        Written By claude
        """
        self.assertEqual(self.resource.model_class, DocumentNote)
        self.assertEqual(self.resource.queryset_class, DocumentNoteQuerySet)
        self.assertEqual(self.resource.name, "document_notes")
        self.assertIn("list", self.resource.endpoints)

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "/api/document/${pk}/notes/"
        self.assertEqual(self.resource.get_endpoint("list"), "/api/document/${pk}/notes/")


if __name__ == "__main__":
    unittest.main()
