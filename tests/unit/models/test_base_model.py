

from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from typing import override
from unittest.mock import patch

from pydantic import field_serializer

from paperap.exceptions import FilterDisabledError
from paperap.models import StandardModel
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.resources.base import StandardResource
from tests.lib import UnitTestCase


class ExampleModel(StandardModel):

    """
    Example model for testing purposes.
    """

    a_str : str
    a_date : datetime
    an_int : int
    a_float : float
    a_bool : bool
    an_optional_str : str | None = None
    # Make id field optional for testing is_new_method
    id: int | None = None

    class Meta(StandardModel.Meta):
        save_on_write = False

    @field_serializer("a_date")
    def serialize_datetime(self, value: datetime | None, _info):
        return value.isoformat() if value else None

class ExampleResource(StandardResource[ExampleModel]):

    """
    Example resource for testing purposes.
    """

    name = "example"
    model_class = ExampleModel

class TestBase(UnitTestCase[ExampleModel, ExampleResource]):
    @override
    def setUp(self):
        super().setUp()

        self.resource = ExampleResource(self.client)
        self.model_data_parsed = {
            "id": 1,
            "a_str": "Hello, world!",
            "a_date": "2020-05-12T12:00:00Z",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True,
            "an_optional_str": None
        }

class TestWithModel(TestBase):
    @override
    def setUp(self):
        super().setUp()
        self.model = ExampleModel.from_dict(self.model_data_parsed)

class TestModelFromDict(TestBase):

    def test_from_dict(self):
        # Test if the model can be created from a dictionary
        model_data_parsed = {
            "id": 1,
            "a_str": "Hello, world!",
            "a_date": "2020-05-12T12:00:00Z",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True
        }
        model = ExampleModel.from_dict(model_data_parsed)
        self.assertIsInstance(model, ExampleModel)
        self.assertIsInstance(model.a_date, datetime)
        self.assertIsInstance(model.a_str, str)
        self.assertIsInstance(model.an_int, int)
        self.assertIsInstance(model.a_float, float)
        self.assertIsInstance(model.a_bool, bool)

        self.assertEqual(model.id, model_data_parsed["id"])
        self.assertEqual(model.a_str, model_data_parsed["a_str"])
        self.assertEqual(model.an_int, model_data_parsed["an_int"])
        self.assertEqual(model.a_float, model_data_parsed["a_float"])
        self.assertEqual(model.a_bool, model_data_parsed["a_bool"])
        # TODO datetime

class TestModelToDict(TestWithModel):

    def test_to_dict_options(self):
        # Test if the model can be converted to a dictionary with different options
        model_dict = self.model.to_dict(include_read_only=False)
        self.assertNotIn("id", model_dict)

        model_dict = self.model.to_dict(exclude_none=False)
        self.assertIn("a_str", model_dict)
        self.assertIn("an_optional_str", model_dict)

        model_dict = self.model.to_dict(exclude_none=True)
        self.assertNotIn("an_optional_str", model_dict)

    @patch("paperap.resources.base.StandardResource.create")
    def test_create_method(self, mock_create):
        # Set up the mock to return a model instance
        model_data = {
            "id": 2,
            "a_str": "New Model",
            "a_date": "2021-01-01T00:00:00Z",
            "an_int": 100,
            "a_float": 1.23,
            "a_bool": False
        }
        mock_model = ExampleModel.from_dict(model_data)
        mock_create.return_value = mock_model

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


class TestModel(TestWithModel):
    def test_model_initialization(self):
        # Test if the model is initialized correctly
        self.assertEqual(self.model.id, self.model_data_parsed["id"])
        self.assertEqual(self.model.a_str, self.model_data_parsed["a_str"])
        self.assertEqual(self.model.an_int, self.model_data_parsed["an_int"])
        self.assertEqual(self.model.a_float, self.model_data_parsed["a_float"])
        self.assertEqual(self.model.a_bool, self.model_data_parsed["a_bool"])

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.a_date, datetime)

        # TZ UTC
        self.assertEqual(self.model.a_date, datetime(2020, 5, 12, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["id"], self.model_data_parsed["id"])
        self.assertEqual(model_dict["a_str"], self.model_data_parsed["a_str"])
        self.assertEqual(model_dict["an_int"], self.model_data_parsed["an_int"])
        self.assertEqual(model_dict["a_float"], self.model_data_parsed["a_float"])
        self.assertEqual(model_dict["a_bool"], self.model_data_parsed["a_bool"])

        self.assertEqual(model_dict["a_date"], "2020-05-12T12:00:00+00:00")

    def test_model_update_int(self):
        test_cases = [
            ({"an_int": 100}, 100),
            ({"an_int": 0}, 0),
            ({"an_int": -1}, -1),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data) # type: ignore
            self.assertEqual(self.model.an_int, expected_value)

    def test_model_update_str(self):
        test_cases = [
            ({"a_str": "New value"}, "New value"),
            ({"a_str": ""}, ""),
            ({"a_str": " "}, " "),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data) # type: ignore
            self.assertEqual(self.model.a_str, expected_value)

    def test_model_update_float(self):
        test_cases = [
            ({"a_float": 3.14159}, 3.14159),
            ({"a_float": 0.0}, 0.0),
            ({"a_float": -1.0}, -1.0),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data) # type: ignore
            self.assertEqual(self.model.a_float, expected_value)

    def test_model_update_bool(self):
        test_cases = [
            ({"a_bool": False}, False),
            ({"a_bool": True}, True),
        ]
        for update_data, expected_value in test_cases:
            self.model.update_locally(**update_data)
            self.assertEqual(self.model.a_bool, expected_value)

class TestClassAttributes(UnitTestCase):
    def test_filtering_fields(self):
        expected_fields = {"id", "a_str", "a_date", "an_int", "a_float", "a_bool", "an_optional_str", "_resource"}
        self.assertEqual(set(ExampleModel._meta.filtering_fields), expected_fields) # type: ignore

    def test_new_fields_in_filtering_fields(self):
        class NewFieldsModel(StandardModel):
            a_str: str
            an_int : int
            a_date : datetime

        # Inherited ID included
        self.assertIn("id", NewFieldsModel._meta.filtering_fields) # type: ignore
        # New fields included
        self.assertIn("a_str", NewFieldsModel._meta.filtering_fields) # type: ignore
        self.assertIn("an_int", NewFieldsModel._meta.filtering_fields) # type: ignore
        self.assertIn("a_date", NewFieldsModel._meta.filtering_fields) # type: ignore

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

        fields = DisabledFieldsModel._meta.filtering_fields  # type: ignore

        # Inherited ID included
        self.assertIn("id", fields)
        # Disabled field excluded
        self.assertNotIn("a_str_no", fields)
        self.assertNotIn("an_int_no", fields)
        self.assertNotIn("a_date_no", fields)
        # Enabled field included
        self.assertIn("a_str_yes", fields)
        self.assertIn("an_int_yes", fields)
        self.assertIn("a_date_yes", fields)

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

        fields = ReadOnlyFieldsModel._meta.filtering_fields  # type: ignore

        # Inherited ID included
        self.assertIn("id", fields)
        # All fields included
        self.assertIn("a_str_no", fields)
        self.assertIn("an_int_no", fields)
        self.assertIn("a_date_no", fields)
        self.assertIn("a_str_yes", fields)
        self.assertIn("an_int_yes", fields)
        self.assertIn("a_date_yes", fields)

    def test_can_disable_inherited(self):
        class DisabledInheritedModel(StandardModel):
            a_str: str
            an_int : int
            a_date : datetime

            class Meta(StandardModel.Meta):
                filtering_disabled = {"id"}

        fields = DisabledInheritedModel._meta.filtering_fields  # type: ignore

        # Inherited ID excluded
        self.assertNotIn("id", fields)
        # New fields included
        self.assertIn("a_str", fields)
        self.assertIn("an_int", fields)
        self.assertIn("a_date", fields)

class TestFilters(UnitTestCase):
    @override
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

class TestDirtyFields(TestBase):
    @override
    def setUp(self):
        super().setUp()
        self.model = ExampleModel.from_dict(self.model_data_parsed)

    def test_dirty_fields_str(self):
        self.assertFalse(self.model.is_dirty(), "Test preconditions failed")
        original_str = self.model.a_str

        # Test if the dirty fields are correctly tracked
        self.model.a_str = "Updated String"
        self.assertTrue(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {"a_str": (original_str, "Updated String")})
        self.model.a_str = original_str
        self.assertFalse(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {})

    def test_dirty_fields_int(self):
        original_int = self.model.an_int
        self.model.an_int = 100
        self.assertTrue(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {"an_int": (original_int, 100)})
        self.model.an_int = original_int
        self.assertFalse(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {})

    def test_dirty_fields_bool(self):
        self.model.a_bool = False
        self.assertTrue(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {"a_bool": (True, False)})
        self.model.a_bool = True
        self.assertEqual(self.model.dirty_fields(), {})
        self.assertFalse(self.model.is_dirty())

    def test_dirty_fields_date(self):
        original_date = self.model.a_date
        new_date = datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.model.a_date = new_date
        self.assertTrue(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {"a_date": ('2020-05-12T12:00:00+00:00', '2021-01-01T00:00:00+00:00')})
        self.model.a_date = original_date
        self.assertFalse(self.model.is_dirty())
        self.assertEqual(self.model.dirty_fields(), {})

    def test_dirty_fields_instancevar(self):
        model1 = ExampleModel.from_dict(self.model_data_parsed)
        model2 = ExampleModel.from_dict(self.model_data_parsed)
        self.assertFalse(model1.is_dirty())
        self.assertFalse(model2.is_dirty())
        model1.a_str = "Updated String"
        self.assertTrue(model1.is_dirty())
        self.assertFalse(model2.is_dirty())
        self.assertEqual(model1.dirty_fields(), {"a_str": (self.model_data_parsed["a_str"], "Updated String")})
        self.assertEqual(model2.dirty_fields(), {})
        model2.a_str = "Something Else"
        self.assertTrue(model1.is_dirty())
        self.assertTrue(model2.is_dirty())
        self.assertEqual(model1.dirty_fields(), {"a_str": (self.model_data_parsed["a_str"], "Updated String")})
        self.assertEqual(model2.dirty_fields(), {"a_str": (self.model_data_parsed["a_str"], "Something Else")})
        model3 = ExampleModel.from_dict(self.model_data_parsed)
        self.assertFalse(model3.is_dirty())
        self.assertEqual(model3.dirty_fields(), {})
        self.assertTrue(model1.is_dirty())
        self.assertTrue(model2.is_dirty())
        self.assertEqual(model1.dirty_fields(), {"a_str": (self.model_data_parsed["a_str"], "Updated String")})
        self.assertEqual(model2.dirty_fields(), {"a_str": (self.model_data_parsed["a_str"], "Something Else")})


if __name__ == "__main__":
    unittest.main()
