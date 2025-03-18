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
from functools import singledispatchmethod
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import os
import logging
from typing import Any, Iterator,List
import requests
from alive_progress import alive_bar
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
import openai
import openai.types.chat
from openai import OpenAI
import fitz
from PIL import Image, UnidentifiedImageError
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, date
import dateparser

from paperap.exceptions import NoImagesException, DocumentParsingError
from paperap.scripts.utils import setup_logging
from previoius-project.models import Document, Tag
from previoius-project.models.document import Document
from previoius-project.client import PaperlessClient

logger = logging.getLogger(__name__)

DESCRIBE_ACCEPTED_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'tif', 'tiff', 'bmp', 'webp', 'pdf']
OPENAI_ACCEPTED_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf']
MIME_TYPES = {
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
}

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
TAG_HRSH = 2
TAG_NYS_OMH = 229
DOCUMENT_TYPE_PHOTO = 8
DOCUMENT_TYPE_DETAIL_CLOSEUP = 30
DOCUMENT_TYPE_ITEMS = 11
VERSION = "0.2.2"

class DescribePhotos(BaseModel):
    """
    Describes photos in the Paperless NGX instance using an LLM (such as OpenAI's GPT-4o model).
    """
    max_threads: int = 0
    paperless_url: str = Field(..., env='PAPERLESS_URL')
    paperless_key: str | None = Field(..., env='PAPERLESS_KEY')
    paperless_tag: str | None = Field('needs-description', env='PAPERLESS_TAG')
    openai_key: str | None = Field(default=None, env='PAPERLESS_OPENAI_API_KEY')
    openai_url: str | None = Field(default=None, env='PAPERLESS_OPENAI_URL')
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL, env="PAPERLESS_OPENAI_MODEL")
    force_openai: bool = Field(default=False)
    prompt: str | None = Field(None)
    _jinja_env: Environment | None = PrivateAttr(default=None)
    _progress_bar = PrivateAttr(default=None)
    _progress_message: str | None = PrivateAttr(default=None)
    _openai: OpenAI | None = PrivateAttr(default=None)
    _paperless_client: PaperlessClient | None = PrivateAttr(default=None)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def progress_bar(self) -> alive_bar:
        if not self._progress_bar:
            self._progress_bar = alive_bar(title='Running', unknown='waves')
        return self._progress_bar

    @property
    def paperless_client(self) -> PaperlessClient:
        """Return or initialize the Paperless instance."""
        if not self._paperless_client:
            self._paperless_client = PaperlessClient(self.paperless_url, self.paperless_key)
        return self._paperless_client

    @property
    def openai(self) -> OpenAI:
        if not self._openai:
            if self.force_openai:
                if self.openai_url:
                    # Reset the model for openai
                    self.openai_model = DEFAULT_OPENAI_MODEL
                    self.openai_url = None
                    
            if self.openai_url:
                logger.info('Using custom OpenAI URL: %s', self.openai_url)
                self._openai = OpenAI(api_key=self.openai_key, base_url=self.openai_url)
            else:
                logger.info('Using default OpenAI URL')
                self._openai = OpenAI()
        return self._openai

    @property
    def pc(self) -> PaperlessClient:
        return self.paperless_client

    @field_validator('max_threads', mode='before')
    def validate_max_threads(cls, value):
        # Sensible default
        if not value:
            # default is between 1-4 threads. More than 4 presumptively stresses the HDD non-optimally.
            if not (cpu_count := os.cpu_count()):
                cpu_count = 1
            return max(1, min(4, round(cpu_count / 2)))
            
        if value < 1:
            raise ValueError('max_threads must be a positive integer.')
        return value

    @field_validator('openai_key', mode="before")
    def validate_openai_key(cls, value):
        if not value and not (value := os.getenv('OPENAI_API_KEY')):
            logger.warning('OPENAI_API_KEY environment variable is not set.')
            raise ValueError('OPENAI_API_KEY environment variable is not set.')
        return value

    @property
    def jinja_env(self) -> Environment:
        if not self._jinja_env:
            templates_path = Path(__file__).parent / 'templates'
            self._jinja_env = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=True)
        return self._jinja_env

    def choose_template(self, document: Document) -> str:
        """
        Choose a jinja template for a document
        """
        # If the document type is NOT "photo", choose paperwork.jinja
        if document.document_type not in [DOCUMENT_TYPE_PHOTO, DOCUMENT_TYPE_DETAIL_CLOSEUP, DOCUMENT_TYPE_ITEMS]:
            return "paperwork.jinja"
        
        # If it has the "cleanup" tag, choose cleanup_photo.jinja
        if document.tags and any(tag == "cleanup" for tag in document.tags):
            return "cleanup_photo.jinja"

        # If the date is prior to 2010, choose old_photo.jinja
        if document.created and document.created.year < 2010:
            return "old_photo.jinja"

        # Newer photos
        return "comparison_photo.jinja"

    def get_prompt(self, document: Document) -> str:
        """
        Generate a prompt to sent to openai using a jinja template.
        """
        if self.prompt:
            return self.prompt
        
        template_name = self.choose_template(document)
        template_path = f"output_json/{template_name}"
        logger.debug('Using template: %s', template_path)
        template = self.jinja_env.get_template(template_path)
        location = self.get_location(document)
        tags = self.paperless_client.get_document_tag_names(document, filter_needs=True)

        if not (description := template.render(document=document, location=location, tags=tags)):
            raise ValueError("Failed to generate prompt.")

        return description

    def get_location(self, document: Document) -> str | None:
        """
        Get the location of a document.
        """
        template = None

        if document.tags:
            if any(tag == TAG_HRSH for tag in document.tags):
                template = self.jinja_env.get_template("locations/hrsh.jinja")
            if any(tag == TAG_NYS_OMH for tag in document.tags):
                template = self.jinja_env.get_template("locations/nys_omh.jinja")

        if template:
            return template.render(document=document)
        return None
        
    def filter_documents(self, documents: List[Document]) -> Iterator[Document]:
        """
        Yields documents from the Paperless NGX instance that need description.

        Args:
            documents (List[Document]): The documents to filter

        Yields:
            Iterator[Document]: The filtered documents.
        """
        for document in documents:
            if self.filter_document(document):
                yield document

    def filter_document(self, document: Document) -> bool:
        """
        """
        # If content includes "IMAGE DESCRIPTION", skip
        if document.content and "IMAGE DESCRIPTION" in document.content:
            logger.debug("Skipping document with existing description")
            return False

        if document.tags:
            # If tags include "described", skip
            if self.pc.document_has_tag("described", document):
                logger.debug("Skipping document with 'described' tag")
                return False

            # If tags DO NOT include "needs-description", skip
            if not self.pc.document_has_tag("needs-description", document):
                logger.debug("Skipping document without 'needs-description' tag")
                return False

        # Check it is a supported extension
        original_filename = document.original_file_name or ""
        if not any(original_filename.lower().endswith(ext) for ext in DESCRIBE_ACCEPTED_FORMATS):
            logger.debug("Skipping document with unsupported extension: %s", original_filename)
            return False

        return True


    def fetch_documents_with_tag(self, tag_name: str | None = None, *, filter_results : bool = True) -> Iterator[Document]:
        """Fetches documents with the specified tag from Paperless NGX."""
        tag_name = tag_name or self.paperless_tag
        tag_id = None

        for tag in self.pc.get_tags():
            if tag.name == tag_name:
                tag_id = tag.id
                break
                                                                  
        if tag_id is None:
            logger.error(f"Tag '{tag_name}' not found")
            return

        for doc in self.pc.get_documents():
            if self.pc.document_has_tag(tag_id, doc):
                if not filter_results or self.filter_document(doc):
                    yield doc

    def update_document(self, document : Document) -> bool:
        return self.pc.update_document(document)

    @singledispatchmethod
    def remove_tag(self, tag_id: Any, document : Document) -> None:
        raise TypeError(f"Unsupported tag type: {type(tag_id)}")

    @remove_tag.register
    def _remove_tag(self, tag_id: int, document : Document) -> None:  # type: ignore
        """Removes a tag from a document."""
        if not document.tags:
            return
        
        document.tags = [tag for tag in document.tags if tag != tag_id]
        self.update_document(document)

    @remove_tag.register
    def _remove_tag(self, tag: Tag, document : Document) -> None: # type: ignore
        """Removes a tag from a document."""
        self.remove_tag(tag.id, document)

    @remove_tag.register
    def _remove_tag(self, tag_name: str, document : Document) -> None:
        """Removes a tag from a document."""
        tag = self.pc.get_tag(tag_name)
        if not tag:
            raise ValueError(f"Tag '{tag_name}' not found.")
        self.remove_tag(tag.id, document)

    @singledispatchmethod
    def add_tag(self, tag_id: Any, document: Document) -> None:
        raise TypeError(f"Unsupported tag type: {type(tag_id)}")

    @add_tag.register
    def _add_tag(self, tag_id: int, document: Document) -> None:  # type: ignore
        """Adds a tag to a document."""
        if not document.tags:
            document.tags = [tag_id]
            self.update_document(document)
            return

        if tag_id not in document.tags:
            document.tags = document.tags + [tag_id]
            self.update_document(document)

    @add_tag.register
    def _add_tag(self, tag: Tag, document: Document) -> None:  # type: ignore
        """Adds a tag to a document."""
        self.add_tag(tag.id, document)

    @add_tag.register
    def _add_tag(self, tag_name: str, document: Document) -> None:
        """Adds a tag to a document."""
        tag = self.pc.get_tag(tag_name)
        if not tag:
            raise ValueError(f"Tag '{tag_name}' not found.")
        self.add_tag(tag.id, document)

    def download_document(self, document: Document) -> DownloadedDocument | None:
        """Downloads a document from Paperless NGX."""
        try:
            logger.debug(f"Downloading document {document.id} from Paperless...")
            content = self.paperless_client.download_document(document)
            logger.debug(f"Downloaded document {document.id}")
            return content
        except Exception as e:
            logger.error(f"Failed to download document {document.id}: {e}")
        return None

    def extract_images_from_pdf(self, pdf_bytes: bytes, max_images: int = 2) -> list[bytes]:
        """
        Extracts the first image from a PDF file.

        Args:
            pdf_bytes (bytes): The PDF file content as bytes.

        Returns:
            bytes | None: The first {max_images} images as bytes or None if no image is found.
        """
        results : list[bytes] = []
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
                        logger.error(f"Failed to extract one image from page {page_number} of PDF. Result count {count}: {e}")
                        if count < 1:
                            raise

        except Exception as e:
            logger.error(f"extract_images_from_pdf: Error extracting image from PDF: {e}")
            raise DocumentParsingError("Error extracting image from PDF.") from e

        if not results:
            if image_count < 1:
                raise NoImagesException('No images found in the PDF')
            raise DocumentParsingError('Unable to extract images from PDF.')

        return results

    def append_document_content(self, document: Document, content: str) -> Document:
        """
        Appends content to a document.

        Args:
            document (Document): The document to append content to.
            content (str): The content to append.

        Returns:
            Document: The document with the content appended.
        """
        if not content:
            raise ValueError("Content should not be empty.")

        logger.debug(f"Appending content to document {document.id}")
        
        current_content = document.content or ""
        document.content = current_content + "\n\r\n\r" + content
        self.update_document(document)

        logger.debug(f"Successfully appended content to document {document.id}")
        return document

    def parse_date(self, date_str: str) -> date | None:
        """
        Parses a date string.

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
        Parses a date string.

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

    def update_document_date(self, document: Document, new_date: str | date | datetime) -> None:
        """
        Updates the date of a document.

        Args:
            document (Document): The document to update.
            date (str): The new date in 'YYYY-MM-DD' format.

        Returns:
            Document: The updated document.
        """
        parsed_date : str | date | datetime | None = new_date
        if isinstance(parsed_date, str):
            parsed_date = self.parse_datetime(parsed_date)
        if isinstance(parsed_date, date):
            parsed_date = datetime.combine(parsed_date, datetime.min.time())
            
        if not parsed_date:
            return
        
        logger.debug(f"Updating date of document {document.id} to '{parsed_date}'")
        
        # update the document date
        document.created = parsed_date
        self.update_document(document)
        
        logger.debug(f"Successfully updated date of document {document.id} to '{parsed_date}'")

    def standardize_image_contents(self, content: bytes) -> list[str]:
        """
        Standardize image contents to base64-encoded PNG format.
        """    
        try:
            return [self._convert_to_png(content)]
        except Exception as e:
            logger.debug(f"Failed to convert contents to png, will try other methods: {e}")

        # Interpret it as a pdf
        if (image_contents_list := self.extract_images_from_pdf(content)):
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
                raise NoImagesException("No images found to describe.")

            message_contents: list[openai.types.chat.ChatCompletionMessageParam] = [
                {
                    "type": "text",
                    "text": self.get_prompt(document),
                }  # type: ignore
            ] 
            
            for image in images:
                message_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image}"},
                })  # type: ignore

            response = self.openai.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": message_contents
                    } # type: ignore
                ],
                max_tokens=500,
            )
            description = response.choices[0].message.content
            logger.debug(f"Generated description: {description}")

        except fitz.FileDataError as fde:
            logger.error("Failed to generate description due to error reading file #%s: %s -> %s", document.id, document.original_file_name, fde)

        except ValueError as ve:
            logger.warning("Failed to generate description for document #%s: %s. Continuing with next image -> %s", 
                document.id, document.original_file_name, ve)

        except UnidentifiedImageError as uii:
            logger.warning('Failed to identify image format for document #%s: %s. Continuing with next image -> %s', 
                document.id, document.original_file_name, uii)

        except openai.APIConnectionError as ace:
            logger.error("API Connection Error. Is the OpenAI API URL correct? URL: %s, model: %s -> %s", 
                self.openai_url, self.openai_model, ace)
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

    def describe_document(self, document: Document) -> None:
        """
        Describes a single document using OpenAI's GPT-4o model.

        The document object passed in will be updated with the description.

        Args:
            document (dict): The document to describe.
        """
        response = None
        try:
            logger.debug(f"Describing document {document.id} using OpenAI...")
            
            if not (downloaded_document := self.download_document(document)):
                logger.error("Failed to download document content.")
                return

            if not (content := downloaded_document.content):
                logger.error("Document content is empty.")
                return

            # Ensure accepted format
            original_file_name = (document.original_file_name or "").lower()
            if not any(original_file_name.endswith(ext) for ext in DESCRIBE_ACCEPTED_FORMATS):
                logger.error(f"Document {document.id} has unsupported extension: {original_file_name}")
                return

            try:
                if not (response := self._send_describe_request(content, document)):
                    logger.error(f"OpenAI returned empty description for document {document.id}.")
                    return
            except NoImagesException as nie:
                logger.debug(f"No images found in document {document.id}: {nie}")
                return
            except DocumentParsingError as dpe:
                logger.error(f"Failed to parse document {document.id}: {dpe}")
                return
            except openai.BadRequestError as e:
                if "invalid_image_format" not in str(e):
                    logger.error("Failed to generate description for document #%s: %s -> %s", document.id, document.original_file_name, e)
                    return

                logger.debug("Bad format for document #%s: %s -> %s", document.id, document.original_file_name, e)
                return
                    
            # Process the response
            self.process_response(response, document)
        except requests.RequestException as e:
            logger.error(f"Failed to describe document {document.id}. {response=} => {e}")
            raise

    def parse_json(self, response: str, document: Document) -> dict | None:
        # Attempt to parse response as json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.debug("Failed to parse response as JSON. Saving response raw in document content. Document #%s: %s", 
                document.id, document.original_file_name)

        # If "```json" is present, strip everything before it
        if "```json" in response:
            response = response[response.index("```json") + 7:]
            # Strip everything after "```"
            if "```" in response:
                response = response[:response.index("```")]

        # try again
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.debug('Failed again after stripping json block')

        logger.error('Failed to parse response as JSON. Saving response raw in document content. Document #%s: %s', 
            document.id, document.original_file_name)
        self.append_document_content(document, response)
        return None

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
        if not (parsed_response := self.parse_json(response, document)):
            logger.debug('Unable to process response after failed json parsing')
            return document

        # Check if parsed_response is a dictionary
        if not isinstance(parsed_response, dict):
            logger.error("Parsed response is not a dictionary. Saving response raw in document content. Document #%s: %s", 
                document.id, document.original_file_name)
            self.append_document_content(document, response)
            return document
        
        # Attempt to grab "title", "description", "tags", "date" from parsed_response
        title = parsed_response.get("title", None)
        description = parsed_response.get("description", None)
        summary = parsed_response.get("summary", None)
        content = parsed_response.get("content", None)
        tags = parsed_response.get("tags", None)
        date = parsed_response.get("date", None)
        full_description = f"""AI IMAGE DESCRIPTION (v{VERSION}): 
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
        
        if title and document.tags and any(tag == "needs-title" for tag in document.tags):
            try:
                document.title = title
                self.remove_tag("needs-title", document)
                self.update_document(document)
            except Exception as e:
                logger.error("Failed to update document title. Document #%s: %s -> %s", 
                    document.id, document.original_file_name, e)

        if date and document.tags and any(tag == "needs-date" for tag in document.tags):
            try:
                self.update_document_date(document, date)
                self.remove_tag("needs-date", document)
            except Exception as e:
                logger.error("Failed to update document date. Document #%s: %s -> %s", 
                    document.id, document.original_file_name, e)

        # Append the description to the document
        self.append_document_content(document, full_description)
        self.remove_tag("needs-description", document)
        self.add_tag("described", document)
        
        logger.debug(f"Successfully described document {document.id}")
        return document

    def describe_documents(self, documents: list[Document] | None = None) -> list[Document]:
        """
        Describes a list of documents using OpenAI's GPT-4o model.

        Args:
            documents (list[Document]): The documents to describe.

        Returns:
            list[Document]: The documents with the descriptions added.
        """
        logger.info('Fetching documents to describe...')
        if documents is None:
            documents = list(self.fetch_documents_with_tag())
        
        results = []
        with alive_bar(title='Running', unknown='waves') as self._progress_bar:
            for document in documents:
                if (updated_document := self.describe_document(document)):
                    results.append(updated_document)
                self.progress_bar()
        return results

class ArgNamespace(argparse.Namespace):
    """
    A custom namespace class for argparse.
    """
    verbose: bool = False
    tag: str
    url: str
    key: str
    model: str | None = None
    prompt: str | None = None
    force_openai: bool = False

def main():
    logger = setup_logging()
    try:
        load_dotenv()

        DEFAULT_URL = os.getenv("PAPERLESS_URL")
        DEFAULT_KEY = os.getenv("PAPERLESS_KEY")
        DEFAULT_TAG = "needs-description"
        OPENAI_URL = os.getenv('PAPERLESS_OPENAI_URL')
        OPENAI_KEY = os.getenv('PAPERLESS_OPENAI_API_KEY')
        OPENAI_MODEL = os.getenv('PAPERLESS_OPENAI_MODEL', DEFAULT_OPENAI_MODEL)

        parser = argparse.ArgumentParser(description="Fetch documents with a specific tag from Paperless NGX.")
        parser.add_argument('--url', type=str, default=DEFAULT_URL, help="The base URL of the Paperless NGX instance")
        parser.add_argument('--key', type=str, default=DEFAULT_KEY, help="The API key for the Paperless NGX instance")
        parser.add_argument('--model', type=str, default=OPENAI_MODEL, help=f"The OpenAI model to use (default: {DEFAULT_OPENAI_MODEL})")
        parser.add_argument('--tag', type=str, default=DEFAULT_TAG, help="Tag to filter documents (default: 'needs-description')")
        parser.add_argument('--prompt', type=str, default=None, help="Prompt to use for OpenAI")
        parser.add_argument('--force-openai', action='store_true', help="Force the use of OpenAI, instead of urls or models loaded from env vars or other parameters")
        parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
        
        args = parser.parse_args(namespace=ArgNamespace())

        if args.verbose:
            logger.setLevel(logging.DEBUG)

        if not args.url:
            logger.error("PAPERLESS_URL environment variable is not set.")
            sys.exit(1)

        if not args.key:
            logger.error("PAPERLESS_KEY environment variable is not set.")
            sys.exit(1)

        paperless = DescribePhotos(
            paperless_url=args.url, 
            paperless_key=args.key, 
            paperless_tag=args.tag, 
            openai_key=OPENAI_KEY,
            openai_url=OPENAI_URL,
            openai_model=OPENAI_MODEL,
            prompt=args.prompt,
            force_openai=args.force_openai
        )
        results = paperless.describe_documents()
        if results:
            logger.info(f"Described {len(results)} documents")
        else:
            logger.info("No documents described.")

    except KeyboardInterrupt:
        logger.info("Script cancelled by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()