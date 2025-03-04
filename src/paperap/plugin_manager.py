"""




----------------------------------------------------------------------------

   METADATA:

       File:    plugin_manager.py
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

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Any, Optional, Set, TypedDict

from paperap.plugins.base import Plugin

logger = logging.getLogger(__name__)


class PluginConfig(TypedDict):
    """
    Configuration settings for a plugin.
    """

    enabled_plugins: list[str]
    settings: dict[str, Any]


class PluginManager:
    """Manages the discovery, configuration and initialization of plugins."""

    plugins: dict[str, type[Plugin]]
    instances: dict[str, Plugin]
    config: PluginConfig
    dependencies: dict[str, Set[str]]

    def __init__(self):
        self.plugins = {}
        self.instances = {}
        self.config = {
            "enabled_plugins": [],
            "settings": {},
        }
        self.dependencies = {}

    @property
    def enabled_plugins(self) -> list[str]:
        # TODO: There's a bug here... disabling every plugin will then enable every plugin
        if enabled := self.config.get("enabled_plugins"):
            return enabled

        return list(self.plugins.keys())

    def discover_plugins(self, package_name: str = "paperap.plugins") -> None:
        """
        Discover available plugins in the specified package.

        Args:
            package_name: Dotted path to the package containing plugins.
        """
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            logger.warning(f"Could not import plugin package: {package_name}")
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
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin and obj.__module__ == module_name:
                        plugin_name = obj.__name__
                        self.plugins[plugin_name] = obj
                        logger.debug(f"Discovered plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error loading plugin module {module_name}: {e}")

    def configure(self, config: PluginConfig) -> None:
        """
        Configure the plugin manager with plugin-specific configurations.

        Args:
            config: dictionary mapping plugin names to their configurations.
        """
        self.config = config

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """Get the configuration for a specific plugin."""
        return self.config["settings"].get(plugin_name, {})

    def initialize_plugin(self, plugin_name: str, client: Any) -> Plugin | None:
        """
        Initialize a specific plugin.

        Args:
            plugin_name: Name of the plugin to initialize.
            client: The PaperlessClient instance.

        Returns:
            The initialized plugin instance or None if initialization failed.
        """
        if plugin_name in self.instances:
            return self.instances[plugin_name]

        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not found: {plugin_name}")
            return None

        plugin_class = self.plugins[plugin_name]
        plugin_config = self.get_plugin_config(plugin_name)

        try:
            # Initialize the plugin with client and any plugin-specific config
            plugin_instance = plugin_class(client, **plugin_config)
            self.instances[plugin_name] = plugin_instance
            logger.info(f"Initialized plugin: {plugin_name}")
            return plugin_instance
        except Exception as e:
            logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            return None

    def initialize_all_plugins(self, client: Any) -> dict[str, Plugin]:
        """
        Initialize all discovered plugins.

        Args:
            client: The PaperlessClient instance.

        Returns:
            Dictionary mapping plugin names to their initialized instances.
        """
        # Get enabled plugins from config
        enabled_plugins = self.enabled_plugins

        # Initialize plugins in dependency order (if we had dependencies)
        initialized = {}
        for plugin_name in enabled_plugins:
            instance = self.initialize_plugin(plugin_name, client)
            if instance:
                initialized[plugin_name] = instance

        return initialized
