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
from paperap.plugins.base import Plugin

class TestPlugin(unittest.TestCase):
    # All tests in this class were AI Generated (gpt-4o). Will remove this message when they are reviewed.
    def test_plugin_initialization(self):
        mock_client = MagicMock()
        class TestPlugin(Plugin):
            @override
            def setup(self): 
                pass
            @override
            def teardown(self): 
                pass

        plugin = TestPlugin(mock_client)
        self.assertEqual(plugin.client, mock_client)

    def test_plugin_config(self):
        mock_client = MagicMock()
        class TestPlugin(Plugin):
            @override
            def setup(self): 
                pass
            @override
            def teardown(self): 
                pass

        plugin = TestPlugin(mock_client, option1="value1", option2=42)
        self.assertEqual(plugin.config["option1"], "value1")
        self.assertEqual(plugin.config["option2"], 42)

    def test_plugin_get_config_schema_default(self):
        class TestPlugin(Plugin):
            @override
            def setup(self): 
                pass
            @override
            def teardown(self): 
                pass

        self.assertEqual(TestPlugin.get_config_schema(), {"option1": str, "option2": int})

    def test_plugin_get_config_schema(self):
        class TestPlugin(Plugin):
            @override
            def setup(self): 
                pass
            @override
            def teardown(self): 
                pass
            
            @override
            @classmethod
            def get_config_schema(cls) -> dict[str, Any]:
                return {"option1": str, "option2": int}

        self.assertEqual(TestPlugin.get_config_schema(), {"option1": str, "option2": int})

    def test_plugin_get_config_schema_with_extra_option(self):
        class ExtraOptionPlugin(Plugin):
            @override
            def setup(self): 
                pass
            @override
            def teardown(self): 
                pass
            @override
            @classmethod
            def get_config_schema(cls) -> dict[str, Any]:
                return {"option1": str, "option2": int, "option3": bool}

        self.assertEqual(ExtraOptionPlugin.get_config_schema(), {"option1": str, "option2": int, "option3": bool})

if __name__ == "__main__":
    unittest.main()
