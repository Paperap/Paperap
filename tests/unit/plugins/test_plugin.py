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
        self.assertEqual(plugin.config["option1"], "value1")
        self.assertEqual(plugin.config["option2"], 42)

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

    def test_plugin_get_config_schema_with_extra_required(self):
        class ExtraOptionPlugin(Plugin):
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
                    "option1": { "type": str, "required": True },
                    "option2": { "type": int },
                    "option3": { "type": bool }
                }

        self.assertEqual(ExtraOptionPlugin.get_config_schema(), {"option1": { "type": str, "required": True }, "option2": { "type": int }, "option3": { "type": bool }})

        _instance = ExtraOptionPlugin(manager=self.manager, option1="value1", option2=42, option3=True) # type: ignore

        with self.assertRaises(ModelValidationError):
            _2instance = ExtraOptionPlugin(manager=self.manager, option2=42, option3=True) # type: ignore
            print(_2instance.get_config_schema())
            print(_2instance.config)

class TestPluginConfigValidation(UnitTestCase):
    @override
    def setUp(self):
        super().setUp()
        self.manager = PluginManager(client=self.client)

    def test_valid_config(self):
        """Test that valid configurations pass validation."""
        valid_config = {"test_dir": "/tmp", "max_files": 10}
        plugin = MockPlugin(manager=self.manager, **valid_config) # type: ignore
        self.assertEqual(plugin.config, valid_config)

    def test_missing_required_config(self):
        """Test that missing required fields raise a ValidationError."""
        invalid_config = {"max_files": 10}  # Missing 'test_dir'
        with self.assertRaises(ValueError) as context:
            MockPlugin(manager=self.manager, **invalid_config) # type: ignore
        self.assertIn("Missing required configuration parameter: test_dir", str(context.exception))

    def test_invalid_type_config(self):
        """Test that incorrect types raise a ValidationError."""
        invalid_config = {"test_dir": "/tmp", "max_files": "not a number"}
        with self.assertRaises(ValueError) as context:
            MockPlugin(manager=self.manager, **invalid_config) # type: ignore
        self.assertIn("Invalid type for configuration parameter max_files", str(context.exception))

    def test_empty_config(self):
        """Test that an empty configuration raises an error for required fields."""
        with self.assertRaises(ValueError) as context:
            MockPlugin(manager=self.manager)
        self.assertIn("Missing required configuration parameter: test_dir", str(context.exception))

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        valid_config = {"test_dir": "/tmp"}  # 'max_files' omitted
        plugin = MockPlugin(manager=self.manager, **valid_config) # type: ignore
        self.assertEqual(plugin.config, valid_config)

if __name__ == "__main__":
    unittest.main()
