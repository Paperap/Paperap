"""
Plugin for collecting sample data from API responses for testing purposes.

This module provides a plugin that intercepts API responses and saves them as JSON files,
which can be used for testing and development. It sanitizes personal information
to ensure privacy while maintaining the structure of the data.
"""

from __future__ import annotations

import datetime
import json
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from faker import Faker
from pydantic import HttpUrl, field_validator

from paperap.exceptions import ModelValidationError
from paperap.models import StandardModel
from paperap.plugins.base import Plugin
from paperap.signals import SignalPriority, registry

logger = logging.getLogger(__name__)

# Pattern for sanitizing filenames to be safe for filesystem
sanitize_pattern = re.compile(r"[^a-zA-Z0-9|.=_-]")

# Keys that might contain personal information and should be sanitized
SANITIZE_KEYS = [
    "email",
    "first_name",
    "last_name",
    "name",
    "phone",
    "username",
    "content",
    "filename",
    "title",
    "slug",
    "original_filename",
    "archived_file_name",
    "task_file_name",
    "filename",
]

# Type alias for API response data structures
type ClientResponse = dict[str, Any] | list[dict[str, Any]]


class SampleDataCollector(Plugin):
    """
    Plugin to collect test data from API responses.

    This plugin intercepts API responses, sanitizes any personal information,
    and saves them as JSON files for use in testing. It connects to various
    signals in the client to capture different types of responses.

    Attributes:
        name: Unique identifier for the plugin.
        description: Human-readable description of the plugin's purpose.
        version: Version string for the plugin.
        fake: Faker instance for generating replacement data.
        test_dir: Directory where sample data files will be saved.

    """

    name = "test_data_collector"
    description = "Collects sample data from API responses for testing purposes"
    version = "0.0.3"
    fake: Faker = Faker()
    test_dir: Path = Path("tests/sample_data")

    @field_validator("test_dir", mode="before")
    @classmethod
    def validate_test_dir(cls, value: Any) -> Path | None:
        """
        Validate and normalize the test directory path.

        This validator ensures the test directory is a valid Path object,
        converts relative paths to absolute paths, and creates the directory
        if it doesn't exist.

        Args:
            value: The directory path as a string or Path object.

        Returns:
            Path: The validated and normalized directory path.

        Raises:
            ModelValidationError: If the value is not a string or Path object.

        Examples:
            >>> SampleDataCollector.validate_test_dir("tests/data")
            PosixPath('/path/to/project/tests/data')

        """
        # Convert string path to Path object if needed
        if not value:
            value = Path("tests/sample_data")

        if isinstance(value, str):
            value = Path(value)

        if not isinstance(value, Path):
            raise ModelValidationError("Test directory must be a string or Path object")

        if not value.is_absolute():
            # Make it relative to project root
            project_root = Path(__file__).parents[4]
            value = project_root / value

        value.mkdir(parents=True, exist_ok=True)
        return value

    @override
    def setup(self) -> None:
        """
        Register signal handlers to intercept API responses.

        This method connects the plugin's handler methods to the appropriate signals
        in the client, allowing it to capture and save API responses.
        """
        registry.connect("resource._handle_response:after", self.save_list_response, SignalPriority.LOW)
        registry.connect("resource._handle_results:before", self.save_first_item, SignalPriority.LOW)
        registry.connect("client.request:after", self.save_parsed_response, SignalPriority.LOW)

    @override
    def teardown(self) -> None:
        """
        Unregister signal handlers when the plugin is disabled.

        This method disconnects all the signal handlers that were connected in setup(),
        ensuring the plugin doesn't continue to intercept API responses after it's disabled.
        """
        registry.disconnect("resource._handle_response:after", self.save_list_response)
        registry.disconnect("resource._handle_results:before", self.save_first_item)
        registry.disconnect("client.request:after", self.save_parsed_response)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """
        Serialize objects that are not natively JSON serializable.

        This method handles various Python types that aren't directly serializable to JSON,
        converting them to appropriate string or primitive representations.

        Args:
            obj: The object to serialize.

        Returns:
            A JSON-serializable representation of the object.

        Raises:
            TypeError: If the object type cannot be serialized.

        Examples:
            >>> SampleDataCollector._json_serializer(datetime.datetime(2023, 1, 1))
            '2023-01-01T00:00:00'
            >>> SampleDataCollector._json_serializer(Path('/tmp/file.txt'))
            '/tmp/file.txt'

        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, StandardModel):
            return obj.to_dict()
        if isinstance(obj, StandardModel):
            return obj.model_dump()
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        raise TypeError(f"Type {type(obj).__name__} is not JSON serializable")

    def _sanitize_list_response[R: list[dict[str, Any]]](self, response: R) -> R:
        """
        Sanitize a list of dictionary responses.

        Processes each item in the list, replacing potentially sensitive information
        with fake data while preserving the structure.

        Args:
            response: A list of dictionaries containing API response data.

        Returns:
            A sanitized copy of the input list with sensitive data replaced.

        """
        sanitized_list: R = []  # type: ignore
        for item in response:
            sanitized_item = self._sanitize_value_recursive("", item)
            sanitized_list.append(sanitized_item)  # type: ignore
        return sanitized_list

    def _sanitize_dict_response[R: dict[str, Any]](self, **response: R) -> R:
        """
        Sanitize a dictionary response.

        Processes each key-value pair in the dictionary, replacing potentially
        sensitive information with fake data while preserving the structure.

        Args:
            **response: A dictionary containing API response data.

        Returns:
            A sanitized copy of the input dictionary with sensitive data replaced.

        """
        sanitized: dict[str, Any] = {}
        for key, value in response.items():
            sanitized[key] = self._sanitize_value_recursive(key, value)

        # Replace "next" domain using regex
        if (next_page := response.get("next", None)) and isinstance(next_page, str):
            sanitized["next"] = re.sub(r"https?://.*?/", "https://example.com/", next_page)

        return sanitized  # type: ignore

    def _sanitize_value_recursive(self, key: str, value: Any) -> Any:
        """
        Recursively sanitize values in nested data structures.

        This method traverses nested dictionaries and lists, replacing sensitive
        string values with fake data generated by Faker.

        Args:
            key: The key associated with the value (used to determine if sanitization is needed).
            value: The value to potentially sanitize.

        Returns:
            The sanitized value, or the original value if no sanitization was needed.

        Examples:
            >>> collector = SampleDataCollector()
            >>> collector._sanitize_value_recursive("email", "user@example.com")
            'word123'  # A random word from Faker
            >>> collector._sanitize_value_recursive("content", {"text": "sensitive info"})
            {'text': 'word456'}  # Sanitized nested content

        """
        if isinstance(value, dict):
            return {k: self._sanitize_value_recursive(k, v) for k, v in value.items()}

        if key in SANITIZE_KEYS:
            if isinstance(value, str):
                return self.fake.word()
            if isinstance(value, list):
                return [self.fake.word() for _ in value]

        return value

    def save_response(self, filepath: Path, response: ClientResponse | None, **kwargs: Any) -> None:
        """
        Save an API response to a JSON file.

        This method sanitizes the response data and saves it to the specified file path.
        If the file already exists, it will not be overwritten.

        Args:
            filepath: Path where the JSON file should be saved.
            response: The API response data to save.
            **kwargs: Additional context information (not used directly).

        Note:
            Any errors during saving are logged but do not interrupt normal operation.

        """
        if not response or filepath.exists():
            return

        try:
            if isinstance(response, list):
                response = self._sanitize_list_response(response)
            else:
                response = self._sanitize_dict_response(**response)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open("w") as f:
                json.dump(response, f, indent=4, sort_keys=True, ensure_ascii=False, default=self._json_serializer)
        except (TypeError, OverflowError, OSError) as e:
            # Don't allow the plugin to interfere with normal operations in the event of failure
            logger.error("Error saving response to file (%s): %s", filepath.absolute(), e)

    def save_list_response[R: ClientResponse | None](self, sender: Any, response: R, **kwargs: Any) -> R:
        """
        Save a list response from a resource to a JSON file.

        This method is connected to the "resource._handle_response:after" signal and
        saves list responses from API resources.

        Args:
            sender: The object that sent the signal.
            response: The API response data to save.
            **kwargs: Additional context information, including the resource name.

        Returns:
            The original response, unmodified.

        """
        if not response or not (resource_name := kwargs.get("resource")):
            return response

        filepath = self.test_dir / f"{resource_name}_list.json"
        self.save_response(filepath, response)

        return response

    def save_first_item[R: dict[str, Any]](self, sender: Any, item: R, **kwargs: Any) -> R:
        """
        Save the first item from a resource result to a JSON file.

        This method is connected to the "resource._handle_results:before" signal and
        saves the first individual item from a resource query. After saving the first
        item, it disables itself to avoid saving duplicate items.

        Args:
            sender: The object that sent the signal.
            item: The individual item data to save.
            **kwargs: Additional context information, including the resource name.

        Returns:
            The original item, unmodified.

        """
        resource_name = kwargs.get("resource")
        if not resource_name:
            return item

        filepath = self.test_dir / f"{resource_name}_item.json"
        self.save_response(filepath, item)

        # Disable this handler after saving the first item
        registry.disable("resource._handle_results:before", self.save_first_item)

        return item

    def save_parsed_response(
        self,
        parsed_response: dict[str, Any],
        method: str,
        params: dict[str, Any] | None,
        json_response: bool,
        endpoint: str | HttpUrl,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Save a parsed API response to a JSON file.

        This method is connected to the "client.request:after" signal and saves
        responses from direct client requests. It creates filenames based on the
        HTTP method, endpoint, and request parameters.

        Args:
            parsed_response: The parsed API response data.
            method: The HTTP method used (GET, POST, etc.).
            params: The request parameters.
            json_response: Whether the response is JSON.
            endpoint: The API endpoint that was requested.
            **kwargs: Additional context information.

        Returns:
            The original parsed response, unmodified.

        Raises:
            ValueError: If the endpoint is not provided.

        Examples:
            A GET request to "/api/documents/?page=1" might be saved as:
            "api.documents__page=1.json"

            A POST request to "/api/tags/" might be saved as:
            "post__api.tags__.json"

        """
        if not endpoint:
            raise ValueError("Endpoint is required to save parsed response")

        endpoint = str(endpoint)

        # If endpoint contains "example.com", we're testing, so skip it
        if "example.com" in str(endpoint):
            return parsed_response

        if not json_response or not params:
            return parsed_response

        # Strip url to final path segment
        resource_name = ".".join(endpoint.split("/")[-2:])

        combined_params = list(f"{k}={v}" for k, v in params.items())
        params_str = "|".join(combined_params)
        filename_prefix = ""
        if method.lower() != "get":
            filename_prefix = f"{method.lower()}__"
        filename = f"{filename_prefix}{resource_name}__{params_str}.json"
        filename = sanitize_pattern.sub("_", filename)
        filename = filename[:100]  # Limit filename length

        filepath = self.test_dir / filename
        self.save_response(filepath, parsed_response)

        return parsed_response

    @override
    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """
        Define the configuration schema for this plugin.

        This method specifies the configuration options that can be set for the plugin,
        including their types, descriptions, and whether they're required.

        Returns:
            A dictionary describing the configuration schema.

        """
        return {
            "test_dir": {
                "type": str,
                "description": "Directory to save test data files",
                "required": False,
            }
        }
