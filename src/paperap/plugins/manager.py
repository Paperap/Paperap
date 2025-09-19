"""
Plugin management system for Paperap.

This module provides the infrastructure for discovering, configuring, and
initializing plugins that extend the functionality of the Paperap client.
Plugins can hook into various parts of the application lifecycle through
the signal system.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Self, Set, TypedDict

import pydantic

from paperap.client import PaperlessClient
from paperap.plugins.base import Plugin

logger = logging.getLogger(__name__)


class PluginConfig(TypedDict):
    """
    Configuration settings for plugins.

    This TypedDict defines the structure of the configuration dictionary
    used to configure the plugin manager and individual plugins.

    Attributes:
        enabled_plugins: List of plugin names to enable. If empty, all discovered
            plugins will be enabled.
        settings: Dictionary mapping plugin names to their specific configuration
            settings.

    """

    enabled_plugins: list[str]
    settings: dict[str, Any]


class PluginManager(pydantic.BaseModel):
    """
    Manages the discovery, configuration and initialization of plugins.

    This class is responsible for discovering available plugins, configuring them
    with user-provided settings, and initializing them when needed. It maintains
    a registry of available plugin classes and their instances.

    Attributes:
        plugins: Dictionary mapping plugin names to their class definitions.
        instances: Dictionary mapping plugin names to their initialized instances.
        config: Configuration settings for plugins, including which plugins are enabled
            and their individual settings.
        client: The PaperlessClient instance that this plugin manager is associated with.

    """

    plugins: dict[str, type[Plugin]] = {}
    instances: dict[str, Plugin] = {}
    config: PluginConfig = {
        "enabled_plugins": [],
        "settings": {},
    }
    client: PaperlessClient

    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_assignment=True,
    )

    @property
    def enabled_plugins(self) -> list[str]:
        """
        Get the list of enabled plugin names.

        If no plugins are explicitly enabled in the configuration, all discovered
        plugins are considered enabled.

        Returns:
            List of enabled plugin names.

        Note:
            There's a known issue where if the enabled_plugins list is empty,
            all plugins will be enabled, which may not be the intended behavior
            if the user explicitly wanted to disable all plugins.

        """
        # TODO: There's a bug here... disabling every plugin will then enable every plugin
        if enabled := self.config.get("enabled_plugins"):
            return enabled

        return list(self.plugins.keys())

    def discover_plugins(self, package_name: str = "paperap.plugins") -> None:
        """
        Discover available plugins in the specified package.

        This method recursively searches the specified package for classes that
        inherit from the Plugin base class. Discovered plugins are registered
        in the plugins dictionary.

        Args:
            package_name: Dotted path to the package containing plugins.

        Example:
            ```python
            # Discover plugins in the default package
            plugin_manager.discover_plugins()

            # Discover plugins in a custom package
            plugin_manager.discover_plugins("myapp.custom_plugins")
            ```

        """
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            logger.warning("Could not import plugin package: %s", package_name)
            return

        # Find all modules in the package
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if is_pkg:
                # Recursively discover plugins in subpackages
                self.discover_plugins(module_name)
                continue

            try:
                module = importlib.import_module(module_name)

                # Find plugin classes in the module
                for _name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin and obj.__module__ == module_name:
                        plugin_name = obj.__name__
                        self.plugins[plugin_name] = obj
                        logger.debug("Discovered plugin: %s", plugin_name)
            except Exception as e:
                logger.error("Error loading plugin module %s: %s", module_name, e)

    def configure(self, config: PluginConfig | None = None, **kwargs: Any) -> None:
        """
        Configure the plugin manager with plugin-specific configurations.

        This method updates the plugin manager's configuration with the provided
        settings. Configuration can be provided either as a PluginConfig dictionary
        or as keyword arguments.

        Args:
            config: Dictionary containing plugin configuration. If provided, it
                replaces the current configuration.
            **kwargs: Additional configuration options. Supported keys are:
                - enabled_plugins: List of plugin names to enable.
                - settings: Dictionary mapping plugin names to their configurations.

        Example:
            ```python
            # Configure with a complete config dictionary
            plugin_manager.configure({
                "enabled_plugins": ["LoggingPlugin", "MetricsPlugin"],
                "settings": {
                    "LoggingPlugin": {"log_level": "DEBUG"},
                    "MetricsPlugin": {"collect_interval": 60}
                }
            })

            # Configure with keyword arguments
            plugin_manager.configure(
                enabled_plugins=["LoggingPlugin"],
                settings={"LoggingPlugin": {"log_level": "INFO"}}
            )
            ```

        """
        if config:
            self.config = config

        if kwargs:
            if enabled_plugins := kwargs.pop("enabled_plugins", None):
                self.config["enabled_plugins"] = enabled_plugins
            if settings := kwargs.pop("settings", None):
                self.config["settings"] = settings
            if kwargs:
                logger.warning("Unexpected configuration keys: %s", kwargs.keys())

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """
        Get the configuration for a specific plugin.

        Retrieves the configuration settings for the specified plugin from the
        plugin manager's configuration.

        Args:
            plugin_name: Name of the plugin to get configuration for.

        Returns:
            Dictionary containing the plugin's configuration settings.
            Returns an empty dictionary if no configuration exists for the plugin.

        """
        return self.config["settings"].get(plugin_name, {})  # type: ignore # mypy can't infer the return type correctly

    def initialize_plugin(self, plugin_name: str) -> Plugin | None:
        """
        Initialize a specific plugin.

        Creates an instance of the specified plugin using its class definition and
        configuration settings. If the plugin is already initialized, returns the
        existing instance.

        This method handles exceptions during plugin initialization to prevent
        plugin errors from disrupting the application.

        Args:
            plugin_name: Name of the plugin to initialize.

        Returns:
            The initialized plugin instance, or None if initialization failed or
            the plugin was not found.

        Example:
            ```python
            # Initialize a specific plugin
            logging_plugin = plugin_manager.initialize_plugin("LoggingPlugin")
            if logging_plugin:
                print(f"Plugin {logging_plugin.__class__.__name__} initialized")
            else:
                print("Failed to initialize plugin")
            ```

        """
        if plugin_name in self.instances:
            return self.instances[plugin_name]

        if plugin_name not in self.plugins:
            logger.warning("Plugin not found: %s", plugin_name)
            return None

        plugin_class = self.plugins[plugin_name]
        plugin_config = self.get_plugin_config(plugin_name)

        try:
            # Initialize the plugin with plugin-specific config
            plugin_instance = plugin_class(manager=self, **plugin_config)
            self.instances[plugin_name] = plugin_instance
            logger.info("Initialized plugin: %s", plugin_name)
            return plugin_instance
        except Exception as e:
            # Do not allow plugins to interrupt the normal program flow.
            logger.error("Failed to initialize plugin %s: %s", plugin_name, e)
            return None

    def initialize_all_plugins(self) -> dict[str, Plugin]:
        """
        Initialize all enabled plugins.

        Initializes all plugins that are enabled according to the configuration.
        If no plugins are explicitly enabled, initializes all discovered plugins.

        Returns:
            Dictionary mapping plugin names to their initialized instances.
            Only successfully initialized plugins are included in the result.

        Example:
            ```python
            # Discover and initialize all enabled plugins
            plugin_manager.discover_plugins()
            initialized_plugins = plugin_manager.initialize_all_plugins()
            print(f"Initialized {len(initialized_plugins)} plugins")
            ```

        """
        # Get enabled plugins from config
        enabled_plugins = self.enabled_plugins

        # Initialize plugins
        initialized = {}
        for plugin_name in enabled_plugins:
            instance = self.initialize_plugin(plugin_name)
            if instance:
                initialized[plugin_name] = instance

        return initialized
