"""
----------------------------------------------------------------------------

   METADATA:

       File:    base.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.8
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, NotRequired, TypedDict, override

import pydantic
from pydantic import ConfigDict, field_validator
from typing_extensions import Unpack

from paperap.exceptions import ModelValidationError

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.plugins.manager import PluginManager


class ConfigType(TypedDict, total=False):
    type: NotRequired[type]
    description: NotRequired[str]
    required: NotRequired[bool]


class Plugin(pydantic.BaseModel, ABC):
    """Base class for all plugins."""

    # Class attributes for plugin metadata
    name: ClassVar[str]
    description: ClassVar[str] = "No description provided"
    version: ClassVar[str] = "0.0.1"
    manager: "PluginManager"

    @override
    def __init_subclass__(cls, **kwargs: ConfigDict):
        # Enforce name is set
        if not getattr(cls, "name", None):
            raise ValueError("Plugin name must be set")
        return super().__init_subclass__(**kwargs)  # type: ignore # Not sure why pyright is complaining

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        use_enum_values=True,
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_assignment=True,
    )

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            **kwargs: Plugin-specific configuration.

        """
        # Pydantic handles config
        super().__init__(**kwargs)

        # Finalize setting up the plugin (defined by subclass)
        self.setup()

    @property
    def client(self) -> "PaperlessClient":
        return self.manager.client

    @abstractmethod
    def setup(self):
        """Register signal handlers and perform other initialization tasks."""

    @abstractmethod
    def teardown(self):
        """Clean up resources when the plugin is disabled or the application exits."""

    @classmethod
    def get_config_schema(cls) -> dict[str, ConfigType]:
        """
        Get the configuration schema for this plugin.

        Returns:
            A dictionary describing the expected configuration parameters.

        Examples:
            >>> return {
            >>>     "test_dir": {
            >>>         "type": str,
            >>>         "description": "Directory to save test data files",
            >>>         "required": False,
            >>>     }
            >>> }

        """
        return {}
