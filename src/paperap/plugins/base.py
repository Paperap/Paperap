"""




----------------------------------------------------------------------------

   METADATA:

       File:    base.py
       Project: paperap
       Created: 2025-03-04
       Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from paperap.client import PaperlessClient


class Plugin(ABC):
    """Base class for all plugins."""

    # Class attributes for plugin metadata
    name: str | None = None
    description: str = "No description provided"
    version: str = "0.0.1"
    client: PaperlessClient
    config: dict[str, Any]

    def __init__(self, client: "PaperlessClient", **kwargs):
        """
        Initialize the plugin.

        Args:
            client: The PaperlessClient instance.
            **kwargs: Plugin-specific configuration.
        """
        self.client = client
        self.config = kwargs
        self.setup()

    @abstractmethod
    def setup(self):
        """Register signal handlers and perform other initialization tasks."""
        pass

    @abstractmethod
    def teardown(self):
        """Clean up resources when the plugin is disabled or the application exits."""
        pass

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """
        Get the configuration schema for this plugin.

        Returns:
            A dictionary describing the expected configuration parameters.
        """
        return {}
