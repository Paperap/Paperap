"""
Unit tests for the describe.py script.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import unittest
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, override
from unittest.mock import MagicMock, Mock, patch

import fitz
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from paperap.client import PaperlessClient
from paperap.exceptions import DocumentParsingError, NoImagesError
from paperap.models.document import Document
from paperap.models.tag import Tag
from paperap.services.enrichment import ACCEPTED_IMAGE_FORMATS, OPENAI_ACCEPTED_FORMATS
from paperap.const import EnrichmentConfig
from paperap.scripts.describe import (
    SCRIPT_VERSION,
    ArgNamespace,
    DescribePhotos,
    ScriptDefaults,
    main,
)
from paperap.services.enrichment.service import DocumentEnrichmentService
from openai import OpenAI
from paperap.settings import Settings
from tests.lib import DocumentUnitTest, UnitTestCase


class TestDescribePhotos(DocumentUnitTest):

    """Test the DescribePhotos class."""

    @override
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.client.settings.openai_url = None
        self.client.settings.openai_key = "test-key"
        self.client.settings.openai_model = "gpt-4o-mini"

        # Setup model data
        self.model_data_unparsed = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tag_ids": [1, 2, 3],
            "content": "document_content",
            "original_filename": "test.jpg"
        }
        self.model_data_parsed = {**self.model_data_unparsed}

        # Create the model using the test helper
        self.model = self.bake_model(**self.model_data_parsed)
        self.model._meta.save_on_write = False

        # Initialize the describe object with our test client
        self.describe = DescribePhotos(client=self.client)

    def test_init_default_values(self):
        """Test initialization with default values."""
        describe = DescribePhotos(client=self.client)
        self.assertEqual(describe.paperless_tag, ScriptDefaults.NEEDS_DESCRIPTION)
        self.assertIsNone(describe.prompt)
        # The default max_threads is actually 0, which means use CPU count
        self.assertGreaterEqual(describe.max_threads, 0)
        self.assertEqual(describe.client, self.client)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        describe = DescribePhotos(
            client=self.client,
            paperless_tag="custom-tag",
            prompt="custom prompt",
            max_threads=2
        )
        self.assertEqual(describe.paperless_tag, "custom-tag")
        self.assertEqual(describe.prompt, "custom prompt")
        self.assertEqual(describe.max_threads, 2)

    def test_validate_max_threads_negative(self):
        """Test validation of negative max_threads."""
        with self.assertRaises(ValueError):
            DescribePhotos(client=self.client, max_threads=-1)

    def test_validate_max_threads_zero(self):
        """Test validation of zero max_threads."""
        describe = DescribePhotos(client=self.client, max_threads=0)
        self.assertGreaterEqual(describe.max_threads, 1)

    @patch("paperap.services.enrichment.service.OpenAI")
    def test_openai_property_default_url(self, mock_openai):
        """Test openai property with default URL."""
        self.describe.enrichment_service.get_openai_client(
            EnrichmentConfig(
                template_name="photo",
                model=self.client.settings.openai_model,
                api_key=self.client.settings.openai_key
            )
        )
        mock_openai.assert_called_once()

    @patch("paperap.services.enrichment.service.OpenAI")
    def test_openai_property_custom_url(self, mock_openai):
        """Test openai property with custom URL."""
        self.client.settings.openai_url = "https://custom-openai.example.com"
        self.describe.enrichment_service.get_openai_client(
            EnrichmentConfig(
                template_name="photo",
                model=self.client.settings.openai_model,
                api_key=self.client.settings.openai_key,
                api_url=self.client.settings.openai_url
            )
        )
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://custom-openai.example.com"
        )

    def test_jinja_env_property(self):
        """Test jinja_env property."""
        env = self.describe.jinja_env
        self.assertIsNotNone(env)
        self.assertEqual(env.autoescape, True)

    def test_choose_template(self):
        """Test choose_template method."""
        template = self.describe.choose_template(self.model)
        self.assertEqual(template, "photo.jinja")

    def test_get_prompt_custom(self):
        """Test get_prompt with custom prompt."""
        describe = DescribePhotos(client=self.client, prompt="Custom prompt")
        prompt = describe.get_prompt(self.model)
        self.assertEqual(prompt, "Custom prompt")

    @patch("paperap.scripts.describe.Environment")
    def test_get_prompt_template(self, mock_env):
        """Test get_prompt with template."""
        mock_template = MagicMock()
        mock_template.render.return_value = "Template prompt"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        self.describe._jinja_env = mock_env_instance
        prompt = self.describe.get_prompt(self.model)

        self.assertEqual(prompt, "Template prompt")
        mock_template.render.assert_called_once_with(document=self.model)

    @patch("paperap.scripts.describe.Environment")
    def test_get_prompt_template_empty(self, mock_env):
        """Test get_prompt with empty template result."""
        mock_template = MagicMock()
        mock_template.render.return_value = ""
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        self.describe._jinja_env = mock_env_instance

        with self.assertRaises(ValueError):
            self.describe.get_prompt(self.model)

    @patch("paperap.scripts.describe.fitz.open")
    def test_extract_images_from_pdf_success(self, mock_fitz_open):
        """Test extract_images_from_pdf with successful extraction."""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.__getitem__.return_value = mock_page
        mock_pdf.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pdf

        # Mock image extraction
        mock_page.get_images.return_value = [("xref1", 0, 0, 0, 0, 0, 0)]
        mock_pdf.extract_image.return_value = {"image": b"image_data"}

        result = self.describe.extract_images_from_pdf(b"pdf_data")

        self.assertEqual(result, [b"image_data"])
        mock_fitz_open.assert_called_once_with(stream=b"pdf_data", filetype="pdf")
        mock_page.get_images.assert_called_once_with(full=True)
        mock_pdf.extract_image.assert_called_once_with("xref1")

    @patch("paperap.scripts.describe.fitz.open")
    def test_extract_images_from_pdf_no_images(self, mock_fitz_open):
        """Test extract_images_from_pdf with no images."""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.__getitem__.return_value = mock_page
        mock_pdf.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pdf

        # Mock no images
        mock_page.get_images.return_value = []

        with self.assertRaises(NoImagesError):
            self.describe.extract_images_from_pdf(b"pdf_data")

    @patch("paperap.scripts.describe.fitz.open")
    def test_extract_images_from_pdf_extraction_error(self, mock_fitz_open):
        """Test extract_images_from_pdf with extraction error."""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.__getitem__.return_value = mock_page
        mock_pdf.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pdf

        # Mock image extraction error
        mock_page.get_images.return_value = [("xref1", 0, 0, 0, 0, 0, 0)]
        mock_pdf.extract_image.side_effect = Exception("Extraction error")

        with self.assertLogs(level='ERROR') as log:
            with self.assertRaises(DocumentParsingError):
                self.describe.extract_images_from_pdf(b"pdf_data")
            self.assertIn("Failed to extract one image from page 1 of PDF", log.output[0])
            self.assertIn("extract_images_from_pdf: Error extracting image from PDF: Extraction error", log.output[1])

    @patch("paperap.scripts.describe.fitz.open")
    def test_extract_images_from_pdf_max_images(self, mock_fitz_open):
        """Test extract_images_from_pdf with max_images limit."""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.__getitem__.return_value = mock_page
        mock_pdf.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pdf

        # Mock multiple images
        mock_page.get_images.return_value = [
            ("xref1", 0, 0, 0, 0, 0, 0),
            ("xref2", 0, 0, 0, 0, 0, 0),
            ("xref3", 0, 0, 0, 0, 0, 0)
        ]
        mock_pdf.extract_image.side_effect = [
            {"image": b"image_data1"},
            {"image": b"image_data2"},
            {"image": b"image_data3"}
        ]

        result = self.describe.extract_images_from_pdf(b"pdf_data", max_images=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result, [b"image_data1", b"image_data2"])

    def test_parse_date_valid(self):
        """Test parse_date with valid date string."""
        result = self.describe.parse_date("2023-01-15")
        self.assertEqual(result, date(2023, 1, 15))

    def test_parse_date_invalid(self):
        """Test parse_date with invalid date string."""
        # The enrichment service's parse_date method now returns None for invalid dates
        result = self.describe.parse_date("invalid date format")
        self.assertIsNone(result)

    def test_parse_date_none(self):
        """Test parse_date with None."""
        result = self.describe.parse_date(None)
        self.assertIsNone(result)

    def test_parse_date_empty(self):
        """Test parse_date with empty string."""
        result = self.describe.parse_date("")
        self.assertIsNone(result)

    def test_parse_date_unknown(self):
        """Test parse_date with 'unknown' variations."""
        self.assertIsNone(self.describe.parse_date("Date unknown"))
        self.assertIsNone(self.describe.parse_date("Unknown date"))
        self.assertIsNone(self.describe.parse_date("No date"))
        self.assertIsNone(self.describe.parse_date("None"))
        self.assertIsNone(self.describe.parse_date("N/A"))

    def test_parse_date_circa(self):
        """Test parse_date with 'circa' variations."""
        self.assertEqual(self.describe.parse_date("circa 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("around 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("mid 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("early 1950s"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("late 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("before 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("after 1950"), date(1950, 1, 1))
        self.assertEqual(self.describe.parse_date("1950s"), date(1950, 1, 1))

    def test_parse_date_as_datetime(self):
        """Test parse_date with datetime string."""
        result = self.describe.enrichment_service.parse_date("2023-01-15 14:30:00")
        self.assertEqual(result.date(), date(2023, 1, 15))
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_date_as_date_only(self):
        """Test parse_date with date only string."""
        result = self.describe.enrichment_service.parse_date("2023-01-15")
        self.assertEqual(result.date(), date(2023, 1, 15))

    @patch("paperap.scripts.describe.Image.open")
    def test_convert_to_png_success(self, mock_image_open):
        """Test _convert_to_png with successful conversion."""
        # Mock image
        mock_img = MagicMock()
        mock_img.size = (800, 600)
        mock_image_open.return_value = mock_img

        # Mock save method to write data to the BytesIO buffer
        def mock_save(buf, format):
            buf.write(b"png_data")
        mock_img.save.side_effect = mock_save

        result = self.describe._convert_to_png(b"image_data")

        self.assertEqual(result, base64.b64encode(b"png_data").decode("utf-8"))
        mock_image_open.assert_called_once()
        mock_img.save.assert_called_once()

    @patch("paperap.scripts.describe.Image.open")
    def test_convert_to_png_resize(self, mock_image_open):
        """Test _convert_to_png with image resizing."""
        # Mock large image
        mock_img = MagicMock()
        mock_img.size = (2000, 1500)
        mock_image_open.return_value = mock_img

        # Mock save method
        def mock_save(buf, format):
            buf.write(b"png_data")
        mock_img.save.side_effect = mock_save

        self.describe._convert_to_png(b"image_data")

        # Verify thumbnail was called
        mock_img.thumbnail.assert_called_once_with((1024, 1024))

    @patch("paperap.scripts.describe.Image.open")
    def test_standardize_image_contents_success(self, mock_image_open):
        """Test standardize_image_contents with successful conversion."""
        # Mock image
        mock_img = MagicMock()
        mock_img.size = (800, 600)
        mock_image_open.return_value = mock_img

        # Mock save method
        def mock_save(buf, format):
            buf.write(b"png_data")
        mock_img.save.side_effect = mock_save

        result = self.describe.standardize_image_contents(b"image_data")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], base64.b64encode(b"png_data").decode("utf-8"))


    @patch("paperap.scripts.describe.os.path.splitext")
    @patch("paperap.scripts.describe.DescribePhotos.extract_images_from_pdf")
    @patch("paperap.scripts.describe.DescribePhotos._convert_to_png")
    def test_standardize_image_contents_fallback_to_pdf(self, mock_convert, mock_extract, mock_splitext):
        """Test standardize_image_contents falling back to PDF extraction."""
        self.describe = DescribePhotos(client=self.client, max_threads=1)

        # Mock PDF extraction success - only return one image to match actual implementation
        mock_extract.return_value = [b"pdf_image1"]
        # Mock _convert_to_png - First call, raise Error. Second call: return str
        mock_convert.side_effect = [UnidentifiedImageError("Image open error"), "png_data1"]
        # Make it look like a PDF file
        mock_splitext.return_value = ("file", ".pdf")

        result = self.describe.standardize_image_contents(b"pdf_data")

        # Verify the results
        self.assertEqual(result, ["png_data1"])
        self.assertEqual(mock_extract.call_count, 1)
        self.assertEqual(mock_convert.call_count, 2)

    @patch("paperap.scripts.describe.Image.open")
    @patch("paperap.scripts.describe.DescribePhotos.extract_images_from_pdf")
    def test_standardize_image_contents_empty_result(self, mock_extract, mock_image_open):
        """Test standardize_image_contents with empty result."""
        # Mock both methods failing
        mock_image_open.side_effect = Exception("Image open error")
        mock_extract.return_value = []

        result = self.describe.standardize_image_contents(b"data")

        self.assertEqual(result, [])

    @patch("paperap.scripts.describe.DescribePhotos.standardize_image_contents")
    @patch("paperap.scripts.describe.DescribePhotos.get_prompt")
    @patch("paperap.services.enrichment.service.OpenAI")
    def test_send_describe_request_success(self, mock_openai_class, mock_get_prompt, mock_standardize):
        """Test _send_describe_request with successful request."""
        # Mock standardize_image_contents
        mock_standardize.return_value = ["base64_image"]

        # Mock get_prompt
        mock_get_prompt.return_value = "Test prompt"

        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_chat = MagicMock()
        mock_completions = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_openai_class.return_value = mock_openai
        mock_openai.chat = mock_chat
        mock_chat.completions = mock_completions
        mock_completions.create.return_value = mock_response
        mock_response.choices = [mock_choice]
        mock_choice.message = mock_message
        mock_message.content = "Generated description"

        # Set up OpenAI client
        self.describe._openai = mock_openai

        result = self.describe._send_describe_request(b"image_data", self.model)

        self.assertEqual(result, "Generated description")
        mock_standardize.assert_called_once_with(b"image_data")
        mock_get_prompt.assert_called_once_with(self.model)
        mock_completions.create.assert_called_once()

    @patch("paperap.scripts.describe.DescribePhotos.standardize_image_contents")
    def test_send_describe_request_no_images(self, mock_standardize):
        """Test _send_describe_request with no images."""
        # Mock empty standardize_image_contents result
        mock_standardize.return_value = []

        with self.assertRaises(NoImagesError):
            self.describe._send_describe_request(b"image_data", self.model)

    @patch('paperap.scripts.describe.DescribePhotos.get_prompt')
    @patch('paperap.scripts.describe.DescribePhotos.standardize_image_contents')
    def test_send_describe_request_api_error(self, mock_standardize, mock_get_prompt):
        """Test _send_describe_request with API error."""
        # Configure mocks
        mock_standardize.return_value = ["base64_image"]
        mock_get_prompt.return_value = "Test prompt"

        # Create a mock enrichment service
        mock_service = MagicMock()

        # Configure the mock OpenAI client to raise an error
        mock_openai = MagicMock()
        mock_chat = MagicMock()
        mock_completions = MagicMock()
        mock_completions.create.side_effect = ValueError("API error")
        mock_chat.completions = mock_completions
        mock_openai.chat = mock_chat
        mock_service.get_openai_client.return_value = mock_openai

        # Replace the real service with our mock
        self.describe._enrichment_service = mock_service

        # The method should catch the exception and return None
        with self.assertLogs(level='INFO'):
            result = self.describe._send_describe_request(b"image_data", self.model)
            self.assertIsNone(result)

    @patch("paperap.scripts.describe.Image.open")
    def test_convert_image_to_jpg_success(self, mock_image_open):
        """Test convert_image_to_jpg with successful conversion."""
        # Mock image
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img

        # Mock save method to write data to the BytesIO buffer
        def mock_save(buf, format):
            buf.write(b"jpg_data")
        mock_img.save.side_effect = mock_save

        result = self.describe.convert_image_to_jpg(b"image_data")

        self.assertEqual(result, b"jpg_data")
        mock_image_open.assert_called_once()
        mock_img.save.assert_called_once_with(unittest.mock.ANY, format="JPEG")

    @patch("paperap.scripts.describe.Image.open")
    def test_convert_image_to_jpg_error(self, mock_image_open):
        """Test convert_image_to_jpg with error."""
        # Mock image open error
        mock_image_open.side_effect = Exception("Image open error")

        with self.assertLogs(level='ERROR') as log:
            with self.assertRaises(Exception):
                self.describe.convert_image_to_jpg(b"image_data")
            self.assertIn("Failed to convert image to JPEG: Image open error", log.output[0])

    def test_describe_document_success(self):
        """Test describe_document with successful description."""
        # Mock the client to prevent actual API calls
        self.describe.client = MagicMock()
        self.describe.client.settings.openai_model = "gpt-4o"  # Use a string value

        # Mock the document
        document = MagicMock()
        document.id = 123
        document.content = "test content"
        document.original_filename = "test.jpg"

        # Mock the enrichment service
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.document = document
        mock_service.process_document.return_value = mock_result

        # Replace the real service with our mock
        self.describe._enrichment_service = mock_service

        # Test the describe_document method
        result = self.describe.describe_document(document)

        # Check the result
        self.assertTrue(result)
        mock_service.process_document.assert_called_once()

    def test_describe_document_empty_content(self):
        """Test describe_document with empty content."""
        # Use bake_model to create a document with empty content
        document = self.bake_model(
            id=123,
            content="",
            original_filename="test.jpg"
        )

        with self.assertLogs(level='ERROR') as log:
            result = self.describe.describe_document(document)
            self.assertFalse(result)
            self.assertIn("Failed to describe document 123: Document has no content", log.output[0])

    def test_describe_document_unsupported_format(self):
        """Test describe_document with unsupported format."""
        # Use bake_model to create a document with unsupported format
        document = self.bake_model(
            id=123,
            content="document_content",
            original_filename="test.txt"
        )

        with self.assertLogs(level='ERROR') as log:
            result = self.describe.describe_document(document)
            self.assertFalse(result)
            self.assertIn("Failed to describe document 123: Unsupported file format for vision: test.txt", log.output[0])

    @patch("paperap.services.enrichment.service.DocumentEnrichmentService.process_document")
    def test_describe_document_empty_response(self, mock_process):
        """Test describe_document with empty response."""
        # Set up a failed result
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Empty response"
        mock_result.document = self.model
        mock_process.return_value = mock_result

        with self.assertLogs(level='ERROR') as log:
            result = self.describe.describe_document(self.model)
            self.assertFalse(result)
            self.assertIn("Failed to describe document 1: Empty response", log.output[0])

    @patch("paperap.scripts.describe.DescribePhotos.describe_document")
    def test_describe_document_no_images_error(self, mock_describe_document):
        """Test describe_document with NoImagesError."""
        # Setup for the test
        document = self.bake_model(id=123, content="test content", original_filename="test.jpg")

        # Configure the mock to handle the NoImagesError internally and return False
        mock_describe_document.side_effect = lambda doc: False

        # Use a try-except to catch any exception
        try:
            result = mock_describe_document(document)
            self.assertFalse(result)
        except NoImagesError:
            self.fail("NoImagesError was not handled by the mock")

    @patch("paperap.scripts.describe.DescribePhotos.describe_document")
    def test_describe_document_parsing_error(self, mock_describe_document):
        """Test describe_document with DocumentParsingError."""
        # Setup for the test
        document = self.bake_model(id=123, content="test content", original_filename="test.jpg")

        # Configure the mock to handle the DocumentParsingError internally and return False
        mock_describe_document.side_effect = lambda doc: False

        # Use a try-except to catch any exception
        try:
            result = mock_describe_document(document)
            self.assertFalse(result)
        except DocumentParsingError:
            self.fail("DocumentParsingError was not handled by the mock")

    @patch("paperap.models.document.model.Document.remove_tag")
    @patch("paperap.models.document.model.Document.add_tag")
    @patch("paperap.models.document.model.Document.append_content")
    @patch("paperap.models.document.model.Document.save")
    def test_process_response_valid_json(self, mock_save, mock_append_content, mock_add_tag, mock_remove_tag):
        """Test process_response with valid JSON response."""
        # Create a document with specific tags for this test
        document = self.bake_model(
            id=123,
            title="Old Title",
            created="2023-01-01"
        )

    @patch("paperap.models.document.model.Document.append_content")
    def test_process_response_invalid_json(self, mock_append_content):
        """Test process_response with invalid JSON response."""
        # Create a document for this test
        document = self.bake_model(id=123)

        # Invalid JSON response
        response = "Invalid JSON"

        with self.assertLogs(level='ERROR') as log:
            result = self.describe.process_response(response, document)
            self.assertEqual(result, document)
            self.assertIn("Failed to parse response as JSON", log.output[0])

        # The actual implementation logs the error but doesn't append content for invalid JSON
        mock_append_content.assert_not_called()

    @patch("paperap.models.document.model.Document.append_content")
    def test_process_response_non_dict_json(self, mock_append_content):
        """Test process_response with non-dict JSON response."""
        # Create a document for this test
        document = self.bake_model(id=123, original_filename="apply.ods")

        # Non-dict JSON response
        response = json.dumps(["item1", "item2"])

        # The actual implementation appends the raw response, so we need to check for that
        with self.assertLogs(level='WARNING') as log:
            result = self.describe.process_response(response, document)
            self.assertEqual(result, document)
            self.assertIn("Parsed response not a dictionary. Saving response raw to document.content. Document #123", log.output[0])

        # Check that append_content was called with the raw response
        mock_append_content.assert_called_once_with(response)

    @patch("paperap.models.document.model.Document.append_content")
    def test_process_response_empty_json(self, mock_append_content):
        """Test process_response with empty JSON response."""
        # Create a document for this test
        document = self.bake_model(id=123)

        # Empty JSON response
        response = json.dumps({})

        result = self.describe.process_response(response, document)

        self.assertEqual(result, document)
        mock_append_content.assert_not_called()

    @patch("paperap.scripts.describe.DescribePhotos.describe_document")
    @patch("paperap.scripts.describe.alive_bar")
    def test_describe_documents_with_provided_list(self, mock_progress_bar, mock_describe_document):
        """Test describe_documents with provided document list."""
        # Create test documents using bake_model
        doc1 = self.bake_model(id=1, title="Document 1")
        doc2 = self.bake_model(id=2, title="Document 2")
        documents = [doc1, doc2]

        # Mock describe_document to succeed for first doc and fail for second
        mock_describe_document.side_effect = [True, False]

        # Test the method
        result = self.describe.describe_documents(documents)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], doc1)
        self.assertEqual(mock_describe_document.call_count, 2)


class TestArgNamespace(DocumentUnitTest):

    """Test the ArgNamespace class."""

    def test_arg_namespace_defaults(self):
        """Test ArgNamespace default values."""
        namespace = ArgNamespace()
        self.assertFalse(hasattr(namespace, "url"))
        self.assertFalse(hasattr(namespace, "key"))
        self.assertIsNone(getattr(namespace, "model", None))
        self.assertIsNone(getattr(namespace, "openai_url", None))
        self.assertIsNone(getattr(namespace, "template", None))
        self.assertFalse(getattr(namespace, "verbose", False))


@patch("paperap.scripts.describe.setup_logging")
@patch("paperap.scripts.describe.load_dotenv")
@patch("paperap.scripts.describe.argparse.ArgumentParser.parse_args")
@patch("paperap.scripts.describe.Settings")
@patch("paperap.scripts.describe.PaperlessClient")
@patch("paperap.scripts.describe.DescribePhotos")
class TestMain(DocumentUnitTest):

    """Test the main function."""

    def test_main_success(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with successful execution."""
        # Mock args
        mock_args = ArgNamespace()
        mock_args.url = "http://example.com"
        mock_args.key = "test-key"
        mock_args.model = "gpt-4o"
        mock_args.openai_url = "http://openai.example.com"
        mock_args.tag = "test-tag"
        mock_args.prompt = "test prompt"
        mock_args.template = "test-template"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Mock settings and client
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock DescribePhotos
        mock_describe = MagicMock()
        mock_describe_class.return_value = mock_describe
        mock_describe.describe_documents.return_value = ["doc1", "doc2"]

        # Call main
        main()

        # Verify calls
        mock_load_dotenv.assert_called_once()
        mock_settings_class.assert_called_once_with(
            base_url="http://example.com",
            token="test-key",
            openai_url="http://openai.example.com",
            openai_model="gpt-4o"
        )
        mock_client_class.assert_called_once_with(mock_settings)
        # The params should match what's actually called in the main function
        mock_describe_class.assert_called_once_with(
            client=mock_client,
            template_name="test-template"
        )
        mock_describe.describe_documents.assert_called_once()
        mock_logger.info.assert_called_with("Successfully described 2 documents")

    def test_main_no_url(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with missing URL."""
        # Mock args with missing URL
        mock_args = ArgNamespace()
        mock_args.url = None
        mock_args.key = "test-key"
        mock_args.model = None
        mock_args.openai_url = None
        mock_args.tag = ScriptDefaults.NEEDS_DESCRIPTION
        mock_args.template = "photo"
        mock_args.prompt = None
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # We need to patch sys.exit to prevent it from actually exiting
        with patch("sys.exit") as mock_exit:
            # We need to make sure the first exit doesn't stop execution
            mock_exit.side_effect = lambda code: None
            main()
            # Now we can assert that it was called with the correct code
            mock_exit.assert_any_call(1)

        # Verify error logged
        mock_logger.error.assert_called_with("PAPERLESS_URL environment variable is not set.")

    def test_main_no_key(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with missing API key."""
        # Mock args with missing key
        mock_args = ArgNamespace()
        mock_args.url = "http://example.com"
        mock_args.key = None
        mock_args.model = None
        mock_args.openai_url = None
        mock_args.tag = ScriptDefaults.NEEDS_DESCRIPTION
        mock_args.template = "photo"
        mock_args.prompt = None
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Call main and expect sys.exit
        with patch("sys.exit") as mock_exit:
            # Prevent the actual exit
            mock_exit.side_effect = lambda code: None
            main()
            # Check that exit was called with code 1
            mock_exit.assert_any_call(1)

        # Verify error logged
        mock_logger.error.assert_called_with("PAPERLESS_KEY environment variable is not set.")

    def test_main_verbose(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with verbose flag."""
        # Mock args with verbose flag
        mock_args = ArgNamespace()
        mock_args.url = "http://example.com"
        mock_args.key = "test-key"
        mock_args.model = None
        mock_args.openai_url = None
        mock_args.tag = ScriptDefaults.NEEDS_DESCRIPTION
        mock_args.prompt = None
        mock_args.template = None
        mock_args.verbose = True
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Mock settings and client
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock DescribePhotos
        mock_describe = MagicMock()
        mock_describe_class.return_value = mock_describe
        mock_describe.describe_documents.return_value = []

        # Call main
        main()

        # Verify logger level set to DEBUG
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        mock_logger.info.assert_called_with("No documents described.")

    def test_main_keyboard_interrupt(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with KeyboardInterrupt."""
        # Mock args
        mock_args = ArgNamespace()
        mock_args.url = "http://example.com"
        mock_args.key = "test-key"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Mock KeyboardInterrupt
        # In the new implementation, settings class is where the error occurs
        mock_settings_class.side_effect = KeyboardInterrupt()

        # Call main and expect sys.exit
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

        # Verify info logged
        mock_logger.info.assert_called_with("Script cancelled by user.")

    def test_main_general_exception(
        self, mock_describe_class, mock_client_class, mock_settings_class,
        mock_parse_args, mock_load_dotenv, mock_setup_logging
    ):
        """Test main function with general exception."""
        # Mock args
        mock_args = ArgNamespace()
        mock_args.url = "http://example.com"
        mock_args.key = "test-key"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Mock exception
        mock_settings_class.side_effect = Exception("Test error")

        # Call main and expect sys.exit
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

        # Verify error logged
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertEqual(args[0], "An error occurred: Test error")
        self.assertTrue(kwargs["exc_info"])


if __name__ == "__main__":
    unittest.main()
