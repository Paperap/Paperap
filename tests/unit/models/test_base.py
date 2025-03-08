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
from pydantic import field_serializer
from paperap.exceptions import FilterDisabledError
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.tests import TestCase
from unittest.mock import patch
from paperap.tests import TestCase
from paperap.models import StandardModel
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

    @field_serializer("a_date")
    def serialize_datetime(self, value: datetime | None, _info):
        return value.isoformat() if value else None

class ExampleResource(StandardResource):
    """
    Example resource for testing purposes.
    """
    name = "example"
    model_class = ExampleModel

class TestBase(TestCase):
    def setUp(self):
        super().setUp()

        self.resource = ExampleResource(self.client)
        self.model_data = {
            "id": 1,
            "a_str": "Hello, world!",
            "a_date": "2020-05-12T12:00:00Z",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True
        }

class TestWithModel(TestBase):

    def setUp(self):
        super().setUp()
        self.model = ExampleModel.from_dict(self.model_data, self.resource)

class TestModelFromDict(TestBase):

    def test_from_dict(self):
        # Test if the model can be created from a dictionary
        model_data = {
            "id": 1,
            "a_str": "Hello, world!",
            "a_date": "2020-05-12T12:00:00Z",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True
        }
        model = ExampleModel.from_dict(model_data, self.resource)
        self.assertIsInstance(model, ExampleModel)
        self.assertIsInstance(model.a_date, datetime)
        self.assertIsInstance(model.a_str, str)
        self.assertIsInstance(model.an_int, int)
        self.assertIsInstance(model.a_float, float)
        self.assertIsInstance(model.a_bool, bool)

        self.assertEqual(model.id, model_data["id"])
        self.assertEqual(model.a_str, model_data["a_str"])
        self.assertEqual(model.an_int, model_data["an_int"])
        self.assertEqual(model.a_float, model_data["a_float"])
        self.assertEqual(model.a_bool, model_data["a_bool"])
        # TODO datetime

class TestModelToDict(TestWithModel):

    def test_to_dict_options(self):
        # Test if the model can be converted to a dictionary with different options
        model_dict = self.model.to_dict(include_read_only=False)
        self.assertNotIn("id", model_dict)

        model_dict = self.model.to_dict(exclude_none=False)
        self.assertIn("a_str", model_dict)

    def test_create_method(self):
        # Test if a new model instance can be created
        new_model = ExampleModel.create(
            id=2,
            a_str="New Model",
            a_date="2021-01-01T00:00:00Z",
            an_int=100,
            a_float=1.23,
            a_bool=False,
            resource=self.resource
        )
        self.assertEqual(new_model.id, 2)
        self.assertEqual(new_model.a_str, "New Model")

    def test_update_method(self):
        # Test if the model can be updated
        self.model.update_locally(a_str="Updated String")
        self.assertEqual(self.model.a_str, "Updated String")

    def test_is_new_method(self):
        # Test if the is_new method works correctly
        new_model = ExampleModel.create(
            a_str="New Model",
            a_date="2021-01-01T00:00:00Z",
            an_int=100,
            a_float=1.23,
            a_bool=False,
            resource=self.resource
        )
        self.assertTrue(new_model.is_new())
        self.assertFalse(self.model.is_new())

class TestModel(TestWithModel):
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

        self.assertEqual(model_dict["a_date"], "2020-05-12T12:00:00+00:00")

    def test_model_update_int(self):
        test_cases = [
            ({"an_int": 100}, 100),
            ({"an_int": 0}, 0),
            ({"an_int": -1}, -1),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data)
            self.assertEqual(self.model.an_int, expected_value)

    def test_model_update_str(self):
        test_cases = [
            ({"a_str": "New value"}, "New value"),
            ({"a_str": ""}, ""),
            ({"a_str": " "}, " "),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data)
            self.assertEqual(self.model.a_str, expected_value)

    def test_model_update_float(self):
        test_cases = [
            ({"a_float": 3.14159}, 3.14159),
            ({"a_float": 0.0}, 0.0),
            ({"a_float": -1.0}, -1.0),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data)
            self.assertEqual(self.model.a_float, expected_value)

    def test_model_update_bool(self):
        test_cases = [
            ({"a_bool": False}, False),
            ({"a_bool": True}, True),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data)
            self.assertEqual(self.model.a_bool, expected_value)

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
