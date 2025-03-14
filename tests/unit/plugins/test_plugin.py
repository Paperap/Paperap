"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_base.py
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
from unittest.mock import MagicMock
from pydantic import ValidationError
from paperap.exceptions import ModelValidationError
from paperap.plugins.base import Plugin, ConfigType
from paperap.plugins.manager import PluginManager
from paperap.tests import UnitTestCase

class MockPlugin(Plugin):
    """Mock implementation of the Plugin class for testing."""
    name = "MockPlugin"
    description = "A test plugin."
    version = "1.0.0"
    test_dir : str
    max_files : int

    @override
    @classmethod
    def get_config_schema(cls) -> dict[str, ConfigType]:
        return {
            "test_dir": {
                "type": str,
                "description": "Directory to save test data files",
                "required": True,
            },
            "max_files": {
                "type": int,
                "description": "Maximum number of files to process",
                "required": False,
            },
        }

    @override
    def setup(self):
        pass

    @override
    def teardown(self):
        pass

class TestPlugin(UnitTestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.

    @override
    def setUp(self):
        super().setUp()
        self.manager = PluginManager(client=self.client)

    def test_plugin_initialization(self):
        class TestPlugin(Plugin):
            name = "TestPlugin"
            @override
            def setup(self):
                pass
            @override
            def teardown(self):
                pass

        plugin = TestPlugin(manager=self.manager)
        self.assertEqual(plugin.client, self.client)

    def test_plugin_config(self):
        class TestPlugin(Plugin):
            name = "TestPlugin"
            option1: str
            option2: int
            @override
            def setup(self):
                pass
            @override
            def teardown(self):
                pass

            @override
            @classmethod
            def get_config_schema(cls) -> dict[str, ConfigType]:
                return {
                    "option1": { "type": str },
                    "option2": { "type": int }
                }

        plugin = TestPlugin(manager=self.manager, option1="value1", option2=42) # type: ignore
        self.assertEqual(plugin.option1, "value1")
        self.assertEqual(plugin.option2, 42)

    def test_plugin_name_required(self):
        with self.assertRaises(ValueError):
            class TestPlugin(Plugin): # type: ignore
                @override
                def setup(self):
                    pass
                @override
                def teardown(self):
                    pass

    def test_plugin_get_config_schema_default(self):
        class TestPlugin(Plugin):
            name = "TestPlugin"
            @override
            def setup(self):
                pass
            @override
            def teardown(self):
                pass

        self.assertEqual(TestPlugin.get_config_schema(), {})

    def test_plugin_get_config_schema(self):
        class TestPlugin(Plugin):
            name = "testplugin"
            @override
            def setup(self):
                pass
            @override
            def teardown(self):
                pass

            @override
            @classmethod
            def get_config_schema(cls) -> dict[str, ConfigType]:
                return {
                    "option1": { "type": str },
                    "option2": { "type": int }
                }

        self.assertEqual(TestPlugin.get_config_schema(), {"option1": { "type": str }, "option2": { "type": int }})


if __name__ == "__main__":
    unittest.main()
