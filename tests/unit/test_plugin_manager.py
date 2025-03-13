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
import unittest
from unittest.mock import MagicMock, patch
from paperap.plugin_manager import PluginManager, Plugin

class TestPluginManager(unittest.TestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    def setUp(self):
        self.manager = PluginManager()

    def test_discover_plugins(self):
        with patch("importlib.import_module") as mock_import:
            self.manager.discover_plugins("paperap.plugins")
            mock_import.assert_called()

    def test_configure(self):
        config = {"enabled_plugins": ["TestPlugin"], "settings": {}}
        self.manager.configure(config)
        self.assertEqual(self.manager.config, config)

    def test_initialize_plugin(self):
        mock_plugin = MagicMock(spec=Plugin)
        self.manager.plugins["TestPlugin"] = mock_plugin
        client = MagicMock()
        instance = self.manager.initialize_plugin("TestPlugin", client)
        self.assertIsNotNone(instance)

    def test_initialize_nonexistent_plugin(self):
        client = MagicMock()
        instance = self.manager.initialize_plugin("NonExistentPlugin", client)
        self.assertIsNone(instance)

    def test_initialize_plugin_with_exception(self):
        class FailingPlugin(Plugin):
            def setup(self):
                raise RuntimeError("Setup failed")

            def teardown(self):
                pass

        self.manager.plugins["FailingPlugin"] = FailingPlugin
        client = MagicMock()
        instance = self.manager.initialize_plugin("FailingPlugin", client)
        self.assertIsNone(instance)

if __name__ == "__main__":
    unittest.main()
