"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    test_base.py                                                                                         *
*        Project: models                                                                                               *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""
import unittest
from datetime import datetime, timezone
from paperap.models import PaperlessModel
from paperap.client import PaperlessClient
from paperap.resources.base import PaperlessResource

class ExampleModel(PaperlessModel):
    """
    Example model for testing purposes.
    """
    a_str : str
    a_date : datetime
    an_int : int
    a_float : float
    a_bool : bool

class ExampleResource(PaperlessResource):
    """
    Example resource for testing purposes.
    """
    name = "example"
    model_class = ExampleModel

class TestModel(unittest.TestCase):
    def setUp(self):
        # Setup a sample model instance
        self.client = PaperlessClient()
        self.resource = ExampleResource(self.client)
        self.model_data = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
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
        self.assertIsInstance(self.model.created, datetime)
        self.assertIsInstance(self.model.updated, datetime)
        self.assertIsInstance(self.model.a_date, datetime)

        # TZ UTC
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(self.model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(self.model.a_date, datetime(2020, 5, 12, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["id"], self.model_data["id"])
        self.assertEqual(model_dict["a_str"], self.model_data["a_str"])
        self.assertEqual(model_dict["an_int"], self.model_data["an_int"])
        self.assertEqual(model_dict["a_float"], self.model_data["a_float"])
        self.assertEqual(model_dict["a_bool"], self.model_data["a_bool"])

        self.assertEqual(model_dict["created_on"], datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(model_dict["updated_on"], datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))
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

if __name__ == "__main__":
    unittest.main()
