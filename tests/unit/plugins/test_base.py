"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_base.py
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
from typing import Any, ClassVar, Dict, override
from unittest.mock import MagicMock, patch

import pydantic

from paperap.plugins.base import ConfigType, Plugin
from paperap.exceptions import ModelValidationError


class ValidPlugin(Plugin):
    """A valid plugin implementation for testing."""

    name: ClassVar[str] = "ValidPlugin"
    description: ClassVar[str] = "A valid plugin for testing"
    version: ClassVar[str] = "1.0.0"

    # Config fields
    test_field: str = "default"
    optional_field: int | None = None

    @override
    def setup(self) -> None:
        """
        Written by Claude

        Setup method implementation for testing.
        """
        pass

    @override
    def teardown(self) -> None:
        """
        Written by Claude

        Teardown method implementation for testing.
        """
        pass

    @classmethod
    @override
    def get_config_schema(cls) -> dict[str, ConfigType]:
        """
        Written by Claude

        Custom config schema for testing.
        """
        return {
            "test_field": {
                "type": str,
                "description": "A test field",
                "required": True,
            },
            "optional_field": {
                "type": int,
                "description": "An optional field",
                "required": False,
            }
        }


class TestPlugin(unittest.TestCase):
    """
    Written by Claude

    Test cases for the Plugin base class.
    """

    @override
    def setUp(self) -> None:
        """
        Written by Claude

        Set up test fixtures.
        """
        self.mock_manager = MagicMock()
        self.mock_client = MagicMock()
        self.mock_manager.client = self.mock_client

    def test_plugin_initialization(self) -> None:
        """
        Written by Claude

        Test that a valid plugin can be initialized.
        """
        plugin = ValidPlugin(manager=self.mock_manager)

        self.assertEqual(plugin.name, "ValidPlugin")
        self.assertEqual(plugin.description, "A valid plugin for testing")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.test_field, "default")
        self.assertIsNone(plugin.optional_field)
        self.assertEqual(plugin.manager, self.mock_manager)
        self.assertEqual(plugin.client, self.mock_client)

    def test_plugin_with_config(self) -> None:
        """
        Written by Claude

        Test that a plugin can be initialized with configuration.
        """
        plugin = ValidPlugin(
            manager=self.mock_manager,
            test_field="custom",
            optional_field=42
        )

        self.assertEqual(plugin.test_field, "custom")
        self.assertEqual(plugin.optional_field, 42)

    def test_plugin_name_required(self) -> None:
        """
        Written by Claude

        Test that a plugin must have a name.
        """
        with self.assertRaises(ValueError):
            # Create a plugin class without a name
            class InvalidPlugin(Plugin):
                @override
                def setup(self) -> None:
                    pass

                @override
                def teardown(self) -> None:
                    pass

    def test_abstract_methods(self) -> None:
        """
        Written by Claude

        Test that abstract methods must be implemented.
        """
        # Test missing setup method
        with self.assertRaises(TypeError):
            class MissingSetupPlugin(Plugin):
                name: ClassVar[str] = "MissingSetupPlugin"

                @override
                def teardown(self) -> None:
                    pass

            MissingSetupPlugin(manager=self.mock_manager)

        # Test missing teardown method
        with self.assertRaises(TypeError):
            class MissingTeardownPlugin(Plugin):
                name: ClassVar[str] = "MissingTeardownPlugin"

                @override
                def setup(self) -> None:
                    pass

            MissingTeardownPlugin(manager=self.mock_manager)

    def test_get_config_schema_default(self) -> None:
        """
        Written by Claude

        Test the default config schema.
        """
        class MinimalPlugin(Plugin):
            name: ClassVar[str] = "MinimalPlugin"

            @override
            def setup(self) -> None:
                pass

            @override
            def teardown(self) -> None:
                pass

        # Default implementation should return an empty dict
        self.assertEqual(MinimalPlugin.get_config_schema(), {})

    def test_get_config_schema_custom(self) -> None:
        """
        Written by Claude

        Test a custom config schema.
        """
        schema = ValidPlugin.get_config_schema()

        self.assertIn("test_field", schema)
        self.assertIn("optional_field", schema)

        self.assertEqual(schema["test_field"]["type"], str)
        self.assertEqual(schema["test_field"]["description"], "A test field")
        self.assertTrue(schema["test_field"]["required"])

        self.assertEqual(schema["optional_field"]["type"], int)
        self.assertEqual(schema["optional_field"]["description"], "An optional field")
        self.assertFalse(schema["optional_field"]["required"])

    def test_setup_called_on_init(self) -> None:
        """
        Written by Claude

        Test that setup is called during initialization.
        """
        setup_called = False

        class SetupTestPlugin(Plugin):
            name: ClassVar[str] = "SetupTestPlugin"

            @override
            def setup(self) -> None:
                nonlocal setup_called
                setup_called = True

            @override
            def teardown(self) -> None:
                pass

        plugin = SetupTestPlugin(manager=self.mock_manager)
        self.assertTrue(setup_called)

    def test_validation(self) -> None:
        """
        Written by Claude

        Test that plugin configuration is validated.
        """
        # Test with invalid type
        with self.assertRaises(pydantic.ValidationError):
            ValidPlugin(
                manager=self.mock_manager,
                test_field=123,  # Should be a string
            )

        # Test with invalid optional field
        with self.assertRaises(pydantic.ValidationError):
            ValidPlugin(
                manager=self.mock_manager,
                optional_field="not an int",  # Should be an int
            )

    def test_extra_fields_ignored(self) -> None:
        """
        Written by Claude

        Test that extra fields are ignored.
        """
        plugin = ValidPlugin(
            manager=self.mock_manager,
            extra_field="should be ignored"
        )

        # Should not have the extra field
        with self.assertRaises(AttributeError):
            plugin.extra_field

    def test_required_manager(self) -> None:
        """
        Written by Claude

        Test that manager is required.
        """
        with self.assertRaises(pydantic.ValidationError):
            ValidPlugin()  # Missing required manager

    def test_client_property(self) -> None:
        """
        Written by Claude

        Test the client property.
        """
        plugin = ValidPlugin(manager=self.mock_manager)
        self.assertEqual(plugin.client, self.mock_client)

        # Change the client and verify the property reflects the change
        new_client = MagicMock()
        self.mock_manager.client = new_client
        self.assertEqual(plugin.client, new_client)


if __name__ == "__main__":
    unittest.main()
