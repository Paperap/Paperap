

import unittest
from string import Template
from typing import override
from unittest.mock import MagicMock

from pydantic import ValidationError

from paperap.models import StandardModel
from paperap.resources.base import BaseResource
from tests.lib import UnitTestCase


class ExampleModel(StandardModel):
    name : str | None = None

class TestBaseResource(UnitTestCase):
    # TODO: All methods in this class are AI Generated Tests (gpt 4oo). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        class TestResource(BaseResource):
            model_class = ExampleModel
            endpoints = {
                "list": Template("http://example.com")
            }

        self.resource = TestResource(self.client) # type: ignore

    def test_all(self):
        self.resource.queryset_class = MagicMock(return_value="queryset") # type: ignore
        self.assertEqual(self.resource.all(), "queryset")

    def test_filter(self):
        self.resource.queryset_class = MagicMock() # type: ignore
        self.resource.queryset_class.return_value.filter.return_value = "filtered_queryset" # type: ignore
        result = self.resource.filter(name="test")
        self.assertEqual(result, "filtered_queryset")

    def test_create_model(self):
        model_instance = self.resource.create_model(name="TestModel")
        self.assertEqual(model_instance.name, "TestModel")

    def test_transform_data_output(self):
        transformed = self.resource.transform_data_output(name="TestModel")
        self.assertEqual(transformed["name"], "TestModel")

    def test_endpoints_converted_to_template_init(self):
        class FooResource(BaseResource):
            model_class = MagicMock()
            endpoints = {
                "list": "http://example.com/fooresource/" # type: ignore
            }

        resource = FooResource(self.client)
        self.assertIsInstance(resource.endpoints, dict)
        self.assertIsInstance(resource.endpoints["list"], Template) # type: ignore
        self.assertEqual(resource.endpoints["list"].safe_substitute(), "http://example.com/fooresource/") # type: ignore


if __name__ == "__main__":
    unittest.main()
