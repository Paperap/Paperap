

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from paperap.client import PaperlessClient
from paperap.const import URLS
from paperap.exceptions import ResourceNotFoundError
from paperap.models.document.download import DownloadedDocument, RetrieveFileMode
from paperap.resources.document_download import DownloadedDocumentResource


class TestDownloadedDocumentResource(unittest.TestCase):
    """
    Test suite for the DownloadedDocumentResource class.
    """

    def setUp(self):
        """
        Written By claude

        Set up test fixtures before each test method.
        Creates a mock client and initializes the resource.
        """
        self.mock_client = MagicMock(spec=PaperlessClient)
        self.resource = DownloadedDocumentResource(self.mock_client)

        # Mock get_endpoint to return string URLs instead of MagicMock objects
        self.resource.get_endpoint = MagicMock()

    def test_initialization(self):
        """
        Written By claude

        Test that the resource is initialized correctly with the right attributes.
        """
        self.assertEqual(self.resource.model_class, DownloadedDocument)
        self.assertEqual(self.resource.name, "document")

    def test_load_download_mode(self):
        """
        Written By claude

        Test loading a document in download mode.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.DOWNLOAD, original=False)

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="test.pdf"',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Call the method
        self.resource.load(doc)

        # Verify the client was called correctly
        self.mock_client.request_raw.assert_called_once_with(
            "GET", "document/1/download/", params={"original": "false"}, data=None
        )

        # Verify the document was updated
        self.assertEqual(doc.content, b"file content")
        self.assertEqual(doc.content_type, "application/pdf")
        self.assertEqual(doc.disposition_filename, "test.pdf")
        self.assertEqual(doc.disposition_type, "attachment")

    def test_load_preview_mode(self):
        """
        Written By claude

        Test loading a document in preview mode.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.PREVIEW, original=True)

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"preview content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'inline; filename="preview.pdf"',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/preview/"

        # Call the method
        self.resource.load(doc)

        # Verify the client was called correctly
        self.mock_client.request_raw.assert_called_once_with(
            "GET", "document/1/preview/", params={"original": "true"}, data=None
        )

        # Verify the document was updated
        self.assertEqual(doc.content, b"preview content")
        self.assertEqual(doc.content_type, "application/pdf")
        self.assertEqual(doc.disposition_filename, "preview.pdf")
        self.assertEqual(doc.disposition_type, "inline")

    def test_load_thumbnail_mode(self):
        """
        Written By claude

        Test loading a document in thumbnail mode.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.THUMBNAIL, original=False)

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"thumbnail content"
        mock_response.headers = {
            "Content-Type": "image/jpeg",
            "Content-Disposition": 'inline; filename="thumb.jpg"',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/thumb/"

        # Call the method
        self.resource.load(doc)

        # Verify the client was called correctly
        self.mock_client.request_raw.assert_called_once_with(
            "GET", "document/1/thumb/", params={"original": "false"}, data=None
        )

        # Verify the document was updated
        self.assertEqual(doc.content, b"thumbnail content")
        self.assertEqual(doc.content_type, "image/jpeg")
        self.assertEqual(doc.disposition_filename, "thumb.jpg")
        self.assertEqual(doc.disposition_type, "inline")

    def test_load_default_mode(self):
        """
        Written By claude

        Test loading a document with no mode specified (should default to download).
        """
        # Create a mock document with no mode
        doc = DownloadedDocument(id=1, mode=None, original=False)

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="test.pdf"',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Call the method
        self.resource.load(doc)

        # Verify the client was called correctly with default mode (download)
        self.mock_client.request_raw.assert_called_once_with(
            "GET", "document/1/download/", params={"original": "false"}, data=None
        )

    def test_load_no_content_disposition(self):
        """
        Written By claude

        Test loading a document when the response has no Content-Disposition header.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.DOWNLOAD, original=False)

        # Mock the response with no Content-Disposition
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            # No Content-Disposition header
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Call the method
        self.resource.load(doc)

        # Verify the document was updated correctly
        self.assertEqual(doc.content, b"file content")
        self.assertEqual(doc.content_type, "application/pdf")
        self.assertIsNone(doc.disposition_filename)
        self.assertIsNone(doc.disposition_type)

    def test_load_complex_content_disposition(self):
        """
        Written By claude

        Test loading a document with a complex Content-Disposition header.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.DOWNLOAD, original=False)

        # Mock the response with a complex Content-Disposition
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="test file.pdf"; size=12345',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Call the method
        self.resource.load(doc)

        # Verify the document was updated correctly
        self.assertEqual(doc.content, b"file content")
        self.assertEqual(doc.disposition_filename, "test file.pdf")
        self.assertEqual(doc.disposition_type, "attachment")

    def test_load_request_failure(self):
        """
        Written By claude

        Test that a ResourceNotFoundError is raised when the request fails.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.DOWNLOAD, original=False)

        # Mock the response to be None (request failed)
        self.mock_client.request_raw.return_value = None

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Verify that the correct exception is raised
        with self.assertRaises(ResourceNotFoundError):
            self.resource.load(doc)

    @patch('paperap.models.document.download.DownloadedDocument.update_locally')
    def test_update_locally_called_correctly(self, mock_update_locally):
        """
        Written By claude

        Test that update_locally is called with the correct parameters.
        """
        # Create a mock document
        doc = DownloadedDocument(id=1, mode=RetrieveFileMode.DOWNLOAD, original=False)

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="test.pdf"',
        }
        self.mock_client.request_raw.return_value = mock_response

        # Set the mock endpoint value
        self.resource.get_endpoint.return_value = "document/1/download/"

        # Call the method
        self.resource.load(doc)

        # Verify update_locally was called with the correct parameters
        mock_update_locally.assert_called_once_with(
            from_db=True,
            content=b"file content",
            content_type="application/pdf",
            disposition_filename="test.pdf",
            disposition_type="attachment",
        )


if __name__ == "__main__":
    unittest.main()
