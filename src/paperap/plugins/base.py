"""
Base module for the Paperap plugin system.

This module provides the foundation for creating plugins that extend the functionality
of the Paperap client. Plugins can hook into various parts of the application lifecycle
and interact with the Paperless-NgX API through the client.
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
    """
    Type definition for plugin configuration schema entries.

    This TypedDict defines the structure of configuration options that plugins
    can declare in their get_config_schema method.

    Attributes:
        type: The Python type of the configuration value.
        description: Human-readable description of the configuration option.
        required: Whether this configuration option is required.

    """

    type: NotRequired[type]
    description: NotRequired[str]
    required: NotRequired[bool]


class Plugin(pydantic.BaseModel, ABC):
    """
    Base class for all Paperap plugins.

    This abstract class defines the interface that all plugins must implement.
    Plugins extend the functionality of the Paperap client by hooking into
    various parts of the application lifecycle.

    Plugins are configured using Pydantic models, allowing for automatic validation
    of configuration options.

    Attributes:
        name: Class attribute that defines the unique name of the plugin.
        description: Class attribute for human-readable plugin description.
        version: Class attribute for the plugin version string.
        manager: Reference to the PluginManager that manages this plugin.

    Examples:
        ```python
        class MyPlugin(Plugin):
            name = "my_plugin"
            description = "A sample plugin that logs API requests"
            version = "1.0.0"

            def setup(self) -> None:
                # Register signal handlers
                self.manager.client.signals.connect("request:before", self.on_request)

            def teardown(self) -> None:
                # Clean up resources
                self.manager.client.signals.disconnect("request:before", self.on_request)

            def on_request(self, method, url, **kwargs):
                print(f"API Request: {method} {url}")
                return kwargs
        ```

    """

    # Class attributes for plugin metadata
    name: ClassVar[str]
    description: ClassVar[str] = "No description provided"
    version: ClassVar[str] = "0.0.1"
    manager: "PluginManager"

    @override
    def __init_subclass__(cls, **kwargs: ConfigDict):
        """
        Validate plugin subclass requirements.

        This method is called when a new plugin class is defined. It ensures that
        required class attributes like 'name' are properly set.

        Args:
            **kwargs: Additional configuration options for the subclass.

        Raises:
            ValueError: If the plugin name is not set.

        """
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
        Initialize the plugin with configuration options.

        This constructor handles validation of configuration options using Pydantic,
        then calls the plugin's setup method to complete initialization.

        Args:
            **kwargs: Plugin-specific configuration options as defined in the plugin's
                get_config_schema method.

        Raises:
            ModelValidationError: If the provided configuration options don't match
                the expected schema.

        """
        # Pydantic handles config
        super().__init__(**kwargs)

        # Finalize setting up the plugin (defined by subclass)
        self.setup()

    @property
    def client(self) -> "PaperlessClient":
        """
        Get the PaperlessClient instance associated with this plugin.

        Returns:
            The PaperlessClient instance that this plugin is attached to.

        """
        return self.manager.client

    @abstractmethod
    def setup(self) -> None:
        """
        Register signal handlers and perform other initialization tasks.

        This method is called automatically when the plugin is initialized.
        Subclasses must implement this method to set up any necessary resources,
        register signal handlers, or perform other initialization tasks.

        Examples:
            ```python
            def setup(self) -> None:
                # Register signal handlers
                self.client.signals.connect("document.save:before", self.on_document_save)

                # Initialize resources
                self.temp_dir = tempfile.TemporaryDirectory()
            ```

        """
        pass

    @abstractmethod
    def teardown(self) -> None:
        """
        Clean up resources when the plugin is disabled or the application exits.

        Subclasses must implement this method to clean up any resources that were
        allocated during setup, such as temporary files, network connections, or
        signal handlers.

        Examples:
            ```python
            def teardown(self) -> None:
                # Disconnect signal handlers
                self.client.signals.disconnect("document.save:before", self.on_document_save)

                # Clean up resources
                self.temp_dir.cleanup()
            ```

        """
        pass

    @classmethod
    def get_config_schema(cls) -> dict[str, ConfigType]:
        """
        Get the configuration schema for this plugin.

        This method returns a dictionary describing the configuration options that
        this plugin accepts. Each entry in the dictionary corresponds to a configuration
        option, with metadata about its type, description, and whether it's required.

        The schema is used for validation when the plugin is initialized, and can also
        be used to generate configuration UI in management interfaces.

        Returns:
            A dictionary mapping configuration option names to their metadata.

        Examples:
            ```python
            @classmethod
            def get_config_schema(cls) -> dict[str, ConfigType]:
                return {
                    "log_level": {
                        "type": str,
                        "description": "Logging level (DEBUG, INFO, WARNING, ERROR)",
                        "required": False,
                    },
                    "output_dir": {
                        "type": str,
                        "description": "Directory to save output files",
                        "required": True,
                    }
                }
            ```

        """
        return {}
