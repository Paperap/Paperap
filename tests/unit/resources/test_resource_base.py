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
from string import Template
from typing import override
import unittest
from unittest.mock import MagicMock

from pydantic import ValidationError
from paperap.resources.base import BaseResource

class TestBaseResource(unittest.TestCase):
    # TODO: All methods in this class are AI Generated Tests (gpt 4oo). Will remove this comment when they are removed.

    @override
    def setUp(self):
        self.mock_client = MagicMock()
        class TestResource(BaseResource):
            model_class = MagicMock()
            endpoints = {
                "list": Template("http://example.com")
            }

        self.resource = TestResource(self.mock_client)

    def test_all(self):
        self.resource._meta.queryset = MagicMock(return_value="queryset") # type: ignore
        self.assertEqual(self.resource.all(), "queryset")

    def test_filter(self):
        self.resource._meta.queryset = MagicMock() # type: ignore
        self.resource._meta.queryset.return_value.filter.return_value = "filtered_queryset" # type: ignore
        result = self.resource.filter(name="test")
        self.assertEqual(result, "filtered_queryset")

    def test_create_model(self):
        model_instance = self.resource.create_model(name="TestModel")
        self.assertEqual(model_instance.name, "TestModel")

    def test_transform_data_output(self):
        transformed = self.resource.transform_data_output(name="TestModel")
        self.assertEqual(transformed["name"], "TestModel")

    def test_endpoints_converted_to_template_setattr(self):
        self.resource.endpoints = {
            "list": "http://newdomain.com/list" # type: ignore
        }
        self.assertIsInstance(self.resource.endpoints, dict)
        self.assertIsInstance(self.resource.endpoints["list"], Template)
        self.assertEqual(self.resource.endpoints["list"], Template("http://newdomain.com/list"))

    def test_update_endpoints_converted_to_template(self):
        self.resource.endpoints["detail"] = "http://example.com/detail" # type: ignore
        self.assertIsInstance(self.resource.endpoints, dict)
        self.assertIsInstance(self.resource.endpoints["detail"], Template)
        self.assertEqual(self.resource.endpoints["detail"], Template("http://example.com/detail"))

    def test_endpoints_converted_to_template_init(self):
        class FooResource(BaseResource):
            model_class = MagicMock()
            endpoints = {
                "list": "http://example.com/fooresource/" # type: ignore
            }

        resource = FooResource(self.mock_client)
        self.assertIsInstance(resource.endpoints, dict)
        self.assertIsInstance(resource.endpoints["list"], Template) # type: ignore
        self.assertEqual(resource.endpoints["list"].safe_substitute(), "http://example.com/fooresource/") # type: ignore

    def test_endpoints_del_list_required(self):
        with self.assertRaises(ValueError):
            del self.resource.endpoints["list"] # type: ignore
            
    def test_endpoints_setattr_list_required(self):
        with self.assertRaises(ValueError):
            self.resource.endpoints = { # type: ignore
                "create": Template("http://example.com") 
            }

    def test_endpoints_init_list_required(self):
        with self.assertRaises(ValueError):
            class BarResource(BaseResource): # type: ignore
                model_class = MagicMock()
                endpoints = {
                    "create": Template("http://example.com") # type: ignore
                }

if __name__ == "__main__":
    unittest.main()
