"""
Describe documents with AI in Paperless-ngx.

This script uses the document enrichment service to generate descriptions for documents stored in a
Paperless-ngx instance. It leverages the same code used by the API to process documents, ensuring
consistency between CLI and API functionality.

Usage:
    $ python describe.py --tag needs-description
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from datetime import date
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import fitz  # type: ignore
from jinja2 import Environment, FileSystemLoader
from PIL import Image, UnidentifiedImageError
import openai

import requests
from alive_progress import alive_bar  # type: ignore
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
from paperap.const import EnrichmentConfig
from paperap.client import PaperlessClient
from paperap.exceptions import DocumentParsingError, NoImagesError
from paperap.models import Document, EnrichmentResult
from paperap.scripts.utils import ProgressBar, setup_logging
from paperap.services.enrichment import DocumentEnrichmentService
from paperap.settings import Settings

logger = logging.getLogger(__name__)


class ScriptDefaults(StrEnum):
    NEEDS_DESCRIPTION = "needs-description"
    DESCRIBED = "described"
    NEEDS_TITLE = "needs-title"
    NEEDS_DATE = "needs-date"
    MODEL = "gpt-4o-mini"


# Current version of the describe script
SCRIPT_VERSION = "0.3.0"


class DescribePhotos(BaseModel):
    """
    Describes photos in the Paperless NGX instance using a language model.

    This class uses the DocumentEnrichmentService to analyze documents and generate
    descriptions, titles, dates, and tags.

    Attributes:
        max_threads (int): Maximum number of threads to use for processing.
        paperless_tag (str | None): Tag to filter documents for description.
        template_name (str): Name of the template to use for description generation.
        client (PaperlessClient): Client for interacting with the Paperless-NgX API.
        _enrichment_service (DocumentEnrichmentService | None): Service for document enrichment.
        _progress_bar (ProgressBar | None): Progress bar for tracking processing status.

    Example:
        >>> client = PaperlessClient(settings)
        >>> describer = DescribePhotos(client=client)
        >>> describer.describe_documents()

    Notes:
        Custom templates can be provided by setting the PAPERAP_TEMPLATE_DIR
        environment variable or passing template_dir to the Settings constructor.

    """

    max_threads: int = 0
    paperless_tag: str | None = Field(default=ScriptDefaults.NEEDS_DESCRIPTION)
    template_name: str = Field(default="photo")
    client: PaperlessClient
    prompt: str | None = Field(default=None)
    _enrichment_service: DocumentEnrichmentService | None = PrivateAttr(default=None)
    _progress_bar: ProgressBar | None = PrivateAttr(default=None)
    _jinja_env: Environment | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def progress_bar(self) -> ProgressBar:
        if not self._progress_bar:
            self._progress_bar = alive_bar(title="Running", unknown="waves")  # pyright: ignore[reportAttributeAccessIssue]
        return self._progress_bar  # type: ignore # pyright not handling the protocol correctly, not sure why

    @property
    def enrichment_service(self) -> DocumentEnrichmentService:
        """Get or create the document enrichment service."""
        if not self._enrichment_service:
            self._enrichment_service = DocumentEnrichmentService(api_key=self.client.settings.openai_key, api_url=self.client.settings.openai_url)
        return self._enrichment_service

    @field_validator("max_threads", mode="before")
    @classmethod
    def validate_max_threads(cls, value: Any) -> int:
        # Sensible default
        if not value:
            # default is between 1-4 threads. More than 4 presumptively stresses the HDD non-optimally.
            if not (cpu_count := os.cpu_count()):
                cpu_count = 1
            return max(1, min(4, round(cpu_count / 2)))

        if value < 1:
            raise ValueError("max_threads must be a positive integer.")
        return int(value)

    @property
    def jinja_env(self) -> Environment:
        if not self._jinja_env:
            # If template_dir is provided in settings, use that
            if self.client.settings.template_dir:
                templates_path = Path(self.client.settings.template_dir)
            else:
                # Otherwise use the default path
                templates_path = Path(__file__).parent / "templates"
            self._jinja_env = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=True)
        return self._jinja_env

    def choose_template(self, document: Document) -> str:
        """
        Choose a Jinja template for a document.

        Args:
            document (Document): The document for which to choose a template.

        Returns:
            str: The name of the Jinja template to use.

        """
        return "photo.jinja"

    def get_prompt(self, document: Document) -> str:
        """
        Generate a prompt to send to OpenAI using a Jinja template.

        Args:
            document (Document): The document for which to generate a prompt.

        Returns:
            str: The generated prompt.

        Raises:
            ValueError: If the prompt generation fails.

        """
        if self.prompt:
            return self.prompt

        template_name = self.choose_template(document)
        template_path = f"templates/{template_name}"
        logger.debug("Using template: %s", template_path)
        template = self.jinja_env.get_template(template_path)

        if not (description := template.render(document=document)):
            raise ValueError("Failed to generate prompt.")

        return description

    def extract_images_from_pdf(self, pdf_bytes: bytes, max_images: int = 2) -> list[bytes]:
        """
        Extract images from a PDF file.

        Args:
            pdf_bytes (bytes): The PDF file content as bytes.
            max_images (int): Maximum number of images to extract.

        Returns:
            list[bytes]: A list of extracted images as bytes.

        Raises:
            DocumentParsingError: If an error occurs during image extraction.
            NoImagesError: If no images are found in the PDF.

        Example:
            >>> with open("document.pdf", "rb") as f:
            >>>     pdf_bytes = f.read()
            >>> images = describer.extract_images_from_pdf(pdf_bytes)

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
                        logger.error(
                            "Failed to extract one image from page %s of PDF. Result count %s: %s",
                            page_number + 1,
                            count,
                            e,
                        )
                        if count < 1:
                            raise

        except Exception as e:
            logger.error(f"extract_images_from_pdf: Error extracting image from PDF: {e}")
            raise DocumentParsingError("Error extracting image from PDF.") from e

        if not results:
            if image_count < 1:
                raise NoImagesError("No images found in the PDF")
            raise DocumentParsingError("Unable to extract images from PDF.")

        return results

    def parse_date(self, date_str: str) -> date | None:
        """
        Parse a date string into a date object.

        Args:
            date_str (str): The date string to parse.

        Returns:
            date | None: The parsed date or None if parsing fails.

        Example:
            >>> parsed_date = describer.parse_date("2025-03-24")
            >>> print(parsed_date)

        """
        # Use the service's parse_date method and convert to date if needed
        dt = self.enrichment_service.parse_date(date_str)
        if dt is None:
            return None
        return dt.date() if hasattr(dt, "date") else dt

    def standardize_image_contents(self, content: bytes) -> list[str]:
        """
        Standardize image contents to base64-encoded PNG format.

        Args:
            content (bytes): The image content as bytes.

        Returns:
            list[str]: A list of base64-encoded PNG images.

        Example:
            >>> with open("image.jpg", "rb") as f:
            >>>     image_bytes = f.read()
            >>> png_images = describer.standardize_image_contents(image_bytes)

        """
        try:
            return [self._convert_to_png(content)]
        except Exception as e:
            logger.debug(f"Failed to convert contents to png, will try other methods: {e}")

        # Interpret it as a pdf
        if image_contents_list := self.extract_images_from_pdf(content):
            return [self._convert_to_png(image) for image in image_contents_list]

        return []

    def _convert_to_png(self, content: bytes) -> str:
        img = Image.open(BytesIO(content))

        # Resize large images
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024))

        # Re-save it as PNG in-memory
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Convert to base64
        return base64.b64encode(buf.read()).decode("utf-8")

    def _send_describe_request(self, content: bytes | list[bytes], document: Document) -> str | None:
        """
        Send an image description request to OpenAI.

        Args:
            content: Document content as bytes or list of bytes
            document: The document to describe

        Returns:
            str: The description generated by OpenAI

        """
        description: str | None = None
        if not isinstance(content, list):
            content = [content]

        try:
            # Convert all images to standardized format
            images = []
            for image_content in content:
                images.extend(self.standardize_image_contents(image_content))

            if not images:
                raise NoImagesError("No images found to describe.")

            message_contents: list[dict[str, Any]] = [
                {
                    "type": "text",
                    "text": self.get_prompt(document),
                }
            ]

            for image in images:
                message_contents.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image}"},
                    }
                )

            # Get OpenAI client from the enrichment service
            openai_client = self.enrichment_service.get_openai_client(
                EnrichmentConfig(template_name=self.template_name, model=self.client.settings.openai_model or ScriptDefaults.MODEL)
            )

            response = openai_client.chat.completions.create(
                model=self.client.settings.openai_model or ScriptDefaults.MODEL,
                messages=[
                    {"role": "user", "content": message_contents}  # type: ignore
                ],
                max_tokens=500,
            )
            description = response.choices[0].message.content
            logger.debug(f"Generated description: {description}")

        except fitz.FileDataError as fde:
            logger.error(
                "Failed to generate description due to error reading file #%s: %s -> %s",
                document.id,
                document.original_filename,
                fde,
            )

        except ValueError as ve:
            logger.warning(
                "Failed to generate description for document #%s: %s. Continuing with next image -> %s",
                document.id,
                document.original_filename,
                ve,
            )

        except UnidentifiedImageError as uii:
            logger.warning(
                "Failed to identify image format for document #%s: %s. Continuing with next image -> %s",
                document.id,
                document.original_filename,
                uii,
            )

        except openai.APIConnectionError as ace:
            logger.error(
                "API Connection Error. Is the OpenAI API URL correct? URL: %s, model: %s -> %s",
                self.client.settings.openai_url,
                self.client.settings.openai_model or ScriptDefaults.MODEL,
                ace,
            )
            raise

        return description

    def convert_image_to_jpg(self, bytes_content: bytes) -> bytes:
        """
        Convert an image to JPEG format.

        Args:
            bytes_content (bytes): The image content as bytes.

        Returns:
            bytes: The image content in JPEG format.

        Raises:
            Exception: If the conversion fails.

        Example:
            >>> with open("image.png", "rb") as f:
            >>>     png_bytes = f.read()
            >>> jpeg_bytes = describer.convert_image_to_jpg(png_bytes)

        """
        try:
            img = Image.open(BytesIO(bytes_content))
            buf = BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            return buf.read()
        except Exception as e:
            logger.error(f"Failed to convert image to JPEG: {e}")
            raise

    def describe_document(self, document: Document) -> bool:
        """
        Describe a single document using the document enrichment service.

        The document object passed in will be updated with the description.

        Args:
            document (Document): The document to describe.

        Returns:
            bool: True if the document was successfully described, False otherwise.

        Raises:
            requests.RequestException: If a request error occurs.

        Example:
            >>> document = client.documents.get(123)
            >>> success = describer.describe_document(document)
            >>> print("Description successful:", success)

        """
        try:
            logger.debug(f"Describing document {document.id}...")

            # Create enrichment config
            config = EnrichmentConfig(
                template_name=self.template_name,
                model=self.client.settings.openai_model or ScriptDefaults.MODEL,
                vision=True,
                extract_images=True,
                max_images=2,
            )

            try:
                # Process the document
                result = self.enrichment_service.process_document(document, config)

                # Handle the result
                if not result.success:
                    logger.error(f"Failed to describe document {document.id}: {result.error}")
                    return False
            except (NoImagesError, DocumentParsingError) as e:
                logger.error(f"Failed to describe document {document.id}: {e}")
                return False

            # Add appropriate tags
            if result.success:
                document.remove_tag(ScriptDefaults.NEEDS_DESCRIPTION)
                document.add_tag(ScriptDefaults.DESCRIBED)

                # Save the document
                document.save()

            return result.success

        except requests.RequestException as e:
            logger.error(f"Failed to describe document {document.id}: {e}")
            raise

        return False

    def process_response(self, response: str, document: Document) -> Document:
        """
        Process the response from OpenAI and update the document.

        Args:
            response (str): The response from OpenAI.
            document (Document): The document to update.

        Returns:
            Document: The updated document with the description added.

        Example:
            >>> response = '{"title": "Sample Title", "description": "Sample Description"}'
            >>> updated_document = describer.process_response(response, document)
            >>> print(updated_document.title)

        """
        # Attempt to parse response as json
        try:
            if not (parsed_response := json.loads(response)):
                logger.debug("Unable to process response after failed json parsing")
                return document
        except json.JSONDecodeError as jde:
            logger.error("Failed to parse response as JSON: %s", jde)
            return document

        # Check if parsed_response is a dictionary
        if not isinstance(parsed_response, dict):
            logger.error(
                "Parsed response not a dictionary. Saving response raw to document.content. Document #%s: %s",
                document.id,
                document.original_filename,
            )
            document.append_content(response)
            return document

        # Attempt to grab "title", "description", "tags", "date" from parsed_response
        title = parsed_response.get("title", None)
        description = parsed_response.get("description", None)
        summary = parsed_response.get("summary", None)
        content = parsed_response.get("content", None)
        tags = parsed_response.get("tags", None)
        date = parsed_response.get("date", None)
        full_description = f"""AI IMAGE DESCRIPTION (v{SCRIPT_VERSION}):
            The following description was provided by an Artificial Intelligence (GPT-4o by OpenAI).
            It may not be fully accurate. Its purpose is to provide keywords and context
            so that the document can be more easily searched.
            Suggested Title: {title}
            Inferred Date: {date}
            Suggested Tags: {tags}
            Previous Title: {document.title}
            Previous Date: {document.created}
        """

        if summary:
            full_description += f"\n\nSummary: {summary}"
        if content:
            full_description += f"\n\nContent: {content}"
        if description:
            full_description += f"\n\nDescription: {description}"
        if not any([description, summary, content]):
            full_description += f"\n\nFull AI Response: {parsed_response}"

        if title and ScriptDefaults.NEEDS_TITLE in document.tag_names:
            try:
                document.title = str(title)
                document.remove_tag(ScriptDefaults.NEEDS_TITLE)
            except Exception as e:
                logger.error(
                    "Failed to update document title. Document #%s: %s -> %s",
                    document.id,
                    document.original_filename,
                    e,
                )

        if date and "ScriptDefaults.NEEDS_DATE" in document.tag_names:
            try:
                document.created = date  # type: ignore # pydantic will handle casting
                document.remove_tag("ScriptDefaults.NEEDS_DATE")
            except Exception as e:
                logger.error(
                    "Failed to update document date. Document #%s: %s -> %s",
                    document.id,
                    document.original_filename,
                    e,
                )

        # Append the description to the document
        document.content = full_description
        document.remove_tag("ScriptDefaults.NEEDS_DESCRIPTION")
        document.add_tag("described")

        logger.debug(f"Successfully described document {document.id}")
        return document

    def describe_documents(self, documents: list[Document] | None = None) -> list[Document]:
        """
        Describe a list of documents using the document enrichment service.

        Args:
            documents (list[Document] | None): The documents to describe. If None, fetches documents
                from the Paperless NGX instance using the specified tag.

        Returns:
            list[Document]: The documents with the descriptions added.

        Example:
            >>> documents = client.documents.filter(tag_name="needs-description")
            >>> described_documents = describer.describe_documents(documents)
            >>> print(f"Described {len(described_documents)} documents")

        """
        logger.info("Fetching documents to describe...")
        if documents is None:
            documents = list(self.client.documents().filter(tag_name=self.paperless_tag))

        total = len(documents)
        logger.info(f"Found {total} documents to describe")

        results = []
        with alive_bar(total=total, title="Describing documents", bar="classic") as self._progress_bar:
            for document in documents:
                if self.describe_document(document):
                    results.append(document)
                self._progress_bar()  # type: ignore
        return results


class ArgNamespace(argparse.Namespace):
    """
    A custom namespace class for argparse.

    Attributes:
        url (str): The base URL of the Paperless NGX instance.
        key (str): The API token for the Paperless NGX instance.
        model (str | None): The OpenAI model to use.
        openai_url (str | None): The base URL for the OpenAI API.
        tag (str): Tag to filter documents.
        prompt (str | None): Prompt to use for OpenAI.
        verbose (bool): Verbose output flag.

    """

    url: str
    key: str
    model: str | None = None
    openai_url: str | None = None
    tag: str
    prompt: str | None = None
    verbose: bool = False


def main() -> None:
    """
    Run the script.

    This function sets up logging, parses command-line arguments, and initiates the document
    description process using the DescribePhotos class.

    Raises:
        SystemExit: If required environment variables are not set or an error occurs.

    Example:
        To run the script from the command line:
        $ python describe.py --url http://paperless.local:8000 --key your_api_token

    """
    logger = setup_logging()
    try:
        load_dotenv()

        parser = argparse.ArgumentParser(description="Describe documents with AI in Paperless-ngx")
        parser.add_argument("--url", type=str, default=None, help="The base URL of the Paperless NGX instance")
        parser.add_argument("--key", type=str, default=None, help="The API token for the Paperless NGX instance")
        parser.add_argument("--model", type=str, default=None, help="The OpenAI model to use")
        parser.add_argument("--openai-url", type=str, default=None, help="The base URL for the OpenAI API")
        parser.add_argument("--tag", type=str, default=ScriptDefaults.NEEDS_DESCRIPTION, help="Tag to filter documents")
        parser.add_argument("--template", type=str, default="photo", help="Template name to use for description")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

        args = parser.parse_args(namespace=ArgNamespace())

        if args.verbose:
            logger.setLevel(logging.DEBUG)

        if not args.url:
            logger.error("PAPERLESS_URL environment variable is not set.")
            sys.exit(1)

        if not args.key:
            logger.error("PAPERLESS_KEY environment variable is not set.")
            sys.exit(1)

        # Exclude None, so pydantic settings loads from defaults for an unset param
        config = {
            k: v
            for k, v in {
                "base_url": args.url,
                "token": args.key,
                "openai_url": args.openai_url,
                "openai_model": args.model,
            }.items()
            if v is not None
        }
        # Cast to Any to avoid type checking issues with **kwargs
        settings = Settings(**cast(Any, config))
        client = PaperlessClient(settings)

        paperless = DescribePhotos(client=client, template_name=args.template)

        logger.info(f"Starting document description process with model: {paperless.client.settings.openai_model}")
        results = paperless.describe_documents()

        if results:
            logger.info(f"Successfully described {len(results)} documents")
        else:
            logger.info("No documents described.")

    except KeyboardInterrupt:
        logger.info("Script cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
