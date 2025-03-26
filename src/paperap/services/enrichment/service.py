"""
Document enrichment service using LLMs.

This module provides the core functionality for enriching documents with
descriptions, summaries, and other metadata using LLMs.

Services in this module can be used directly or through DocumentQuerySet methods
like `describe()`, `summarize()`, and `analyze()`.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol, cast, override, TYPE_CHECKING

import dateparser
import fitz  # type: ignore
import openai
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field

from paperap.exceptions import DocumentParsingError, NoImagesError
from paperap.const import EnrichmentConfig
from paperap.signals import SignalRegistry
from paperap.models.enrichment.result import EnrichmentResult

if TYPE_CHECKING:
    from paperap.models.document import Document

logger = logging.getLogger(__name__)

# Environment variable for template directory
TEMPLATE_DIR_ENV = "PAPERAP_TEMPLATE_DIR"
DEFAULT_TEMPLATES_PATH = str(Path(__file__).parent / "templates")

# File formats accepted by the enrichment services
ACCEPTED_IMAGE_FORMATS = ["png", "jpg", "jpeg", "gif", "tif", "tiff", "bmp", "webp", "pdf"]
# File formats accepted by OpenAI's vision models
OPENAI_ACCEPTED_FORMATS = ["png", "jpg", "jpeg", "gif", "webp"]


class TemplateLoader:
    """
    Template loader for document enrichment services.

    This class manages loading templates from various sources, including
    embedded templates, custom directories, and environment variables.
    """

    @override
    def __init__(self) -> None:
        self._environments: dict[str, Environment] = {}
        super().__init__()

    def get_environment(self, template_dir: str | None = None) -> Environment:
        """
        Get a Jinja environment for the specified template directory.

        Args:
            template_dir: Optional custom directory for templates

        Returns:
            A Jinja environment configured for the template directory

        """
        # Check for template dir in env var if not specified
        template_dir = template_dir or os.environ.get(TEMPLATE_DIR_ENV)

        if not template_dir:
            # Use the default embedded templates
            template_dir = DEFAULT_TEMPLATES_PATH

        if template_dir not in self._environments:
            self._environments[template_dir] = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )

        return self._environments[template_dir]

    def render_template(self, template_name: str, template_dir: str | None = None, **context: Any) -> str:
        """
        Render a template with the provided context.

        Args:
            template_name: Name of the template to render
            template_dir: Optional custom directory for templates
            **context: Context variables for the template

        Returns:
            The rendered template as a string

        """
        env = self.get_environment(template_dir)
        template = env.get_template(f"{template_name}.jinja")
        return template.render(**context)


# Global template loader instance
template_loader = TemplateLoader()


class DocumentEnrichmentService:
    """
    Service for enriching documents with descriptions and summaries.

    This service uses OpenAI's language models to analyze documents and generate
    descriptions, summaries, and other metadata.
    """

    # Class-level signal registry
    signals = SignalRegistry()

    @override
    def __init__(self, api_key: str | None = None, api_url: str | None = None) -> None:
        """
        Initialize the document enrichment service.

        Args:
            api_key: Optional OpenAI API key
            api_url: Optional custom OpenAI API URL

        """
        self._openai_client: OpenAI | None = None
        self._api_key = api_key
        self._api_url = api_url
        self._ensure_default_templates()
        super().__init__()

    def _ensure_default_templates(self) -> None:
        """
        Ensure default templates are available.

        This method checks for the existence of default templates and creates them if necessary.
        """
        import pkgutil
        from pathlib import Path

        # Directory where templates should be stored
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        # List of default templates
        default_templates = [
            "document_description.jinja",
            "document_summary.jinja",
            "document_analysis.jinja",
        ]

        # Check if templates exist, if not create them from package resources
        for template_name in default_templates:
            template_path = template_dir / template_name
            if not template_path.exists():
                # Try to load from package resources
                template_content = pkgutil.get_data("paperap.services.enrichment", f"templates/{template_name}")

                if template_content:
                    # Write template to file
                    template_path.write_bytes(template_content)
                else:
                    logger.warning(f"Default template {template_name} not found in package resources")

    def get_openai_client(self, config: EnrichmentConfig) -> OpenAI:
        """
        Get an OpenAI client using the provided configuration.

        Args:
            config: The enrichment configuration

        Returns:
            An OpenAI client

        """
        if self._openai_client is None:
            kwargs: dict[str, Any] = {}

            # Priority: explicitly passed key > config key > instance key
            api_key = config.api_key or self._api_key
            if api_key:
                kwargs["api_key"] = api_key

            # Priority: explicitly passed URL > config URL > instance URL
            api_url = config.api_url or self._api_url
            if api_url:
                kwargs["base_url"] = api_url

            self._openai_client = OpenAI(**kwargs)

        return self._openai_client

    def prepare_context(self, document: "Document") -> dict[str, Any]:
        """
        Prepare the template context for a document.

        Args:
            document: The document to prepare context for

        Returns:
            A dictionary with context variables for the template

        """
        # Base context with document and metadata
        context: dict[str, Any] = {
            "document": document,
            "tag_names": document.tag_names,
            "correspondent": document.correspondent.name if document.correspondent else None,
            "document_type": document.document_type.name if document.document_type else None,
        }

        # Add custom fields if available
        custom_fields = {}
        for field in document.custom_fields:
            custom_fields[field.name] = document.custom_field_value(field.id)
        context["custom_fields"] = custom_fields

        # Allow context modification through signals
        modified_context = self.signals.emit("enrichment.prepare_context", args=context, return_type=dict)

        return modified_context or context

    def render_prompt(self, document: "Document", config: EnrichmentConfig) -> str:
        """
        Render a prompt template for a document.

        Args:
            document: The document to render the prompt for
            config: The enrichment configuration

        Returns:
            The rendered prompt as a string

        """
        context = self.prepare_context(document)
        if not config.template_name:
            raise ValueError("Template name is required in the enrichment configuration.")
        prompt = template_loader.render_template(config.template_name, config.template_dir, **context)

        # Allow prompt modification through signals
        modified_prompt = self.signals.emit(
            "enrichment.render_prompt",
            args=prompt,
            kwargs={"document": document, "config": config},
            return_type=str,
        )

        return modified_prompt or prompt

    def extract_images_from_pdf(self, pdf_bytes: bytes, max_images: int = 2) -> list[bytes]:
        """
        Extract images from a PDF file.

        Args:
            pdf_bytes: The PDF content as bytes
            max_images: Maximum number of images to extract

        Returns:
            A list of extracted images as bytes

        Raises:
            DocumentParsingError: If image extraction fails
            NoImagesError: If no images are found

        """
        results: list[bytes] = []
        image_count = 0

        try:
            # Open the PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page_number in range(len(pdf_document)):
                if len(results) >= max_images:
                    break

                page = pdf_document[page_number]
                images = page.get_images(full=True)

                if not images:
                    continue

                for image in images:
                    image_count += 1
                    if len(results) >= max_images:
                        break

                    try:
                        xref = image[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        results.append(image_bytes)
                        logger.debug(f"Extracted image from page {page_number + 1} of the PDF.")
                    except Exception as e:
                        count = len(results)
                        logger.error(f"Failed to extract image from page {page_number + 1} of PDF: {e}")
                        if count < 1:
                            raise

        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")
            raise DocumentParsingError("Error extracting images from PDF.") from e

        if not results:
            if image_count < 1:
                raise NoImagesError("No images found in the PDF")
            raise DocumentParsingError("Unable to extract images from PDF.")

        return results

    def convert_to_base64_png(self, image_bytes: bytes) -> str:
        """
        Convert image bytes to a base64-encoded PNG string.

        Args:
            image_bytes: The image content as bytes

        Returns:
            A base64-encoded PNG string

        Raises:
            UnidentifiedImageError: If the image format cannot be identified

        """
        img = Image.open(BytesIO(image_bytes))

        # Resize large images
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024))

        # Save as PNG
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Convert to base64
        return base64.b64encode(buf.read()).decode("utf-8")

    def standardize_image_contents(self, content: bytes, max_images: int = 2) -> list[str]:
        """
        Standardize image contents to base64-encoded PNG format.

        Args:
            content: The image or document content as bytes
            max_images: Maximum number of images to extract

        Returns:
            A list of base64-encoded PNG images

        """
        try:
            # First try to convert directly
            return [self.convert_to_base64_png(content)]
        except Exception as e:
            logger.debug(f"Failed to convert contents to PNG, trying other methods: {e}")

        # Try to extract images from PDF
        try:
            images = self.extract_images_from_pdf(content, max_images)
            return [self.convert_to_base64_png(img) for img in images]
        except Exception as e:
            logger.debug(f"Failed to extract images from PDF: {e}")

        return []

    def process_document(
        self,
        document: "Document",
        config: EnrichmentConfig,
        expand_descriptions: bool = False,
    ) -> EnrichmentResult:
        """
        Process a document with OpenAI.

        Args:
            document: The document to process
            config: The enrichment configuration
            expand_descriptions: Whether to expand descriptions with synonyms for better search

        Returns:
            The enrichment result

        """
        # Default result with the document
        result = EnrichmentResult(document=document)

        try:
            # Get the document content
            if not (content := document.content):
                result.success = False
                result.error = "Document has no content"
                return result

            # Check if the document format is supported for vision
            if config.vision:
                original_filename = (document.original_filename or "").lower()
                if not any(original_filename.endswith(ext) for ext in ACCEPTED_IMAGE_FORMATS):
                    result.success = False
                    result.error = f"Unsupported file format for vision: {original_filename}"
                    return result

            # Render the prompt
            prompt = self.render_prompt(document, config)

            # Convert content to bytes if it's a string
            content_bytes = content if isinstance(content, bytes) else content.encode("utf-8")

            # Process with OpenAI
            openai_client = self.get_openai_client(config)

            # Prepare message contents
            message_contents: list[dict[str, Any]] = [
                {
                    "type": "text",
                    "text": prompt,
                }
            ]

            # Add images if using vision
            if config.vision and config.extract_images:
                try:
                    images = self.standardize_image_contents(content_bytes, config.max_images)

                    if not images:
                        logger.warning(f"No images found in document {document.id}")

                    for image in images:
                        message_contents.append(
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image}"},
                            }
                        )
                except NoImagesError:
                    logger.warning(f"No images found in document {document.id}")
                except DocumentParsingError as e:
                    logger.error(f"Failed to parse document {document.id}: {e}")
                    result.success = False
                    result.error = str(e)
                    return result

            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "user", "content": message_contents}  # type: ignore
                ],
                max_tokens=config.max_tokens,
            )

            # Get the response text
            raw_response = response.choices[0].message.content
            result.raw_response = raw_response

            # Try to parse as JSON
            if raw_response:
                try:
                    result.parsed_response = json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse response as JSON: {raw_response}")

            # Apply the enrichment
            self.apply_enrichment(result, expand_descriptions)

        except openai.APIConnectionError as e:
            logger.error(f"API Connection Error: {e}")
            result.success = False
            result.error = f"API Connection Error: {e}"
        except openai.BadRequestError as e:
            logger.error(f"Bad Request Error: {e}")
            result.success = False
            result.error = f"Bad Request Error: {e}"
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            result.success = False
            result.error = f"Error processing document: {e}"

        return result

    def parse_date(self, date_str: str) -> datetime | None:
        """
        Parse a date string into a datetime object.

        Args:
            date_str: The date string to parse

        Returns:
            The parsed datetime or None if parsing fails

        """
        if not date_str:
            return None

        date_str = str(date_str).strip()

        # "Date unknown" or "Unknown date" or "No date"
        if re.match(r"(date unknown|unknown date|no date|none|unknown|n/?a)$", date_str, re.IGNORECASE):
            return None

        # Handle "circa 1950"
        if matches := re.match(r"((around|circa|mid|early|late|before|after) *)?(\d{4})s?$", date_str, re.IGNORECASE):
            date_str = f"{matches.group(3)}-01-01"

        return dateparser.parse(date_str)

    def expand_description_with_synonyms(self, description: str) -> str:
        """
        Expand a description by generating multiple versions with synonyms.

        This method takes a description and sends it to GPT to create
        alternative versions using synonyms to improve search capabilities.

        Args:
            description: The original description to expand

        Returns:
            A string containing the original description plus expanded versions

        """
        # Skip if no description
        if not description:
            return ""

        try:
            # Create a prompt for GPT to generate synonyms
            prompt = f"""
Please rewrite the following description 3-4 times, using synonyms for key terms to enhance searchability.
Keep each version about the same length as the original, but vary the wording.
Output in the format:
VERSION 1: [rewritten description with synonyms]
VERSION 2: [another rewritten description with different synonyms]
etc.

ORIGINAL DESCRIPTION:
{description}
"""

            # Get the OpenAI client (using a simpler model for synonyms)
            openai_client = self.get_openai_client(EnrichmentConfig(model="gpt-4o-mini"))

            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,  # Allow for longer output to fit multiple versions
            )

            # Get the response text
            expanded_text = response.choices[0].message.content

            # Combine original plus expansions
            result = f"ORIGINAL DESCRIPTION:\n{description}\n\nALTERNATIVE DESCRIPTIONS FOR SEARCH:\n{expanded_text}"
            return result

        except Exception as e:
            logger.error(f"Error expanding description with synonyms: {e}")
            return description  # Return original description on error

    def apply_enrichment(self, result: EnrichmentResult, expand_descriptions: bool = False) -> "Document":
        """
        Apply the enrichment result to the document.

        Args:
            result: The enrichment result
            expand_descriptions: Whether to expand descriptions with synonyms for better search

        Returns:
            The updated document

        """
        document = result.document

        if not result.success or not result.parsed_response:
            return document

        # Signal for customizing how the result is applied
        updated_doc = self.signals.emit(
            "enrichment.apply_result",
            args=document,
            kwargs={"result": result},
        )

        if updated_doc:
            return updated_doc

        # Default implementation
        response = result.parsed_response

        # Update title if available
        if title := response.get("title"):
            document.title = str(title)

        # Update date if available
        if date_str := response.get("date"):
            # Only update if not "Date Unknown" or similar
            if date_str.lower() not in ("date unknown", "unknown", "n/a", "none"):
                try:
                    # Try to parse the date
                    if parsed_date := self.parse_date(date_str):
                        document.created = parsed_date  # type: ignore # pydantic will handle casting
                except Exception as e:
                    logger.error(f"Failed to update document date: {e}")

        # Update tags if available
        if tags := response.get("tags"):
            for tag_name in tags:
                document.add_tag(tag_name)

        # Update custom fields if available
        if custom_fields := response.get("custom_fields"):
            for field_name, field_value in custom_fields.items():
                document.set_custom_field(field_name, field_value)

        # Update description or content
        if description := response.get("description"):
            # Build a comprehensive description
            description_parts = ["AI DOCUMENT DESCRIPTION:"]

            if title := response.get("title"):
                description_parts.append(f"Title: {title}")

            if date := response.get("date"):
                description_parts.append(f"Date: {date}")

            if tags := response.get("tags"):
                description_parts.append(f"Tags: {', '.join(tags)}")

            if document_type := response.get("document_type"):
                description_parts.append(f"Document Type: {document_type}")

            # If expand_descriptions is enabled, generate synonym expansions
            if expand_descriptions:
                expanded_description = self.expand_description_with_synonyms(description)
                description_parts.append(f"\n{expanded_description}")
            else:
                description_parts.append(f"\nDescription:\n{description}")

            # Update document content
            document.content = "\n".join(description_parts)

        # Handle summaries specifically
        if summary := response.get("summary"):
            document.content = f"SUMMARY:\n\n{summary}\n\nORIGINAL CONTENT:\n\n{document.content}"

        return document
