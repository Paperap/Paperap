

import tempfile
import unittest
from typing import Any, override
from unittest.mock import MagicMock, patch

from paperap.plugins import Plugin
from paperap.plugins.manager import PluginConfig, PluginManager
from tests.lib import UnitTestCase


class TestPluginManager(UnitTestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    @override
    def setUp(self):
        super().setUp()
        self.manager = PluginManager(client=self.client)

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
        instance = self.manager.initialize_plugin("TestPlugin")
        self.assertIsNotNone(instance)

    def test_initialize_nonexistent_plugin(self):
        with self.assertLogs(level="WARNING"):
            instance = self.manager.initialize_plugin("NonExistentPlugin")
            self.assertIsNone(instance)

    def test_initialize_plugin_with_exception(self):
        class FailingPlugin(Plugin):
            name = "FailingPlugin"
            @override
            def setup(self):
                raise RuntimeError("Setup failed")

            @override
            def teardown(self):
                pass

        with self.assertLogs(level="WARNING"):
            self.manager.plugins["FailingPlugin"] = FailingPlugin
            instance = self.manager.initialize_plugin("FailingPlugin")
            self.assertIsNone(instance)

if __name__ == "__main__":
    unittest.main()
