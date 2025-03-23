

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable, override
from unittest.mock import MagicMock, patch

from paperap.models import *
from paperap.models.document import DocumentQuerySet
from paperap.resources.tags import TagResource
from tests.lib import TagUnitTest, UnitTestCase, load_sample_data

sample_tag_list = load_sample_data('tags_list.json')
sample_tag = load_sample_data('tags_item.json')

class TestTagsInit(TagUnitTest):

    @override
    def setup_model_data(self):
        self.model_data_parsed = {
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
        model = Tag.from_dict(self.model_data_parsed)
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
            self.assertEqual(value, self.model_data_parsed[field], f"Expected {field} to match sample data")

class TestTag(TagUnitTest):

    @override
    def setup_model_data(self):
        self.model_data_unparsed = {
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
            self.assertEqual(value, self.model_data_unparsed[field], f"Expected {field} to match sample data")

class TestRelationships(TagUnitTest):

    @override
    def setup_model_data(self):
        self.model_data_unparsed = {
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
                sample_document = sample_data["results"][i]
                fields = {
                    "id": int,
                    "title": str,
                }
                for field, field_type in fields.items():
                    value = getattr(document, field)
                    self.assertIsInstance(value, field_type, f"Expected document.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_document[field], f"Expected document.{field} to match sample data")

                self.assertIsInstance(document.tag_ids, list)
                self.assertTrue(self.model.id in document.tag_ids, f"Expected tag.id to be in document.tag_ids. {self.model.id} not in {document.tag_ids}")
                self.assertCountEqual(document.tag_ids, sample_document['tags'], "Expected document.tag_ids to match sample data")

                if sample_document['storage_path'] is None:
                    self.assertIsNone(document.storage_path_id)
                else:
                    self.assertIsInstance(document.storage_path_id, int)
                    self.assertEqual(document.storage_path_id, sample_document['storage_path'])

                if sample_document['correspondent'] is None:
                    self.assertIsNone(document.correspondent_id)
                else:
                    self.assertIsInstance(document.correspondent_id, int)
                    self.assertEqual(document.correspondent_id, sample_document['correspondent'])

                if sample_document['document_type'] is None:
                    self.assertIsNone(document.document_type_id)
                else:
                    self.assertIsInstance(document.document_type_id, int)
                    self.assertEqual(document.document_type_id, sample_document['document_type'])

            self.assertEqual(count, expected_count, f"Expected to iterate over {expected_count} documents, only saw {count}")
