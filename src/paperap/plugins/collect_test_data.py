"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *

        Usage example:
        test_dir = Path(__file__).parent.parent.parent.parent / "tests/sample_data"
        collector = TestDataCollector(test_dir)
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    collect_test_data.py                                                                                 *
*        Project: plugins                                                                                              *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from __future__ import annotations
import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
import logging

from paperap.plugins.base import Plugin
from paperap.signals import post_list_response, post_list_item
from paperap.signals import SignalPriority

if TYPE_CHECKING:
    from paperap.client import PaperlessClient

logger = logging.getLogger(__name__)


class TestDataCollector(Plugin):
    """
    Plugin to collect test data from API responses.
    """

    name = "test_data_collector"
    description = "Collects sample data from API responses for testing purposes"
    version = "0.0.1"

    def __init__(self, client: "PaperlessClient", test_dir=None, **kwargs):
        # Convert string path to Path object if needed
        if test_dir and isinstance(test_dir, str):
            test_dir = Path(test_dir)

        self.test_dir = test_dir or Path(self.config.get("test_dir", "tests/sample_data"))
        self.test_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(client, **kwargs)

    def setup(self):
        """Register signal handlers."""
        post_list_response.connect(self.save_list_response, SignalPriority.LOW)
        post_list_item.connect(self.save_first_item, SignalPriority.LOW)

    def teardown(self):
        """Unregister signal handlers."""
        post_list_response.disconnect(self.save_list_response)
        post_list_item.disconnect(self.save_first_item)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for objects that are not natively serializable."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Type {type(obj).__name__} is not JSON serializable")

    def save_list_response(self, sender, response: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Save the list response to a JSON file."""
        if not response or not (resource_name := kwargs.get("resource")):
            return response

        try:
            if not (content := json.dumps(response, default=self._json_serializer)):
                return response

            filepath = self.test_dir / f"{resource_name}_list.json"
            if not filepath.exists():
                with filepath.open("w") as f:
                    f.write(content)
        except (TypeError, OverflowError, OSError) as e:
            # Don't allow the plugin to interfere with normal operations in the event of failure
            logger.error(f"Error saving list response to file: {e}")

        return response

    def save_first_item(self, sender, item: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Save the first item from a list to a JSON file."""
        resource_name = kwargs.get("resource")
        if not resource_name:
            return item

        try:
            # Only save the first item we encounter
            filepath = self.test_dir / f"{resource_name}_item.json"
            if not filepath.exists():
                with filepath.open("w") as f:
                    f.write(json.dumps(item))
                # Disable this handler after saving the first item
                post_list_item.temporarily_disable(self.save_first_item)
        except (TypeError, OverflowError, OSError) as e:
            # Don't allow the plugin to interfere with normal operations in the event of failure
            logger.error(f"Error saving first item to file: {e}")

        return item

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
