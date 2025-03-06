"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_base.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from paperap.exceptions import FilterDisabledError
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.tests import TestCase
from unittest.mock import patch
from paperap.tests import TestCase
from paperap.models import StandardModel
from paperap.client import PaperlessClient
from paperap.resources.base import PaperlessResource, StandardResource, StandardResource

class ExampleModel(StandardModel):
    """
    Example model for testing purposes.
    """
    a_str : str
    a_date : datetime
    an_int : int
    a_float : float
    a_bool : bool

class ExampleResource(StandardResource):
    """
    Example resource for testing purposes.
    """
    name = "example"
    model_class = ExampleModel

class TestModel(TestCase):
    def setUp(self):
        # Setup a sample model instance
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
            self.client = PaperlessClient()
        self.resource = ExampleResource(self.client)
        self.model_data = {
            "id": 1,
            "a_str": "Hello, world!",
            "a_date": "2020-05-12T12:00:00Z",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True
        }
        self.model = ExampleModel.from_dict(self.model_data, self.resource)

    def test_model_initialization(self):
        # Test if the model is initialized correctly
        self.assertEqual(self.model.id, self.model_data["id"])
        self.assertEqual(self.model.a_str, self.model_data["a_str"])
        self.assertEqual(self.model.an_int, self.model_data["an_int"])
        self.assertEqual(self.model.a_float, self.model_data["a_float"])
        self.assertEqual(self.model.a_bool, self.model_data["a_bool"])

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.a_date, datetime)

        # TZ UTC
        self.assertEqual(self.model.a_date, datetime(2020, 5, 12, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["id"], self.model_data["id"])
        self.assertEqual(model_dict["a_str"], self.model_data["a_str"])
        self.assertEqual(model_dict["an_int"], self.model_data["an_int"])
        self.assertEqual(model_dict["a_float"], self.model_data["a_float"])
        self.assertEqual(model_dict["a_bool"], self.model_data["a_bool"])

        self.assertEqual(model_dict["a_date"], datetime(2020, 5, 12, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_update_int(self):
        test_cases = [
            ({"an_int": 100}, 100),
            ({"an_int": 0}, 0),
            ({"an_int": -1}, -1),
        ]
        for update_data, expected_value in test_cases:
            updated_model = self.model.update(**update_data)
            self.assertEqual(updated_model.an_int, expected_value)

    def test_model_update_str(self):
        test_cases = [
            ({"a_str": "New value"}, "New value"),
            ({"a_str": ""}, ""),
            ({"a_str": " "}, " "),
        ]
        for update_data, expected_value in test_cases:
            updated_model = self.model.update(**update_data)
            self.assertEqual(updated_model.a_str, expected_value)

    def test_model_update_float(self):
        test_cases = [
            ({"a_float": 3.14159}, 3.14159),
            ({"a_float": 0.0}, 0.0),
            ({"a_float": -1.0}, -1.0),
        ]
        for update_data, expected_value in test_cases:
            updated_model = self.model.update(**update_data)
            self.assertEqual(updated_model.a_float, expected_value)

    def test_model_update_bool(self):
        test_cases = [
            ({"a_bool": False}, False),
            ({"a_bool": True}, True),
        ]
        for update_data, expected_value in test_cases:
            updated_model = self.model.update(**update_data)
            self.assertEqual(updated_model.a_bool, expected_value)

class TestClassAttributes(TestCase):
    def test_filtering_fields(self):
        expected_fields = {"id", "a_str", "a_date", "an_int", "a_float", "a_bool"}
        self.assertEqual(set(ExampleModel._meta.filtering_fields), expected_fields)

    def test_new_fields_in_filtering_fields(self):
        class NewFieldsModel(StandardModel):
            a_str: str
            an_int : int
            a_date : datetime

        # Inherited ID included
        self.assertIn("id", NewFieldsModel._meta.filtering_fields)
        # New fields included
        self.assertIn("a_str", NewFieldsModel._meta.filtering_fields)
        self.assertIn("an_int", NewFieldsModel._meta.filtering_fields)
        self.assertIn("a_date", NewFieldsModel._meta.filtering_fields)

    def test_filtering_fields_excludes_disabled(self):
        class DisabledFieldsModel(StandardModel):
            # Fields to disable
            a_str_no: str
            an_int_no : int
            a_date_no : datetime
            # Fields to include
            a_str_yes: str
            an_int_yes : int
            a_date_yes : datetime

            class Meta(StandardModel.Meta):
                filtering_disabled = {"a_str_no", "an_int_no", "a_date_no"}

        # Inherited ID included
        self.assertIn("id", DisabledFieldsModel._meta.filtering_fields)
        # Disabled field excluded
        self.assertNotIn("a_str_no", DisabledFieldsModel._meta.filtering_fields)
        self.assertNotIn("an_int_no", DisabledFieldsModel._meta.filtering_fields)
        self.assertNotIn("a_date_no", DisabledFieldsModel._meta.filtering_fields)
        # Enabled field included
        self.assertIn("a_str_yes", DisabledFieldsModel._meta.filtering_fields)
        self.assertIn("an_int_yes", DisabledFieldsModel._meta.filtering_fields)
        self.assertIn("a_date_yes", DisabledFieldsModel._meta.filtering_fields)

    def test_read_only_doesnt_influence_filtering_fields(self):
        class ReadOnlyFieldsModel(StandardModel):
            # Fields to disable
            a_str_no: str
            an_int_no : int
            a_date_no : datetime
            # Fields to include
            a_str_yes: str
            an_int_yes : int
            a_date_yes : datetime

            class Meta(StandardModel.Meta):
                read_only_fields = {"a_str_no", "an_int_no", "a_date_no"}

        # Inherited ID included
        self.assertIn("id", ReadOnlyFieldsModel._meta.filtering_fields)
        # All fields included
        self.assertIn("a_str_no", ReadOnlyFieldsModel._meta.filtering_fields)
        self.assertIn("an_int_no", ReadOnlyFieldsModel._meta.filtering_fields)
        self.assertIn("a_date_no", ReadOnlyFieldsModel._meta.filtering_fields)
        self.assertIn("a_str_yes", ReadOnlyFieldsModel._meta.filtering_fields)
        self.assertIn("an_int_yes", ReadOnlyFieldsModel._meta.filtering_fields)
        self.assertIn("a_date_yes", ReadOnlyFieldsModel._meta.filtering_fields)

    def test_can_disable_inherited(self):
        class DisabledInheritedModel(StandardModel):
            a_str: str
            an_int : int
            a_date : datetime

            class Meta(StandardModel.Meta):
                filtering_disabled = {"id"}

        # Inherited ID excluded
        self.assertNotIn("id", DisabledInheritedModel._meta.filtering_fields)
        # New fields included
        self.assertIn("a_str", DisabledInheritedModel._meta.filtering_fields)
        self.assertIn("an_int", DisabledInheritedModel._meta.filtering_fields)
        self.assertIn("a_date", DisabledInheritedModel._meta.filtering_fields)

class TestFilters(TestCase):
    def setUp(self):
        super().setUp()
        
        class DisabledInheritedModel(StandardModel):
            a_str: str
            an_int : int
            a_date : datetime

            class Meta(StandardModel.Meta):
                filtering_disabled = {"a_str", "an_int", "a_date"}
                
        class SampleResource(StandardResource):
            name = "sample"
            model_class = DisabledInheritedModel

        self.resource = SampleResource(self.client)
        self.qs = StandardQuerySet(self.resource)
            
    def test_calling_a_disabled_filter_raises(self):
        disabled_filters = {
            'a_str': 'example',
            'an_int': 5,
            'a_date': datetime(2020, 5, 12, 12, 0, 0, tzinfo=timezone.utc),
        }
        suffixes = [
            "__eq",
            "__range",
            "__lt",
            "__lte",
            "__gt",
            "__gte",
        ]
        for filter_name, value in disabled_filters.items():
            for suffix in suffixes:
                with self.subTest(suffix=suffix, filter_name=filter_name):
                    key = f"{filter_name}{suffix}"
                    kwargs = {key: value}
                    with self.assertRaises(FilterDisabledError, msg=f"Filtering with {suffix} does not raise exception"):
                        self.qs.filter(**kwargs)

if __name__ == "__main__":
    unittest.main()
