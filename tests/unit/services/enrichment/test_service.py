"""
Unit tests for DocumentEnrichmentService.

Tests the functionality of the document enrichment service, including
template rendering, OpenAI integration, image processing, and document updating.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, cast
from unittest import TestCase, mock
from unittest.mock import MagicMock, Mock, patch

import fitz
import openai
from jinja2 import Environment
from PIL import Image, UnidentifiedImageError

from paperap.exceptions import DocumentParsingError, NoImagesError
from paperap.models.document import Document
from paperap.services.enrichment.service import (
    DEFAULT_TEMPLATES_PATH,
    DocumentEnrichmentService,
    EnrichmentConfig,
    EnrichmentResult,
    TemplateLoader,
    template_loader,
)


class TestTemplateLoader(TestCase):
    """Test the TemplateLoader class for template management."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = TemplateLoader()
        self.custom_dir = Path(__file__).parent / "test_templates"
        self.custom_dir.mkdir(exist_ok=True)

        # Create a test template
        test_template = self.custom_dir / "test.jinja"
        test_template.write_text("Hello {{ name }}!")

    def tearDown(self):
        """Clean up after tests."""
        # Remove test templates
        for file in self.custom_dir.glob("*.jinja"):
            file.unlink()
        self.custom_dir.rmdir()

    def test_get_environment_default(self):
        """Test getting the default environment."""
        env = self.loader.get_environment()
        self.assertIsInstance(env, Environment)
        self.assertEqual(env.loader.searchpath[0], DEFAULT_TEMPLATES_PATH)

    def test_get_environment_custom(self):
        """Test getting a custom environment."""
        env = self.loader.get_environment(str(self.custom_dir))
        self.assertIsInstance(env, Environment)
        self.assertEqual(env.loader.searchpath[0], str(self.custom_dir))

    def test_get_environment_from_env_var(self):
        """Test getting environment from environment variable."""
        with patch.dict(os.environ, {
            "PAPERAP_TEMPLATE_DIR": str(self.custom_dir)
        }):
            env = self.loader.get_environment()
            self.assertIsInstance(env, Environment)
            self.assertEqual(env.loader.searchpath[0], str(self.custom_dir))

    def test_render_template(self):
        """Test rendering a template."""
        result = self.loader.render_template(
            "test",
            template_dir=str(self.custom_dir),
            name="World"
        )
        self.assertEqual(result, "Hello World!")

    def test_environment_caching(self):
        """Test that environments are cached."""
        env1 = self.loader.get_environment(str(self.custom_dir))
        env2 = self.loader.get_environment(str(self.custom_dir))
        self.assertIs(env1, env2)


class TestEnrichmentConfig(TestCase):
    """Test the EnrichmentConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EnrichmentConfig(template_name="test")
        self.assertEqual(config.template_name, "test")
        self.assertIsNone(config.template_dir)
        self.assertEqual(config.model, "gpt-4o-mini")
        self.assertIsNone(config.api_key)
        self.assertIsNone(config.api_url)
        self.assertTrue(config.vision)
        self.assertTrue(config.extract_images)
        self.assertEqual(config.max_images, 2)
        self.assertEqual(config.max_tokens, 500)

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EnrichmentConfig(
            template_name="custom",
            template_dir="/custom/dir",
            model="gpt-4",
            api_key="test-key",
            api_url="https://api.example.com",
            vision=False,
            extract_images=False,
            max_images=5,
            max_tokens=1000,
        )
        self.assertEqual(config.template_name, "custom")
        self.assertEqual(config.template_dir, "/custom/dir")
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.api_url, "https://api.example.com")
        self.assertFalse(config.vision)
        self.assertFalse(config.extract_images)
        self.assertEqual(config.max_images, 5)
        self.assertEqual(config.max_tokens, 1000)


class TestDocumentEnrichmentService(TestCase):
    """Test the DocumentEnrichmentService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = DocumentEnrichmentService()
        self.config = EnrichmentConfig(
            template_name="document_description",
            api_key="test-key",
            api_url="https://api.example.com",
        )

        # Create mock document
        self.document = Mock(spec=Document)
        self.document.id = 123
        self.document.title = "Test Document"
        self.document.content = b"test content"
        self.document.original_filename = "test.pdf"
        self.document.correspondent = Mock(name="Test Correspondent")
        self.document.document_type = Mock(name="Test Type")
        self.document.tag_names = ["tag1", "tag2"]
        self.document.custom_fields = []
        self.document.custom_field_value = Mock(return_value="test value")
        self.document.add_tag = Mock()
        self.document.set_custom_field = Mock()

        # Mock the signals manager
        self.service.signals.emit = Mock(return_value=None)

        # Create test PDF file
        pdf_path = Path(__file__).parent / "test.pdf"
        with open(pdf_path, "wb") as f:
            f.write(b"test PDF content")
        self.test_pdf_path = pdf_path

    def tearDown(self):
        """Clean up after tests."""
        # Remove test PDF
        if self.test_pdf_path.exists():
            self.test_pdf_path.unlink()

    def test_init(self):
        """Test initialization of the service."""
        service = DocumentEnrichmentService(api_key="test-key", api_url="test-url")
        self.assertEqual(service._api_key, "test-key")
        self.assertEqual(service._api_url, "test-url")
        self.assertIsNone(service._openai_client)

    @patch('pkgutil.get_data')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_bytes')
    def test_ensure_default_templates(self, mock_write, mock_exists, mock_mkdir, mock_get_data):
        """Test that default templates are created if missing."""
        mock_exists.return_value = False
        mock_get_data.return_value = b"template content"

        self.service._ensure_default_templates()

        mock_mkdir.assert_called_once()
        self.assertEqual(mock_write.call_count, 3)  # Three default templates
        mock_get_data.assert_called()

    @patch('paperap.services.enrichment.service.OpenAI')
    def test_get_openai_client(self, mock_openai_class):
        """Test getting the OpenAI client."""
        # First call should create a new client
        self.service._openai_client = None

        # Create a new mock instance for OpenAI
        mock_instance = Mock()
        mock_openai_class.return_value = mock_instance

        # Call the method to get the client
        client = self.service.get_openai_client(self.config)

        # Verify the mock was called with the right arguments
        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.example.com"
        )

        # Verify the returned client is our mock
        self.assertEqual(client, mock_instance)

        # Second call should return the existing client
        mock_openai_class.reset_mock()
        client2 = self.service.get_openai_client(self.config)
        mock_openai_class.assert_not_called()

    def test_prepare_context(self):
        """Test preparing context for template rendering."""
        # Configure the mocks to return proper string values
        self.document.correspondent.name = "Test Correspondent"
        self.document.document_type.name = "Test Type"

        context = self.service.prepare_context(self.document)

        self.assertEqual(context["document"], self.document)
        self.assertEqual(context["tag_names"], ["tag1", "tag2"])
        self.assertEqual(context["correspondent"], "Test Correspondent")
        self.assertEqual(context["document_type"], "Test Type")
        self.assertIn("custom_fields", context)

        # Test signal emission
        self.service.signals.emit.assert_called_once_with(
            "enrichment.prepare_context",
            args=context,
            return_type=dict
        )

    @patch.object(TemplateLoader, 'render_template')
    def test_render_prompt(self, mock_render):
        """Test rendering a prompt for a document."""
        mock_render.return_value = "Test prompt"

        # Configure the mocks to return proper string values
        self.document.correspondent.name = "Test Correspondent"
        self.document.document_type.name = "Test Type"

        prompt = self.service.render_prompt(self.document, self.config)

        mock_render.assert_called_once_with(
            self.config.template_name,
            self.config.template_dir,
            document=self.document,
            tag_names=["tag1", "tag2"],
            correspondent="Test Correspondent",
            document_type="Test Type",
            custom_fields={}
        )

        self.assertEqual(prompt, "Test prompt")

        # Test signal emission
        self.service.signals.emit.assert_called_with(
            "enrichment.render_prompt",
            args="Test prompt",
            kwargs={"document": self.document, "config": self.config},
            return_type=str
        )

    @patch('fitz.open')
    def test_extract_images_from_pdf(self, mock_open):
        """Test extracting images from a PDF."""
        # Mock PDF document
        mock_pdf = Mock()
        mock_open.return_value = mock_pdf

        # Mock PDF page
        mock_page = Mock()
        # Use __getitem__ as a mock method to avoid AttributeError
        mock_pdf.__getitem__ = Mock(return_value=mock_page)

        # Properly set up __len__ as a method
        mock_pdf.__len__ = Mock(return_value=1)
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]

        # Mock image extraction
        mock_pdf.extract_image.return_value = {"image": b"test image"}

        result = self.service.extract_images_from_pdf(b"test pdf", max_images=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], b"test image")
        mock_open.assert_called_once_with(stream=b"test pdf", filetype="pdf")

    @patch('fitz.open')
    def test_extract_images_from_pdf_no_images(self, mock_open):
        """Test extracting images when PDF has no images."""
        # Mock PDF document
        mock_pdf = Mock()
        mock_open.return_value = mock_pdf

        # Mock PDF page
        mock_page = Mock()
        # Use __getitem__ as a mock method to avoid AttributeError
        mock_pdf.__getitem__ = Mock(return_value=mock_page)

        # Properly set up __len__ as a method
        mock_pdf.__len__ = Mock(return_value=1)
        mock_page.get_images.return_value = []

        with self.assertRaises(NoImagesError):
            self.service.extract_images_from_pdf(b"test pdf", max_images=1)

    @patch('fitz.open')
    def test_extract_images_from_pdf_extraction_error(self, mock_open):
        """Test error handling during PDF image extraction."""
        # Mock PDF document
        mock_pdf = Mock()
        mock_open.return_value = mock_pdf

        # Mock PDF page
        mock_page = Mock()
        # Use __getitem__ as a mock method to avoid AttributeError
        mock_pdf.__getitem__ = Mock(return_value=mock_page)

        # Properly set up __len__ as a method
        mock_pdf.__len__ = Mock(return_value=1)
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]

        # Mock extraction error
        mock_pdf.extract_image.side_effect = Exception("Test error")

        with self.assertLogs(level='ERROR') as log:
            with self.assertRaises(DocumentParsingError):
                self.service.extract_images_from_pdf(b"test pdf", max_images=1)
            self.assertIn("Failed to extract image from page 1 of PDF: Test error", log.output[0])
            self.assertIn("Error extracting images from PDF: Test error", log.output[1])

    @patch('PIL.Image.open')
    def test_convert_to_base64_png(self, mock_open):
        """Test converting an image to base64 PNG."""
        # Mock image
        mock_img = Mock()
        mock_open.return_value = mock_img
        mock_img.size = (100, 100)

        # Mock save method to write data to BytesIO
        def mock_save(buf, format):
            buf.write(b"test png data")
        mock_img.save.side_effect = mock_save

        result = self.service.convert_to_base64_png(b"test image")

        self.assertEqual(result, base64.b64encode(b"test png data").decode("utf-8"))
        mock_open.assert_called_once()

    @patch('PIL.Image.open')
    def test_convert_to_base64_png_large_image(self, mock_open):
        """Test converting a large image to base64 PNG with resizing."""
        # Mock image
        mock_img = Mock()
        mock_open.return_value = mock_img
        mock_img.size = (2000, 2000)

        # Mock save method to write data to BytesIO
        def mock_save(buf, format):
            buf.write(b"test png data")
        mock_img.save.side_effect = mock_save

        result = self.service.convert_to_base64_png(b"test image")

        self.assertEqual(result, base64.b64encode(b"test png data").decode("utf-8"))
        mock_open.assert_called_once()
        mock_img.thumbnail.assert_called_once_with((1024, 1024))

    @patch.object(DocumentEnrichmentService, 'convert_to_base64_png')
    def test_standardize_image_contents_direct(self, mock_convert):
        """Test standardizing image contents directly."""
        mock_convert.return_value = "test base64"

        result = self.service.standardize_image_contents(b"test image")

        self.assertEqual(result, ["test base64"])
        mock_convert.assert_called_once_with(b"test image")

    @patch.object(DocumentEnrichmentService, 'convert_to_base64_png')
    @patch.object(DocumentEnrichmentService, 'extract_images_from_pdf')
    def test_standardize_image_contents_pdf(self, mock_extract, mock_convert):
        """Test standardizing PDF image contents."""
        # Set up the mocks correctly - first attempt fails, then reset for next calls
        first_convert = Mock(side_effect=ValueError("Not an image"))
        mock_convert.side_effect = [ValueError("Not an image"), "test base64", "test base64"]

        mock_extract.return_value = [b"pdf image 1", b"pdf image 2"]

        result = self.service.standardize_image_contents(b"test pdf")

        self.assertEqual(result, ["test base64", "test base64"])
        mock_extract.assert_called_once_with(b"test pdf", 2)
        self.assertEqual(mock_convert.call_count, 3)  # One failed attempt + two successful ones

    @patch.object(DocumentEnrichmentService, 'convert_to_base64_png')
    @patch.object(DocumentEnrichmentService, 'extract_images_from_pdf')
    def test_standardize_image_contents_failure(self, mock_extract, mock_convert):
        """Test standardizing content when all methods fail."""
        mock_convert.side_effect = ValueError("Not an image")
        mock_extract.side_effect = NoImagesError("No images")

        result = self.service.standardize_image_contents(b"invalid content")

        self.assertEqual(result, [])

    def test_parse_date_valid(self):
        """Test parsing valid date strings."""
        test_cases = [
            ("2023-01-15", datetime(2023, 1, 15)),
            ("January 15, 2023", datetime(2023, 1, 15)),
            ("15/01/2023", datetime(2023, 1, 15)),
            ("15-Jan-2023", datetime(2023, 1, 15)),
            ("2023.01.15", datetime(2023, 1, 15)),
            ("circa 1950", datetime(1950, 1, 1)),
            ("early 1980s", datetime(1980, 1, 1)),
            ("mid 1970", datetime(1970, 1, 1)),
        ]

        for date_str, expected in test_cases:
            with self.subTest(date_str=date_str):
                result = self.service.parse_date(date_str)
                self.assertEqual(result, expected)

    def test_parse_date_invalid(self):
        """Test parsing invalid date strings."""
        test_cases = [
            None,
            "",
            "unknown date",
            "date unknown",
            "n/a",
            "none",
        ]

        for date_str in test_cases:
            with self.subTest(date_str=date_str):
                result = self.service.parse_date(date_str)
                self.assertIsNone(result)

    @patch.object(DocumentEnrichmentService, 'render_prompt')
    @patch.object(DocumentEnrichmentService, 'get_openai_client')
    @patch.object(DocumentEnrichmentService, 'standardize_image_contents')
    def test_process_document(self, mock_standardize, mock_get_client, mock_render):
        """Test processing a document with OpenAI."""
        # Mock the prompt
        mock_render.return_value = "Test prompt"

        # Mock image standardization
        mock_standardize.return_value = ["test base64"]

        # Mock OpenAI client and response
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_choice = Mock()
        mock_response.choices = [mock_choice]
        mock_choice.message.content = json.dumps({
            "title": "New Title",
            "description": "Test description",
            "date": "2023-01-15",
            "tags": ["tag1", "tag3"],
            "custom_fields": {"field1": "value1"}
        })

        # Process the document
        result = self.service.process_document(self.document, self.config)

        # Check the result
        self.assertTrue(result.success)
        self.assertIsNone(result.error)
        self.assertEqual(result.document, self.document)
        self.assertEqual(result.raw_response, mock_choice.message.content)
        self.assertIsInstance(result.parsed_response, dict)

        # Verify the API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]["model"], self.config.model)
        self.assertEqual(call_args[1]["max_tokens"], self.config.max_tokens)

        # Verify image processing
        mock_standardize.assert_called_once()

    @patch.object(DocumentEnrichmentService, 'render_prompt')
    @patch.object(DocumentEnrichmentService, 'get_openai_client')
    def test_process_document_no_content(self, mock_get_client, mock_render):
        """Test processing a document with no content."""
        self.document.content = None

        result = self.service.process_document(self.document, self.config)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Document has no content")
        mock_get_client.assert_not_called()
        mock_render.assert_not_called()

    @patch.object(DocumentEnrichmentService, 'render_prompt')
    @patch.object(DocumentEnrichmentService, 'get_openai_client')
    def test_process_document_unsupported_format(self, mock_get_client, mock_render):
        """Test processing a document with unsupported format."""
        self.document.original_filename = "test.xyz"

        result = self.service.process_document(self.document, self.config)

        self.assertFalse(result.success)
        self.assertIn("Unsupported file format", result.error)
        mock_get_client.assert_not_called()
        mock_render.assert_not_called()

    @patch.object(DocumentEnrichmentService, 'render_prompt')
    @patch.object(DocumentEnrichmentService, 'get_openai_client')
    def test_process_document_api_error(self, mock_get_client, mock_render):
        """Test handling API errors during document processing."""
        # Mock the prompt
        mock_render.return_value = "Test prompt"

        # Mock OpenAI client with error
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Create a proper APIConnectionError with the required 'request' parameter
        mock_request = Mock()
        error = openai.APIConnectionError(request=mock_request)
        error.message = "Connection error."  # Set the message attribute
        mock_client.chat.completions.create.side_effect = error

        # Process the document
        with self.assertLogs(level='ERROR') as log:
            result = self.service.process_document(self.document, self.config)

            # Check the logs
            self.assertIn("Error extracting images from PDF: Failed to open stream", log.output[0])

        # Check the result
        self.assertFalse(result.success)
        self.assertIn("API Connection Error", result.error)

    def test_apply_enrichment_success(self):
        """Test applying enrichment results to a document."""
        # Create a result with parsed response
        result = EnrichmentResult(
            document=self.document,
            raw_response='{"title": "New Title", "date": "2023-01-15", "tags": ["tag1", "tag3"], "description": "Test description", "custom_fields": {"field1": "value1"}}',
            parsed_response={
                "title": "New Title",
                "date": "2023-01-15",
                "tags": ["tag1", "tag3"],
                "description": "Test description",
                "custom_fields": {"field1": "value1"}
            },
            success=True
        )

        # Apply the enrichment
        with patch.object(self.service, 'parse_date') as mock_parse_date:
            mock_parse_date.return_value = datetime(2023, 1, 15)
            updated_doc = self.service.apply_enrichment(result)

        # Check document updates
        self.assertEqual(updated_doc, self.document)
        self.document.add_tag.assert_called_with("tag3")
        self.document.set_custom_field.assert_called_with("field1", "value1")
        mock_parse_date.assert_called_with("2023-01-15")

    def test_apply_enrichment_custom_signal(self):
        """Test applying enrichment with a custom signal handler."""
        # Create a result
        result = EnrichmentResult(
            document=self.document,
            parsed_response={"title": "New Title"},
            success=True
        )

        # Mock signal to return a custom document
        custom_doc = Mock(spec=Document)
        self.service.signals.emit.return_value = custom_doc

        # Apply the enrichment
        updated_doc = self.service.apply_enrichment(result)

        # Check that the custom document was returned
        self.assertEqual(updated_doc, custom_doc)
        self.service.signals.emit.assert_called_with(
            "enrichment.apply_result",
            args=self.document,
            kwargs={"result": result},
        )

    def test_apply_enrichment_no_success(self):
        """Test applying enrichment when result is not successful."""
        # Create a failed result
        result = EnrichmentResult(
            document=self.document,
            success=False,
            error="Test error"
        )

        # Apply the enrichment
        updated_doc = self.service.apply_enrichment(result)

        # Check that document was not modified
        self.assertEqual(updated_doc, self.document)
        self.document.add_tag.assert_not_called()
        self.document.set_custom_field.assert_not_called()

    def test_apply_enrichment_summary(self):
        """Test applying a summary enrichment."""
        # Create a result with summary
        result = EnrichmentResult(
            document=self.document,
            parsed_response={"summary": "Test summary"},
            success=True
        )

        # Apply the enrichment
        updated_doc = self.service.apply_enrichment(result)

        # Check that content was updated with summary
        self.assertIn("SUMMARY:", self.document.content)
        self.assertIn("Test summary", self.document.content)
