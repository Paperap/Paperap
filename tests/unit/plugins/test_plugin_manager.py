"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_plugin_manager.py
        Project: paperap
        Created: 2025-03-13
        Version: 0.0.7
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-13     By Jess Mann

"""
from typing import Any, override
import unittest
from unittest.mock import MagicMock, patch
from paperap.plugins.manager import PluginConfig, PluginManager
from paperap.plugins import Plugin
from paperap.tests import UnitTestCase

class TestPluginManager(UnitTestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    @override
    def setUp(self):
        self.manager = PluginManager(client=self.client)

    def test_discover_plugins(self):
        with patch("importlib.import_module") as mock_import, \
             patch("pkgutil.iter_modules") as mock_iter_modules:
            # Mock the package with __path__ attribute
            mock_package = MagicMock()
            mock_package.__path__ = ["some/path"]
            mock_package.__name__ = "paperap.plugins"
            mock_import.return_value = mock_package
            
            # Mock iter_modules to return some modules
            mock_iter_modules.return_value = [
                (None, "plugin1", False),
                (None, "plugin2", True)
            ]
            
            self.manager.discover_plugins("paperap.plugins")
            mock_import.assert_called_with("paperap.plugins")
            mock_iter_modules.assert_called_with(
                mock_package.__path__, 
                mock_package.__name__ + "."
            )

    def test_configure_with_kwargs(self):
        config : dict[str, Any] = {"enabled_plugins": ["TestPlugin"], "settings": {}}
        self.manager.configure(**config)
        self.assertEqual(self.manager.config, config)
        
    def test_configure_with_dict(self):
        config = PluginConfig(enabled_plugins=["TestPlugin"], settings={})
        self.manager.configure(config)
        self.assertEqual(self.manager.config, config)

    def test_initialize_plugin(self):
        mock_plugin = MagicMock(spec=Plugin)
        self.manager.plugins["TestPlugin"] = mock_plugin  # type: ignore
        client = MagicMock()
        instance = self.manager.initialize_plugin("TestPlugin", client)
        self.assertIsNotNone(instance)

    def test_initialize_nonexistent_plugin(self):
        client = MagicMock()
        instance = self.manager.initialize_plugin("NonExistentPlugin", client)
        self.assertIsNone(instance)

    def test_initialize_plugin_with_exception(self):
        class FailingPlugin(Plugin):
            @override
            def setup(self):
                raise RuntimeError("Setup failed")

            @override
            def teardown(self):
                pass

        self.manager.plugins["FailingPlugin"] = FailingPlugin
        client = MagicMock()
        instance = self.manager.initialize_plugin("FailingPlugin", client)
        self.assertIsNone(instance)

if __name__ == "__main__":
    unittest.main()
