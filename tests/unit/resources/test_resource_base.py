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
from typing import override
import unittest
from unittest.mock import MagicMock
from paperap.resources.base import BaseResource

class TestBaseResource(unittest.TestCase):
    # TODO: All methods in this class are AI Generated Tests (gpt 4oo). Will remove this comment when they are removed.

    @override
    def setUp(self):
        self.mock_client = MagicMock()
        class TestResource(BaseResource):
            model_class = MagicMock()
            endpoints = {}

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

if __name__ == "__main__":
    unittest.main()
