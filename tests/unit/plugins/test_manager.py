"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_manager.py
        Project: paperap
        Created: 2025-03-21
        Version: 0.0.9
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-21     By Jess Mann

"""


from __future__ import annotations

import unittest
from unittest import mock
import importlib
import sys
from typing import Any, Dict, List, Type

import pydantic

from paperap.client import PaperlessClient
from paperap.plugins.base import Plugin
from paperap.plugins.manager import PluginManager, PluginConfig


class MockPlugin(Plugin):
    """Mock plugin for testing."""
    
    def __init__(self, manager: PluginManager, **kwargs: Any) -> None:
        """Initialize the mock plugin."""
        super().__init__(**kwargs)
        self.manager = manager
        self.initialized_with = kwargs


class AnotherMockPlugin(Plugin):
    """Another mock plugin for testing."""
    
    def __init__(self, manager: PluginManager, **kwargs: Any) -> None:
        """Initialize the mock plugin."""
        super().__init__(**kwargs)
        self.manager = manager
        self.initialized_with = kwargs


class TestPluginManager(unittest.TestCase):
    """
    Test suite for the PluginManager class.
    """

    def setUp(self) -> None:
        """
        Written By claude
        
        Set up test fixtures before each test method.
        Creates a mock client and initializes a PluginManager instance.
        """
        self.mock_client = mock.MagicMock(spec=PaperlessClient)
        self.manager = PluginManager(client=self.mock_client)

    def test_init(self) -> None:
        """
        Written By claude
        
        Test that the PluginManager initializes with the expected default values.
        """
        self.assertEqual(self.manager.plugins, {})
        self.assertEqual(self.manager.instances, {})
        self.assertEqual(
            self.manager.config, 
            {"enabled_plugins": [], "settings": {}}
        )
        self.assertEqual(self.manager.client, self.mock_client)

    def test_enabled_plugins_with_config(self) -> None:
        """
        Written By claude
        
        Test that enabled_plugins property returns the configured list when available.
        """
        # Set up
        self.manager.config = {
            "enabled_plugins": ["Plugin1", "Plugin2"],
            "settings": {}
        }
        
        # Test
        self.assertEqual(self.manager.enabled_plugins, ["Plugin1", "Plugin2"])

    def test_enabled_plugins_without_config(self) -> None:
        """
        Written By claude
        
        Test that enabled_plugins property returns all discovered plugins when
        no enabled_plugins list is configured.
        """
        # Set up
        self.manager.plugins = {"Plugin1": MockPlugin, "Plugin2": AnotherMockPlugin}
        self.manager.config = {
            "enabled_plugins": [],
            "settings": {}
        }
        
        # Test
        self.assertEqual(set(self.manager.enabled_plugins), {"Plugin1", "Plugin2"})

    @mock.patch('importlib.import_module')
    @mock.patch('pkgutil.iter_modules')
    @mock.patch('inspect.getmembers')
    def test_discover_plugins(
        self, 
        mock_getmembers: mock.MagicMock, 
        mock_iter_modules: mock.MagicMock, 
        mock_import_module: mock.MagicMock
    ) -> None:
        """
        Written By claude
        
        Test that discover_plugins correctly finds and registers plugin classes.
        """
        # Set up mocks
        mock_package = mock.MagicMock()
        mock_package.__path__ = ["some/path"]
        mock_import_module.return_value = mock_package
        
        mock_module = mock.MagicMock()
        mock_module.__name__ = "test_module"
        
        # Mock a plugin class
        mock_plugin_class = mock.MagicMock(spec=type)
        mock_plugin_class.__name__ = "TestPlugin"
        mock_plugin_class.__module__ = "paperap.plugins.test_module"
        
        # Set up the module iteration
        mock_iter_modules.return_value = [
            (None, "paperap.plugins.test_module", False)
        ]
        
        # Set up class inspection
        mock_getmembers.return_value = [
            ("TestPlugin", mock_plugin_class)
        ]
        
        # Make the mock plugin class appear to be a subclass of Plugin
        def is_subclass_side_effect(cls, parent):
            if parent is Plugin and cls is mock_plugin_class:
                return True
            return False
        
        with mock.patch('inspect.isclass', return_value=True):
            with mock.patch('builtins.issubclass', side_effect=is_subclass_side_effect):
                # Call the method
                self.manager.discover_plugins()
                
                # Verify the plugin was registered
                self.assertIn("TestPlugin", self.manager.plugins)
                self.assertEqual(self.manager.plugins["TestPlugin"], mock_plugin_class)

    def test_configure_with_config_dict(self) -> None:
        """
        Written By claude
        
        Test that configure correctly updates the manager's configuration
        when provided with a PluginConfig dictionary.
        """
        # Set up
        config: PluginConfig = {
            "enabled_plugins": ["Plugin1"],
            "settings": {"Plugin1": {"setting1": "value1"}}
        }
        
        # Call the method
        self.manager.configure(config)
        
        # Verify the configuration was updated
        self.assertEqual(self.manager.config, config)

    def test_configure_with_kwargs(self) -> None:
        """
        Written By claude
        
        Test that configure correctly updates the manager's configuration
        when provided with keyword arguments.
        """
        # Set up
        enabled_plugins = ["Plugin1"]
        settings = {"Plugin1": {"setting1": "value1"}}
        
        # Call the method
        self.manager.configure(enabled_plugins=enabled_plugins, settings=settings)
        
        # Verify the configuration was updated
        self.assertEqual(self.manager.config["enabled_plugins"], enabled_plugins)
        self.assertEqual(self.manager.config["settings"], settings)

    def test_configure_with_unexpected_kwargs(self) -> None:
        """
        Written By claude
        
        Test that configure logs a warning when provided with unexpected keyword arguments.
        """
        # Set up
        with mock.patch('paperap.plugins.manager.logger.warning') as mock_warning:
            # Call the method with an unexpected kwarg
            self.manager.configure(unexpected_key="value")
            
            # Verify a warning was logged
            mock_warning.assert_called_once()
            self.assertIn("Unexpected configuration keys", mock_warning.call_args[0][0])

    def test_get_plugin_config(self) -> None:
        """
        Written By claude
        
        Test that get_plugin_config returns the correct configuration for a plugin.
        """
        # Set up
        self.manager.config = {
            "enabled_plugins": ["Plugin1"],
            "settings": {"Plugin1": {"setting1": "value1"}}
        }
        
        # Test with an existing plugin
        config = self.manager.get_plugin_config("Plugin1")
        self.assertEqual(config, {"setting1": "value1"})
        
        # Test with a non-existent plugin
        config = self.manager.get_plugin_config("NonExistentPlugin")
        self.assertEqual(config, {})

    def test_initialize_plugin_already_initialized(self) -> None:
        """
        Written By claude
        
        Test that initialize_plugin returns the existing instance if the plugin
        has already been initialized.
        """
        # Set up
        mock_instance = mock.MagicMock(spec=Plugin)
        self.manager.instances = {"TestPlugin": mock_instance}
        
        # Call the method
        result = self.manager.initialize_plugin("TestPlugin")
        
        # Verify the existing instance was returned
        self.assertEqual(result, mock_instance)

    def test_initialize_plugin_not_found(self) -> None:
        """
        Written By claude
        
        Test that initialize_plugin returns None and logs a warning if the plugin
        is not found.
        """
        # Set up
        with mock.patch('paperap.plugins.manager.logger.warning') as mock_warning:
            # Call the method with a non-existent plugin
            result = self.manager.initialize_plugin("NonExistentPlugin")
            
            # Verify None was returned and a warning was logged
            self.assertIsNone(result)
            mock_warning.assert_called_once()
            self.assertIn("Plugin not found", mock_warning.call_args[0][0])

    def test_initialize_plugin_success(self) -> None:
        """
        Written By claude
        
        Test that initialize_plugin correctly initializes a plugin and returns the instance.
        """
        # Set up
        self.manager.plugins = {"MockPlugin": MockPlugin}
        self.manager.config = {
            "enabled_plugins": ["MockPlugin"],
            "settings": {"MockPlugin": {"setting1": "value1"}}
        }
        
        # Call the method
        with mock.patch('paperap.plugins.manager.logger.info') as mock_info:
            result = self.manager.initialize_plugin("MockPlugin")
            
            # Verify the plugin was initialized correctly
            self.assertIsInstance(result, MockPlugin)
            self.assertEqual(result.initialized_with, {"setting1": "value1"})
            self.assertEqual(self.manager.instances["MockPlugin"], result)
            mock_info.assert_called_once()
            self.assertIn("Initialized plugin", mock_info.call_args[0][0])

    def test_initialize_plugin_exception(self) -> None:
        """
        Written By claude
        
        Test that initialize_plugin handles exceptions during plugin initialization.
        """
        # Set up a plugin class that raises an exception when initialized
        class ExceptionPlugin(Plugin):
            def __init__(self, **kwargs: Any) -> None:
                raise ValueError("Test exception")
        
        self.manager.plugins = {"ExceptionPlugin": ExceptionPlugin}
        
        # Call the method
        with mock.patch('paperap.plugins.manager.logger.error') as mock_error:
            result = self.manager.initialize_plugin("ExceptionPlugin")
            
            # Verify None was returned and an error was logged
            self.assertIsNone(result)
            mock_error.assert_called_once()
            self.assertIn("Failed to initialize plugin", mock_error.call_args[0][0])

    def test_initialize_all_plugins(self) -> None:
        """
        Written By claude
        
        Test that initialize_all_plugins correctly initializes all enabled plugins.
        """
        # Set up
        self.manager.plugins = {
            "MockPlugin": MockPlugin,
            "AnotherMockPlugin": AnotherMockPlugin
        }
        self.manager.config = {
            "enabled_plugins": ["MockPlugin", "AnotherMockPlugin"],
            "settings": {
                "MockPlugin": {"setting1": "value1"},
                "AnotherMockPlugin": {"setting2": "value2"}
            }
        }
        
        # Call the method
        result = self.manager.initialize_all_plugins()
        
        # Verify all plugins were initialized
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result["MockPlugin"], MockPlugin)
        self.assertIsInstance(result["AnotherMockPlugin"], AnotherMockPlugin)
        self.assertEqual(result["MockPlugin"].initialized_with, {"setting1": "value1"})
        self.assertEqual(result["AnotherMockPlugin"].initialized_with, {"setting2": "value2"})

    def test_initialize_all_plugins_with_failure(self) -> None:
        """
        Written By claude
        
        Test that initialize_all_plugins continues initializing plugins even if
        some fail to initialize.
        """
        # Set up a plugin class that raises an exception when initialized
        class ExceptionPlugin(Plugin):
            def __init__(self, **kwargs: Any) -> None:
                raise ValueError("Test exception")
        
        self.manager.plugins = {
            "MockPlugin": MockPlugin,
            "ExceptionPlugin": ExceptionPlugin
        }
        self.manager.config = {
            "enabled_plugins": ["MockPlugin", "ExceptionPlugin"],
            "settings": {
                "MockPlugin": {"setting1": "value1"}
            }
        }
        
        # Call the method
        with mock.patch('paperap.plugins.manager.logger.error'):
            result = self.manager.initialize_all_plugins()
            
            # Verify the successful plugin was initialized
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result["MockPlugin"], MockPlugin)
            self.assertEqual(result["MockPlugin"].initialized_with, {"setting1": "value1"})


if __name__ == '__main__':
    unittest.main()
