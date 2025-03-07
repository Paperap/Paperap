"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
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
from typing import Iterable
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models import *
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag, TagQuerySet
from paperap.tests import TestCase, load_sample_data

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class DocumentTestCase(TestCase):
    mock_env = True

class TestDocumentInit(DocumentTestCase):
    def setUp(self):
        super().setUp()
        # Setup a sample model instance
        self.resource = self.client.documents
        self.model_data = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
            "title": "Test Document",
            "correspondent": 1,
            "document_type": 1,
            "tags": [1, 2, 3],
        }

    def test_from_dict(self):
        model = Document.from_dict(self.model_data, self.resource)
        fields = {
            "id": int,
            "title": str,
            "correspondent": int,
            "document_type": int,
            "tags": list
        }
        for field, field_type in fields.items():
            value = getattr(model, field)
            self.assertIsInstance(value, field_type, f"Expected {field} to be a {field_type}, got {type(value)}")
            self.assertEqual(value, self.model_data[field], f"Expected {field} to match sample data")
        self.assertIsInstance(model.created, datetime, f"created wrong type after from_dict {type(model.created)}")
        self.assertIsInstance(model.updated, datetime, f"updated wrong type after from_dict {type(model.updated)}")
        self.assertEqual(model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc), f"created wrong value after from_dict {model.created}")
        self.assertEqual(model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc), f"updated wrong value after from_dict {model.updated}")

class TestDocument(DocumentTestCase):
    def setUp(self):
        super().setUp()
        # Setup a sample model instance
        self.resource = self.client.documents
        self.model_data = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
            "title": "Test Document",
            "correspondent": 1,
            "document_type": 1,
            "tags": [1, 2, 3],
        }
        self.model = Document.from_dict(self.model_data, self.resource)

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.created, datetime, f"created wrong type after from_dict {type(self.model.created)}")
        self.assertIsInstance(self.model.updated, datetime, f"updated wrong type after from_dict {type(self.model.updated)}")

        # TZ UTC
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(self.model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.title, "Test Document")

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.correspondent, 1)
        self.assertEqual(self.model.document_type, 1)

    def test_model_list_parsing(self):
        # Test if list fields are parsed correctly
        self.assertIsInstance(self.model.tags, Iterable)
        self.assertEqual(self.model.tags, [1, 2, 3])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["created"], '2025-03-01T12:00:00+00:00')
        self.assertEqual(model_dict['updated'], '2025-03-02T12:00:00+00:00')
        self.assertEqual(model_dict["title"], "Test Document")
        self.assertEqual(model_dict["correspondent"], 1)
        self.assertEqual(model_dict["document_type"], 1)
        self.assertEqual(model_dict["tags"], [1, 2, 3])

class TestGetRelationships(TestCase):
    def setUp(self):
        super().setUp()
        # Setup a sample model instance
        sample_document = load_sample_data('documents_item.json')
        self.resource = DocumentResource(self.client)
        self.document = Document.from_dict(sample_document, self.resource)

    def setup_client(self):
        self.client = PaperlessClient()

    def test_get_tags(self):
        sample_data = load_sample_data('tags_list_id__in_38,162,160,191.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            expected_count = len(self.document.tags)
            tags = self.document.get_tags()
            self.assertIsInstance(tags, TagQuerySet)
            actual_count = tags.count()
            self.assertEqual(expected_count, actual_count, f"Expected {expected_count} tags, got {actual_count}")

            count = 0
            for tag in tags:
                count += 1
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
                    value = getattr(tag, field)
                    self.assertIsInstance(value, field_type, f"Expected tag.{field} to be a {field_type}, got {type(value)}")
                    
                self.assertGreater(tag.document_count, 0, f"Expected tag.document_count to be greater than 0, got {tag.document_count}")
                self.assertTrue(tag.id in self.document.tags, f"Expected tag.id to be in document.tags. {tag.id} not in {self.document.tags}")                

            self.assertEqual(count, expected_count, f"Expected to iterate over {expected_count} tags, only saw {count}")

    def test_get_correspondent(self):
        sample_data = load_sample_data('correspondents_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.document.correspondent = sample_data["id"]
            correspondent = self.document.get_correspondent()
            self.assertIsInstance(correspondent, Correspondent, f"Expected document.correspondent to be a Correspondent, got {type(correspondent)}")
            # Make mypy happy
            assert correspondent is not None
            fields = {
                "id": int,
                "slug": str,
                "name": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(correspondent, field)
                if sample_data[field] is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsInstance(value, field_type, f"Expected correspondent.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_data[field], f"Expected correspondent.{field} to match sample data")
                
    def test_get_document_type(self):
        sample_data = load_sample_data('document_types_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.document.document_type = sample_data["id"]
            document_type = self.document.get_document_type()
            self.assertIsInstance(document_type, DocumentType, f"Expected document.document_type to be a DocumentType, got {type(document_type)}")
            # Make mypy happy
            assert document_type is not None
            fields = {
                "id": int,
                "name": str,
                "slug": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(document_type, field)
                if sample_data[field] is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsInstance(value, field_type, f"Expected document_type.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_data[field], f"Expected document_type.{field} to match sample data")
            

    def test_get_storage_path(self):
        sample_data = load_sample_data('storage_paths_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.document.storage_path = sample_data["id"]
            storage_path = self.document.get_storage_path()
            self.assertIsInstance(storage_path, StoragePath, f"Expected document.storage_path to be a StoragePath, got {type(storage_path)}")
            # Make mypy happy
            assert storage_path is not None
            fields = {
                "id": int,
                "name": str,
                "slug": str,
                "path": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(storage_path, field)
                self.assertIsInstance(value, field_type, f"Expected storage_path.{field} to be a {field_type}, got {type(value)}")
                self.assertEqual(value, sample_data[field], f"Expected storage_path.{field} to match sample data")
                
class TestRequestDocumentList(DocumentTestCase):
    def test_get_documents(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document_list
            documents = self.client.documents()
            self.assertIsInstance(documents, QuerySet)
            total = documents.count()
            expected = sample_document_list["count"]
            self.assertEqual(total, expected, f"Expected {expected} documents, got {total}")

class TestRequestDocument(TestCase):

    def setup_client(self):
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
            self.client = PaperlessClient()

    def test_get_document(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document
            document = self.get_resource(DocumentResource, 7313)
            self.assertIsInstance(document, Document)
            fields = {
                "id": int,
                "title": str,
                "storage_path": int,
                "correspondent": int,
                "document_type": int,
                #"created": datetime,
                #"updated": datetime,
                "tags": list
            }
            for field, field_type in fields.items():
                value = getattr(document, field)
                if sample_document[field] is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsInstance(value, field_type, f"Expected document.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_document[field], f"Expected document.{field} to match sample data")

class TestCustomFieldAccess(TestCase):

    def setUp(self):
        super().setUp()
        self.custom_fields = [
            {"field": 1, "value": "Test Value 1"},
            {"field": 2, "value": "Test Value 2"},
            {"field": 53, "value": "Test Value 53"},
            {"field": 54, "value": 54},
            {"field": 55, "value": 55.50},
            {"field": 56, "value": True},
            {"field": 57, "value": False},
            {"field": 58, "value": None},
        ]
        self.resource = DocumentResource(self.client)
        self.document = Document.from_dict({
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "updated": "2025-03-02T12:00:00Z",
            "title": "Test Document",
            "correspondent": 1,
            "document_type": 1,
            "tags": [1, 2, 3],
            "custom_fields": self.custom_fields
        }, self.resource)

    def test_custom_field_success(self):
        for field in self.custom_fields:
            field_id = field["field"]
            expected = field["value"]
            actual = self.document.custom_field(field_id)
            self.assertEqual(expected, actual, f"Expected {expected}, got {actual} of type {type(actual)}")

    def test_custom_field_default(self):
        default = "Default Value"
        actual = self.document.custom_field(3, default=default)
        self.assertEqual(default, actual, f"Expected {default}, got {actual} of type {type(actual)}")

    def test_custom_field_raises(self):
        with self.assertRaises(ValueError):
            self.document.custom_field(3, raise_errors=True)
        with self.assertRaises(ValueError):
            self.document.custom_field(3, default="Some Default", raise_errors=True)
        
if __name__ == "__main__":
    unittest.main()
