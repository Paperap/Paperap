"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_tag.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.1
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations
import os
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
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
            self.client = PaperlessClient()
        self.resource = self.client.tags
        self.model_data = {
            "id": 1,
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
        self.assertEqual(model.name, self.model_data["name"], f"Tag name is wrong when created from dict: {model.name}")
        self.assertEqual(model.slug, self.model_data["slug"], f"Tag slug is wrong when created from dict: {model.slug}")
        self.assertEqual(model.colour, self.model_data["color"], f"Tag color is wrong when created from dict: {model.colour}")
        self.assertEqual(model.match, self.model_data["match"], f"Tag match is wrong when created from dict: {model.match}")
        self.assertEqual(model.matching_algorithm, self.model_data["matching_algorithm"], f"Tag matching_algorithm is wrong when created from dict: {model.matching_algorithm}")
        self.assertEqual(model.is_insensitive, self.model_data["is_insensitive"], f"Tag is_insensitive is wrong when created from dict: {model.is_insensitive}")
        self.assertEqual(model.is_inbox_tag, self.model_data["is_inbox_tag"], f"Tag is_inbox_tag is wrong when created from dict: {model.is_inbox_tag}")

class TestTag(unittest.TestCase):
    def setUp(self):
        # Setup a sample model instance
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
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

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.name, self.model_data["name"])

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.matching_algorithm, self.model_data["matching_algorithm"])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["name"], self.model_data["name"])
        self.assertEqual(model_dict["slug"], self.model_data["slug"])
        self.assertEqual(model_dict["colour"], self.model_data["color"])
        self.assertEqual(model_dict["match"], self.model_data["match"])
        self.assertEqual(model_dict["matching_algorithm"], self.model_data["matching_algorithm"])
        self.assertEqual(model_dict["is_insensitive"], self.model_data["is_insensitive"])
        self.assertEqual(model_dict["is_inbox_tag"], self.model_data["is_inbox_tag"])

if __name__ == "__main__":
    unittest.main()
