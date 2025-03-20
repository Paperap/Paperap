"""




----------------------------------------------------------------------------

METADATA:

File:    describe.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.8
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import re
import sys
from datetime import date, datetime
from enum import StrEnum
from functools import singledispatchmethod
from io import BytesIO
from pathlib import Path
from typing import Any, Collection, Dict, Iterator, List, Optional, TypeVar, Union, cast

import dateparser
import fitz  # type: ignore
import openai
import openai.types.chat
import requests
from alive_progress import alive_bar  # type: ignore
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from paperap.client import PaperlessClient
from paperap.exceptions import DocumentParsingError, NoImagesError
from paperap.models.document import Document
from paperap.models.document.queryset import DocumentQuerySet
from paperap.models.tag import Tag
from paperap.scripts.utils import ProgressBar, setup_logging
from paperap.settings import Settings

logger = logging.getLogger(__name__)

DESCRIBE_ACCEPTED_FORMATS = ["png", "jpg", "jpeg", "gif", "tif", "tiff", "bmp", "webp", "pdf"]
OPENAI_ACCEPTED_FORMATS = ["png", "jpg", "jpeg", "gif", "webp", "pdf"]
MIME_TYPES = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class ScriptDefaults(StrEnum):
    NEEDS_DESCRIPTION = "needs-description"
    DESCRIBED = "described"
    NEEDS_TITLE = "needs-title"
    NEEDS_DATE = "needs-date"
    MODEL = "gpt-4o-mini"


SCRIPT_VERSION = "0.2.2"


class DescribePhotos(BaseModel):
    """
    Describes photos in the Paperless NGX instance using an LLM (such as OpenAI's GPT-4o-mini model).
    """

    max_threads: int = 0
    paperless_tag: str | None = Field(default=ScriptDefaults.NEEDS_DESCRIPTION)
    prompt: str | None = Field(None)
    client: PaperlessClient
    _jinja_env: Environment | None = PrivateAttr(default=None)
    _progress_bar: ProgressBar | None = PrivateAttr(default=None)
    _progress_message: str | None = PrivateAttr(default=None)
    _openai: OpenAI | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def progress_bar(self) -> ProgressBar:
        if not self._progress_bar:
            self._progress_bar = alive_bar(title="Running", unknown="waves")  # type: ignore
        return self._progress_bar  # type: ignore # pyright not handling the protocol correctly, not sure why

    @property
    def openai_url(self) -> str | None:
        return self.client.settings.openai_url

    @property
    def openai_key(self) -> str | None:
        return self.client.settings.openai_key

    @property
    def openai_model(self) -> str:
        return self.client.settings.openai_model or ScriptDefaults.MODEL

    @property
    def openai(self) -> OpenAI:
        if not self._openai:
            if self.openai_url:
                logger.info("Using custom OpenAI URL: %s", self.openai_url)
                self._openai = OpenAI(api_key=self.openai_key, base_url=self.openai_url)
            else:
                logger.info("Using default OpenAI URL")
                self._openai = OpenAI()
        return self._openai

    @field_validator("max_threads", mode="before")
    @classmethod
    def validate_max_threads(cls, value) -> int:
        # Sensible default
        if not value:
            # default is between 1-4 threads. More than 4 presumptively stresses the HDD non-optimally.
            if not (cpu_count := os.cpu_count()):
                cpu_count = 1
            return max(1, min(4, round(cpu_count / 2)))

        if value < 1:
            raise ValueError("max_threads must be a positive integer.")
        return value

    @property
    def jinja_env(self) -> Environment:
        if not self._jinja_env:
            templates_path = Path(__file__).parent / "templates"
            self._jinja_env = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=True)
        return self._jinja_env

    def choose_template(self, document: Document) -> str:
        """
        Choose a jinja template for a document
        """
        return "photo.jinja"

    def get_prompt(self, document: Document) -> str:
        """
        Generate a prompt to sent to openai using a jinja template.
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
        Extract the first image from a PDF file.

        Args:
            pdf_bytes (bytes): The PDF file content as bytes.

        Returns:
            bytes | None: The first {max_images} images as bytes or None if no image is found.

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
        Parse a date string.

        Args:
            date_str (str): The date string to parse.

        Returns:
            date: The parsed date.

        """
        if not (parsed_date := self.parse_datetime(date_str)):
            return None
        return parsed_date.date()

    def parse_datetime(self, date_str: str) -> datetime | None:
        """
        Parse a date string.

        Args:
            date_str (str): The date string to parse.

        Returns:
            date: The parsed date.

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

        parsed_date = dateparser.parse(date_str)
        if not parsed_date:
            raise ValueError(f"Invalid date format: {date_str=}")
        return parsed_date

    def standardize_image_contents(self, content: bytes) -> list[str]:
        """
        Standardize image contents to base64-encoded PNG format.
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

            message_contents: List[Dict[str, Any]] = [
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

            response = self.openai.chat.completions.create(
                model=self.openai_model,
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
                document.original_file_name,
                fde,
            )

        except ValueError as ve:
            logger.warning(
                "Failed to generate description for document #%s: %s. Continuing with next image -> %s",
                document.id,
                document.original_file_name,
                ve,
            )

        except UnidentifiedImageError as uii:
            logger.warning(
                "Failed to identify image format for document #%s: %s. Continuing with next image -> %s",
                document.id,
                document.original_file_name,
                uii,
            )

        except openai.APIConnectionError as ace:
            logger.error(
                "API Connection Error. Is the OpenAI API URL correct? URL: %s, model: %s -> %s",
                self.openai_url,
                self.openai_model,
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
            bytes: The image content as JPEG.

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
        Describe a single document using OpenAI's GPT-4o model.

        The document object passed in will be updated with the description.

        Args:
            document: The document to describe.

        Returns:
            bool: True if the document was successfully described

        """
        response = None
        try:
            logger.debug(f"Describing document {document.id} using OpenAI...")

            if not (content := document.content):
                logger.error("Document content is empty for document #%s", document.id)
                return False

            # Ensure accepted format
            original_file_name = (document.original_file_name or "").lower()
            if not any(original_file_name.endswith(ext) for ext in DESCRIBE_ACCEPTED_FORMATS):
                logger.error(f"Document {document.id} has unsupported extension: {original_file_name}")
                return False

            try:
                # Convert content to bytes if it's a string
                content_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
                if not (response := self._send_describe_request(content_bytes, document)):
                    logger.error(f"OpenAI returned empty description for document {document.id}.")
                    return False
            except NoImagesError as nie:
                logger.debug(f"No images found in document {document.id}: {nie}")
                return False
            except DocumentParsingError as dpe:
                logger.error(f"Failed to parse document {document.id}: {dpe}")
                return False
            except openai.BadRequestError as e:
                if "invalid_image_format" not in str(e):
                    logger.error(
                        "Failed to generate description for document #%s: %s -> %s",
                        document.id,
                        document.original_file_name,
                        e,
                    )
                    return False

                logger.debug("Bad format for document #%s: %s -> %s", document.id, document.original_file_name, e)
                return False

            # Process the response
            self.process_response(response, document)
        except requests.RequestException as e:
            logger.error(f"Failed to describe document {document.id}. {response=} => {e}")
            raise

        return True

    def process_response(self, response: str, document: Document) -> Document:
        """
        Process the response from OpenAI and update the document.

        Args:
            response (str): The response from OpenAI
            document (Document): The document to update

        Returns:
            Document: The updated document

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
                document.original_file_name,
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
                    document.original_file_name,
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
                    document.original_file_name,
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
        Describe a list of documents using OpenAI's GPT-4o model.

        Args:
            documents (list[Document]): The documents to describe.

        Returns:
            list[Document]: The documents with the descriptions added.

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
                self.progress_bar()
        return results


class ArgNamespace(argparse.Namespace):
    """
    A custom namespace class for argparse.
    """

    url: str
    key: str
    model: str | None = None
    openai_url: str | None = None
    tag: str
    prompt: str | None = None
    verbose: bool = False


def main():
    """
    Run the script.
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
        parser.add_argument("--prompt", type=str, default=None, help="Prompt to use for OpenAI")
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

        paperless = DescribePhotos(client=client, prompt=args.prompt)

        logger.info(f"Starting document description process with model: {paperless.openai_model}")
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
