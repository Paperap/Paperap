"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_tags.py
        Project: paperap
        Created: 2025-03-05
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-05     By Jess Mann

"""
from __future__ import annotations

import os
from typing import Iterable
from unittest.mock import patch, MagicMock
from datetime import datetime
from paperap.models import *
from paperap.resources.tags import TagResource
from paperap.models.document import DocumentQuerySet
from paperap.tests import TestCase, load_sample_data, TagTest

sample_tag_list = load_sample_data('tags_list.json')
sample_tag = load_sample_data('tags_item.json')

class TestTagsInit(TagTest):

    def setup_model_data(self):
        self.model_data = {
            "id": 1,
            "name": "Test Tag",
            "slug": "test-tag",
            "colour": "#ff0000",
            "match": "test",
            "matching_algorithm": 1,
            "is_insensitive": False,
            "is_inbox_tag": False,
            "document_count": 1,
            "owner": 1,
            "user_can_change": False
        }

    def test_from_dict(self):
        model = Tag.from_dict(self.model_data, self.resource)
        fields = {
            "id": int,
            "name": str,
            "slug": str,
            "colour": str,
            "match": str,
            "matching_algorithm": int,
            "is_insensitive": bool,
            "is_inbox_tag": bool,
            "document_count": int,
            "owner": int,
            "user_can_change": bool
        }
        for field, field_type in fields.items():
            value = getattr(model, field)
            self.assertIsInstance(value, field_type, f"Expected {field} to be a {field_type}, got {type(value)}")
            self.assertEqual(value, self.model_data[field], f"Expected {field} to match sample data")

class TestTag(TagTest):

    def setup_model_data(self):
        self.model_data = {
            "id": 1,
            "name": "Test Tag",
            "slug": "test-tag",
            "colour": "#ff0000",
            "match": "test",
            "matching_algorithm": 1,
            "is_insensitive": False,
            "is_inbox_tag": False,
            "document_count": 1,
            "owner": 1,
            "user_can_change": False
        }

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.name, "Test Tag")
        self.assertEqual(self.model.slug, "test-tag")
        self.assertEqual(self.model.colour, "#ff0000")
        self.assertEqual(self.model.match, "test")

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.matching_algorithm, 1)
        self.assertEqual(self.model.document_count, 1)
        self.assertEqual(self.model.owner, 1)

    def test_model_bool_parsing(self):
        # Test if boolean fields are parsed correctly
        self.assertFalse(self.model.is_insensitive)
        self.assertFalse(self.model.is_inbox_tag)
        self.assertFalse(self.model.user_can_change)

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()
        fields = {
            "id": int,
            "name": str,
            "slug": str,
            "colour": str,
            "match": str,
            "matching_algorithm": int,
            "is_insensitive": bool,
            "is_inbox_tag": bool,
            "document_count": int,
            "owner": int,
            "user_can_change": bool
        }
        for field, field_type in fields.items():
            value = model_dict[field]
            self.assertIsInstance(value, field_type, f"Expected {field} to be a {field_type}, got {type(value)}")
            self.assertEqual(value, self.model_data[field], f"Expected {field} to match sample data")

class TestRelationships(TagTest):

    def setup_model_data(self):
        self.model_data = {
            "id": 1337,
            "name": "Test Tag",
            "slug": "test-tag",
            "colour": "#ff0000",
            "match": "test",
            "matching_algorithm": 1,
            "is_insensitive": False,
            "is_inbox_tag": False,
            "document_count": 1,
            "owner": 1,
            "user_can_change": False
        }

    def test_get_documents(self):
        sample_data = load_sample_data('documents_list_id__in_6342,6332,1244.json')
        expected_count = 3
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            documents = self.model.documents
            self.assertIsInstance(documents, DocumentQuerySet)
            actual_count = documents.count()
            self.assertEqual(expected_count, actual_count, f"Expected {expected_count} documents, got {actual_count}")

            count = 0
            for i, document in enumerate(documents):
                count += 1
                fields = {
                    "id": int,
                    "title": str,
                    "storage_path": int,
                    "correspondent": int,
                    "document_type": int,
                    "created": datetime,
                    "tags": list
                }
                for field, field_type in fields.items():
                    value = getattr(document, field)
                    self.assertIsInstance(value, field_type, f"Expected document.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_data["results"][i][field], f"Expected document.{field} to match sample data")

                self.assertTrue(self.model.id in document.tags, f"Expected tag.id to be in document.tags. {self.model.id} not in {document.tags}")

            self.assertEqual(count, expected_count, f"Expected to iterate over {expected_count} documents, only saw {count}")
