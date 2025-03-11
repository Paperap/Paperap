"""
Usage example:
       test_dir = Path(__file__).parent.parent.parent.parent / "tests/sample_data"
       collector = TestDataCollector(test_dir)


----------------------------------------------------------------------------

   METADATA:

       File:    collect_test_data.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

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

from paperap.models import BaseModel
from paperap.plugins.base import Plugin
from paperap.signals import SignalPriority, SignalRegistry

if TYPE_CHECKING:
    from paperap.client import PaperlessClient

logger = logging.getLogger(__name__)

sanitize_pattern = re.compile(r"[^a-zA-Z0-9_-]")


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
    "original_file_name",
    "archived_file_name",
    "task_file_name",
    "filename",
]


class TestDataCollector(Plugin):
    """
    Plugin to collect test data from API responses.
    """

    name = "test_data_collector"
    description = "Collects sample data from API responses for testing purposes"
    version = "0.0.2"
    fake = Faker()
    test_dir: Path

    def __init__(self, client: "PaperlessClient", test_dir: Path | None = None, **kwargs: Any):
        # Convert string path to Path object if needed
        if test_dir and isinstance(test_dir, str):
            test_dir = Path(test_dir)

        self.test_dir = test_dir or Path(self.config.get("test_dir", "tests/sample_data"))
        self.test_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(client, **kwargs)

    @override
    def setup(self):
        """Register signal handlers."""
        SignalRegistry.connect("resource._handle_response:after", self.save_list_response, SignalPriority.LOW)
        SignalRegistry.connect("resource._handle_results:before", self.save_first_item, SignalPriority.LOW)
        SignalRegistry.connect("client.request:after", self.save_parsed_response, SignalPriority.LOW)

    @override
    def teardown(self):
        """Unregister signal handlers."""
        SignalRegistry.disconnect("resource._handle_response:after", self.save_list_response)
        SignalRegistry.disconnect("resource._handle_results:before", self.save_first_item)
        SignalRegistry.disconnect("client.request:after", self.save_parsed_response)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Serialize objects that are not natively serializable."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, BaseModel):
            return obj.to_dict()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        raise TypeError(f"Type {type(obj).__name__} is not JSON serializable")

    def _sanitize_response(self, **response: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize the response data to replace any strings with potentially personal information with dummy data
        """
        sanitized = {}
        for key, value in response.items():
            sanitized[key] = self._sanitize_value_recursive(key, value)

        # Replace "next" domain using regex
        if "next" in response and isinstance(response["next"], str):
            sanitized["next"] = re.sub(r"https?://.*?/", "https://example.com/", response["next"])

        return sanitized

    def _sanitize_value_recursive(self, key: str, value: Any) -> Any:
        """
        Recursively sanitize the value to replace any strings with potentially personal information with dummy data
        """
        if isinstance(value, dict):
            return {k: self._sanitize_value_recursive(k, v) for k, v in value.items()}

        if key in SANITIZE_KEYS:
            if isinstance(value, str):
                return self.fake.word()
            if isinstance(value, list):
                return [self.fake.word() for _ in value]

        return value

    def save_response(self, filepath: Path, response: dict[str, Any], **kwargs: Any) -> None:
        """
        Save the response to a JSON file.
        """
        if filepath.exists():
            return

        try:
            response = self._sanitize_response(**response)
            with filepath.open("w") as f:
                json.dump(response, f, indent=4, sort_keys=True, ensure_ascii=False, default=self._json_serializer)
        except (TypeError, OverflowError, OSError) as e:
            # Don't allow the plugin to interfere with normal operations in the event of failure
            logger.error("Error saving response to file: %s", e)

    def save_list_response(self, sender: Any, response: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Save the list response to a JSON file."""
        if not response or not (resource_name := kwargs.get("resource")):
            return response

        filepath = self.test_dir / f"{resource_name}_list.json"
        self.save_response(filepath, response)

        return response

    def save_first_item(self, sender: Any, item: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Save the first item from a list to a JSON file."""
        resource_name = kwargs.get("resource")
        if not resource_name:
            return item

        filepath = self.test_dir / f"{resource_name}_item.json"
        self.save_response(filepath, item)

        # Disable this handler after saving the first item
        SignalRegistry.disable("resource._handle_results:before", self.save_first_item)

        return item

    def save_parsed_response(
        self,
        parsed_response: dict[str, Any],
        method: str,
        params: dict[str, Any] | None,
        json_response: bool,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Save the request data to a JSON file.

        Connects to client.request:after signal.
        """
        if not json_response or not params:
            return parsed_response

        # Strip url to final path segment
        resource_name = ".".join(endpoint.split("/")[-2:])
        resource_name = sanitize_pattern.sub("_", resource_name)

        combined_params = list(params.keys())
        params_str = "|".join(combined_params)
        params_str = sanitize_pattern.sub("_", params_str)
        filename_prefix = ""
        if method.lower() != "get":
            filename_prefix = f"{method.lower()}__"
        filename = f"{filename_prefix}{resource_name}__{params_str}.json"

        filepath = self.test_dir / filename
        self.save_response(filepath, parsed_response)

        return parsed_response

    @override
    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Define the configuration schema for this plugin."""
        return {
            "test_dir": {
                "type": "string",
                "description": "Directory to save test data files",
                "required": False,
            }
        }
