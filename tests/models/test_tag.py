"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    test_tag.py                                                                                          *
*        Project: models                                                                                               *
*        Created: 2025-03-03                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-03     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""
from typing import Iterable
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from paperap.models.tag import Tag
from paperap.client import PaperlessClient
from paperap.resources.tags import TagResource
from paperap.tests import TestCase, load_sample_data

# Load sample response from tests/sample_data/tags_list.json
sample_data = load_sample_data('tags_list.json')

class TestTagInit(unittest.TestCase):

    def setUp(self):
        # Setup a sample model instance
        self.client = PaperlessClient()
        self.resource = self.client.tags
        self.model_data = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
            "name": "Test Tag",
            "slug": "test-tag",
            "color": "blue",
            "match": "test",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "is_inbox_tag": True,
        }

    def test_from_dict(self):
        model = Tag.from_dict(self.model_data, self.resource)
        self.assertIsInstance(model, Tag, f"Expected Tag, got {type(model)}")
        self.assertEqual(model.id, self.model_data["id"], f"Tag id is wrong when created from dict: {model.id}")
        self.assertIsInstance(model.created, datetime, f"created wrong type after from_dict {type(model.created)}")
        self.assertIsInstance(model.updated, datetime, f"updated wrong type after from_dict {type(model.updated)}")
        self.assertEqual(model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc), f"created wrong value after from_dict {model.created}")
        self.assertEqual(model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc), f"updated wrong value after from_dict {model.updated}")
        self.assertEqual(model.name, self.model_data["name"], f"Tag name is wrong when created from dict: {model.name}")
        self.assertEqual(model.slug, self.model_data["slug"], f"Tag slug is wrong when created from dict: {model.slug}")
        self.assertEqual(model.color, self.model_data["color"], f"Tag color is wrong when created from dict: {model.color}")
        self.assertEqual(model.match, self.model_data["match"], f"Tag match is wrong when created from dict: {model.match}")
        self.assertEqual(model.matching_algorithm, self.model_data["matching_algorithm"], f"Tag matching_algorithm is wrong when created from dict: {model.matching_algorithm}")
        self.assertEqual(model.is_insensitive, self.model_data["is_insensitive"], f"Tag is_insensitive is wrong when created from dict: {model.is_insensitive}")
        self.assertEqual(model.is_inbox_tag, self.model_data["is_inbox_tag"], f"Tag is_inbox_tag is wrong when created from dict: {model.is_inbox_tag}")

class TestTag(unittest.TestCase):
    def setUp(self):
        # Setup a sample model instance
        self.client = PaperlessClient()
        self.resource = self.client.tags
        self.model_data = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
            "name": "Test Tag",
            "slug": "test-tag",
            "color": "blue",
            "match": "test",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "is_inbox_tag": True,
        }
        self.model = Tag.from_dict(self.model_data, self.resource)

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.created, datetime, f"created wrong type after from_dict {type(self.model.created)}")
        self.assertIsInstance(self.model.updated, datetime, f"updated wrong type after from_dict {type(self.model.updated)}")

        # TZ UTC
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(self.model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.name, self.model_data["name"])

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.matching_algorithm, self.model_data["matching_algorithm"])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["created_on"], datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(model_dict["updated_on"], datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(model_dict["name"], self.model_data["name"])
        self.assertEqual(model_dict["slug"], self.model_data["slug"])
        self.assertEqual(model_dict["color"], self.model_data["color"])
        self.assertEqual(model_dict["match"], self.model_data["match"])
        self.assertEqual(model_dict["matching_algorithm"], self.model_data["matching_algorithm"])
        self.assertEqual(model_dict["is_insensitive"], self.model_data["is_insensitive"])
        self.assertEqual(model_dict["is_inbox_tag"], self.model_data["is_inbox_tag"])

if __name__ == "__main__":
    unittest.main()
