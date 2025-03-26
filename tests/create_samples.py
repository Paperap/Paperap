
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar, Dict, Generic, List, Optional, Set, TypeVar, Union, cast

import requests
from alive_progress import alive_bar
from dotenv import load_dotenv
from faker import Faker
from pydantic import BaseModel, Field, HttpUrl, validator
from requests import Response

# Initialize logger with default level
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

class ResponseType(Enum):
    """Types of responses to save."""
    LIST = auto()
    ITEM = auto()
    NOT_FOUND = auto()
    MULTIPLE = auto()
    RAW = auto()


class ApiConfig(BaseModel):
    """Configuration for API access."""
    base_url: str = Field(default_factory=lambda: os.getenv("PAPERLESS_BASE_URL", "").rstrip("/") + "/api/")
    token: str = Field(default_factory=lambda: os.getenv("PAPERLESS_TOKEN", ""))
    save_dir: Path = Field(default_factory=lambda: Path("tests/sample_data"))
    verbose: bool = False

    @property
    def headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {"Authorization": f"Token {self.token}"}

    def initialize(self) -> None:
        """Initialize configuration."""
        self.save_dir.mkdir(parents=True, exist_ok=True)

        if not self.base_url or not self.token:
            raise ValueError("PAPERLESS_BASE_URL and PAPERLESS_TOKEN environment variables must be set")

class SanitizeUtil:
    """Utility for sanitizing sensitive data in API responses."""

    # Initialize faker once
    _faker = Faker()

    SENSITIVE_FIELDS: ClassVar[Set[str]] = {
        "username", "email", "password", "first_name",
        "last_name", "set-cookie", "auth_token"
    }
    URL_PATTERN: ClassVar[re.Pattern] = re.compile(r'https?://[^/]+')
    URL_DETECTION_PATTERN: ClassVar[re.Pattern] = re.compile(r'^https?://')

    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """Replace host with example.com in URLs."""
        return cls.URL_PATTERN.sub('http://example.com', url)

    @classmethod
    def is_url(cls, value: str) -> bool:
        """Check if a string value appears to be a URL."""
        return bool(cls.URL_DETECTION_PATTERN.match(value))

    @classmethod
    def get_fake_value(cls, key: str, original_value: str) -> str:
        """Generate a plausible fake value based on the field type."""
        # If the original value is empty, keep it empty
        if not original_value:
            return original_value

        if key == "username":
            return cls._faker.user_name()
        elif key == "email":
            return cls._faker.email()
        elif key == "password":
            return cls._faker.password(length=12)
        elif key == "first_name":
            return cls._faker.first_name()
        elif key == "last_name":
            return cls._faker.last_name()
        elif key == "set-cookie":
            return f"session={cls._faker.uuid4()}; Path=/; HttpOnly; Secure"
        else:
            # For any other sensitive fields, generate a generic value
            return f"fake-{key}-{cls._faker.uuid4()}"

    @classmethod
    def sanitize_data(cls, data: Any) -> Any:
        """Recursively sanitize sensitive data in response."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Handle dictionary of headers where keys might be case-insensitive
                if key.lower() in (field.lower() for field in cls.SENSITIVE_FIELDS):
                    if isinstance(value, str):
                        result[key] = cls.get_fake_value(key.lower(), value)
                    else:
                        result[key] = value
                # Sanitize URL values
                elif isinstance(value, str) and value and cls.is_url(value):
                    result[key] = cls.sanitize_url(value)
                # Recurse into nested objects
                else:
                    result[key] = cls.sanitize_data(value)
            return result
        elif isinstance(data, list):
            return [cls.sanitize_data(item) for item in data]
        elif isinstance(data, str) and cls.is_url(data):
            return cls.sanitize_url(data)
        return data


T = TypeVar('T')


class ApiClient:
    """Client for interacting with the Paperless-ngx API."""

    def __init__(self, config: ApiConfig) -> None:
        """Initialize the API client."""
        self.config = config

    def get(self, url: str, params: dict[str, Any] | None = None) -> Response:
        """Make a GET request to the API."""
        return requests.get(url, headers=self.config.headers, params=params or {})

    def save_response(
        self,
        endpoint_name: str,
        response_type: ResponseType,
        data: Any,
        suffix: str = ""
    ) -> None:
        """Save response data to a file."""
        # Sanitize sensitive data before saving
        sanitized_data = SanitizeUtil.sanitize_data(data)

        type_suffix = suffix or response_type.name.lower()
        filename = self.config.save_dir / f"{endpoint_name}_{type_suffix}.json"

        with filename.open("w", encoding="utf-8") as file:
            json.dump(sanitized_data, file, indent=4)

        if self.config.verbose:
            logger.debug(f"Saved sample data for {endpoint_name} ({type_suffix}) to {filename}")


class EndpointCollector:
    """Base collector for endpoint data."""

    def __init__(self, client: ApiClient, endpoint_name: str, endpoint_url: str) -> None:
        """Initialize the collector."""
        self.client = client
        self.name = endpoint_name
        self.url = endpoint_url
        self.ids: list[int] = []

    def fetch_list(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Fetch a list of items from the endpoint."""
        try:
            response = self.client.get(self.url, params=params or {"page_size": 10})
            response.raise_for_status()
            data = response.json()
            self.client.save_response(self.name, ResponseType.LIST, data)

            # Extract IDs if available
            if isinstance(data, dict) and "results" in data:
                for item in data["results"]:
                    if isinstance(item, dict) and "id" in item:
                        self.ids.append(item["id"])

            return data
        except requests.RequestException as e:
            if self.client.config.verbose:
                logger.error(f"Failed to fetch list for {self.name}: {e}")
            return {}

    def fetch_item(self, item_id: int) -> dict[str, Any] | None:
        """Fetch a single item by ID."""
        item_url = f"{self.url.rstrip('/')}/{item_id}/"

        try:
            response = self.client.get(item_url)
            response.raise_for_status()
            data = response.json()
            self.client.save_response(self.name, ResponseType.ITEM, data)
            return data
        except requests.RequestException as e:
            if e.response and e.response.status_code == 404:
                # Save 404 response
                self.client.save_response(
                    self.name,
                    ResponseType.NOT_FOUND,
                    {"status_code": 404, "detail": "Not found"}
                )
            elif self.client.config.verbose:
                logger.error(f"Failed to fetch item {item_id} for {self.name}: {e}")
            return None

    def fetch_not_found(self) -> None:
        """Fetch a 404 response by using an invalid ID."""
        if not self.ids:
            if self.client.config.verbose:
                logger.warning(f"No valid IDs found for {self.name}, cannot fetch 404 response")
            return

        # Generate an ID that doesn't exist
        invalid_id = max(self.ids) + 1000

        # Temporarily suppress error logs for expected 404 responses
        logger_level = logger.level
        logger.setLevel(logging.CRITICAL)
        try:
            self.fetch_item(invalid_id)
        finally:
            logger.setLevel(logger_level)

    def fetch_multiple(self, count: int = 3) -> dict[str, Any] | None:
        """Fetch multiple items using id__in parameter."""
        if len(self.ids) < count:
            if self.client.config.verbose:
                logger.warning(f"Not enough IDs for {self.name} to fetch multiple (have {len(self.ids)}, need {count})")
            return None

        # Select a random subset of IDs
        selected_ids = random.sample(self.ids, count)
        id_param = ",".join(str(id) for id in selected_ids)

        try:
            response = self.client.get(self.url, params={"id__in": id_param})
            response.raise_for_status()
            data = response.json()
            self.client.save_response(self.name, ResponseType.MULTIPLE, data)
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch multiple items for {self.name}: {e}")
            return None

    def collect_all(self) -> None:
        """Collect all sample data for this endpoint."""
        # Fetch list with larger page size to get more IDs
        self.fetch_list({"page_size": 50})

        # If IDs were found, collect more detailed information
        if self.ids:
            # Fetch a single item
            self.fetch_item(self.ids[0])

            # Fetch a 404 response
            self.fetch_not_found()

            # Fetch multiple items if we have enough IDs
            if len(self.ids) >= 3:
                self.fetch_multiple(3)
        elif self.client.config.verbose:
            logger.warning(f"No items with IDs found for endpoint {self.name}")


class RawEndpointCollector(EndpointCollector):
    """Collector for endpoints that return raw data."""

    def fetch_raw(self, item_id: int, params: dict[str, Any] | None = None) -> None:
        """Fetch raw data from the endpoint."""
        item_url = f"{self.url.rstrip('/')}/{item_id}/"

        try:
            response = self.client.get(item_url, params or {})
            response.raise_for_status()

            # Save the raw content along with headers for inspection
            data = {
                "content": response.content.decode("utf-8", errors="replace"),
                "headers": dict(response.headers),
                "status_code": response.status_code,
            }
            self.client.save_response(self.name, ResponseType.RAW, data)
        except requests.RequestException as e:
            if self.client.config.verbose:
                logger.error(f"Failed to fetch raw data for {self.name}: {e}")


class DocumentRelatedCollector(EndpointCollector):
    """Collector for document-related endpoints."""

    BINARY_ENDPOINTS: ClassVar[list[str]] = [
        "document_download",
        "document_preview",
        "document_thumbnail"
    ]

    JSON_ENDPOINTS: ClassVar[list[str]] = [
        "document_metadata",
        "document_notes",
        "document_suggestions"
    ]

    def __init__(self, client: ApiClient, document_id: int) -> None:
        """Initialize with a document ID."""
        super().__init__(client, "documents", f"{client.config.base_url}documents/")
        self.document_id = document_id

    def collect_related_data(self) -> None:
        """Collect data from all document-related endpoints."""
        if not self.document_id:
            logger.error("Cannot collect document-related data without a document ID")
            return

        total_endpoints = len(self.BINARY_ENDPOINTS) + len(self.JSON_ENDPOINTS) + 1  # +1 for next_asn

        with alive_bar(total_endpoints, title=f"Document {self.document_id} related data") as bar:
            # Collect binary endpoints (download, preview, thumbnail)
            for endpoint in self.BINARY_ENDPOINTS:
                url = f"{self.client.config.base_url}documents/{self.document_id}/{endpoint.split('_')[1]}/"
                collector = RawEndpointCollector(self.client, endpoint, url)
                collector.fetch_raw(self.document_id, {"original": "false"})
                bar()

            # Collect JSON endpoints (metadata, notes, suggestions)
            for endpoint in self.JSON_ENDPOINTS:
                url = f"{self.client.config.base_url}documents/{self.document_id}/{endpoint.split('_')[1]}/"
                collector = EndpointCollector(self.client, endpoint, url)
                collector.fetch_list()
                bar()

            # Fetch next_asn endpoint
            next_asn_url = f"{self.client.config.base_url}documents/next_asn/"
            try:
                response = self.client.get(next_asn_url)
                response.raise_for_status()
                data = response.json()
                self.client.save_response("document_next_asn", ResponseType.ITEM, data)
            except requests.RequestException as e:
                if self.client.config.verbose:
                    logger.error(f"Failed to fetch document_next_asn: {e}")
            bar()




class SampleDataCollector:
    """Main class for collecting sample data from Paperless-ngx API."""

    EXTRA_ENDPOINTS: ClassVar[dict[str, str]] = {
        "profile": "profile/",
        "saved_views": "saved_views/",
        "share_links": "share_links/",
        "storage_paths": "storage_paths/",
        "tasks": "tasks/",
        "ui_settings": "ui_settings/",
        "workflows": "workflows/",
        "workflow_triggers": "workflow_triggers/",
        "workflow_actions": "workflow_actions/",
    }

    def __init__(self) -> None:
        """Initialize the sample data collector."""
        self.config = ApiConfig()
        self.config.initialize()
        self.client = ApiClient(self.config)
        self.api_root: dict[str, Any] = {}
        self.document_id: int | None = None

    def fetch_api_root(self) -> dict[str, Any]:
        """Fetch the API root to discover available endpoints."""
        try:
            response = self.client.get(self.config.base_url)
            response.raise_for_status()
            self.api_root = response.json()
            self.client.save_response("api_root", ResponseType.ITEM, self.api_root)
            return self.api_root
        except requests.RequestException as e:
            logger.error(f"Failed to fetch API root: {e}")
            return {}

    def collect_from_api_root(self) -> None:
        """Collect data from all endpoints discovered in the API root."""
        if not self.api_root:
            self.fetch_api_root()

        # Filter to include only HTTP endpoints
        http_endpoints = [(endpoint, url) for endpoint, url in self.api_root.items()
                         if isinstance(url, str) and url.startswith("http")]

        with alive_bar(len(http_endpoints), title="API endpoints") as bar:
            for endpoint, url in http_endpoints:
                logger.info(f"Collecting data from endpoint '{endpoint}'...")

                collector = EndpointCollector(self.client, endpoint, url)
                collector.collect_all()

                # If this is the documents endpoint, save a sample document ID
                if endpoint == "documents" and collector.ids and not self.document_id:
                    self.document_id = collector.ids[0]

                bar()

    def collect_document_related(self) -> None:
        """Collect data from document-related endpoints."""
        if not self.document_id:
            logger.warning("No document ID available, skipping document-related endpoints")
            return

        logger.info(f"Collecting document-related data for document ID {self.document_id}...")
        doc_collector = DocumentRelatedCollector(self.client, self.document_id)
        doc_collector.collect_related_data()

    def collect_extra_endpoints(self) -> None:
        """Collect data from additional endpoints not in the API root."""
        with alive_bar(len(self.EXTRA_ENDPOINTS), title="Extra endpoints") as bar:
            for name, path in self.EXTRA_ENDPOINTS.items():
                url = f"{self.config.base_url}{path}"
                logger.info(f"Collecting data from extra endpoint '{name}'...")

                collector = EndpointCollector(self.client, name, url)
                collector.collect_all()
                bar()


    def run(self) -> None:
        """Run the complete data collection process."""
        logger.info("Paperless-ngx API Sample Data Collector")

        # Collect data from API root endpoints
        self.collect_from_api_root()

        # Collect document-related data if a document ID was found
        if self.document_id:
            self.collect_document_related()
        else:
            logger.warning("No document ID found, skipping document-related endpoints")

        # Collect data from extra endpoints
        self.collect_extra_endpoints()


        logger.info("Sample data collection complete.")


def main() -> None:
    """Entry point for the script."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Collect sample data from Paperless-ngx API")
        parser.add_argument("-v", "--verbose", action="count", default=0,
                            help="Increase verbosity (can be used multiple times: -v, -vv)")
        args = parser.parse_args()

        # Configure logging based on verbosity level
        if args.verbose == 0:
            log_level = logging.WARNING
        elif args.verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

        logger.setLevel(log_level)

        # Create and initialize collector with verbosity setting
        collector = SampleDataCollector()
        collector.config.verbose = args.verbose > 0

        # Run the collection process
        collector.run()
    except Exception as e:
        logger.exception(f"Error in sample data collection: {e}")
        raise


if __name__ == "__main__":
    main()
