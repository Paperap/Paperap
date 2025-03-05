"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
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
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.document import Document
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag
from paperap.tests import TestCase, load_sample_data

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class DocumentTestCase(TestCase):
    def setUp(self):
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
            self.client = PaperlessClient()

class TestDocumentInit(DocumentTestCase):
    def setUp(self):
        super().setUp()
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
        self.assertIsInstance(model, Document, f"Expected Document, got {type(model)}")
        self.assertEqual(model.id, self.model_data["id"], f"Document id is wrong when created from dict: {model.id}")
        self.assertEqual(model.title, self.model_data["title"], f"Document title is wrong when created from dict: {model.title}")
        self.assertEqual(model.correspondent, self.model_data["correspondent"], f"Document correspondent is wrong when created from dict: {model.correspondent}")
        self.assertEqual(model.document_type, self.model_data["document_type"], f"Document document_type is wrong when created from dict: {model.document_type}")
        self.assertIsInstance(model.tags, Iterable, f"Document tags is wrong type when created from dict: {type(model.tags)}")
        self.assertEqual(model.tags, self.model_data["tags"], f"Document tags is wrong when created from dict: {model.tags}")
        self.assertIsInstance(model.created, datetime, f"created wrong type after from_dict {type(model.created)}")
        self.assertIsInstance(model.updated, datetime, f"updated wrong type after from_dict {type(model.updated)}")
        self.assertEqual(model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc), f"created wrong value after from_dict {model.created}")
        self.assertEqual(model.updated, datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc), f"updated wrong value after from_dict {model.updated}")

class TestDocument(DocumentTestCase):
    def setUp(self):
        super().setUp()
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

        self.assertEqual(model_dict["created"], datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(model_dict["updated"], datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(model_dict["title"], "Test Document")
        self.assertEqual(model_dict["correspondent"], 1)
        self.assertEqual(model_dict["document_type"], 1)
        self.assertEqual(model_dict["tags"], [1, 2, 3])

class TestGetTags(TestCase):
    def setUp(self):
        super().setUp()
        super().setUp()
        # Setup a sample model instance
        self.documents = self.client.documents()

    def setup_client(self):
        self.client = PaperlessClient()

    """
    # Working test when connected to a real server. Needs proper mocking for the request.
    def test_get_tags(self):
        for document in self.documents:
            self.assertIsInstance(document, Document, f"Expected Document, got {type(document)}")
            tags = document.get_tags()
            self.assertIsInstance(tags, QuerySet)
            expected_count = len(document.tags)
            actual_count = tags.count()
            self.assertEqual(expected_count, actual_count, f"Expected {expected_count} tags, got {actual_count}")

            count = 0
            for tag in tags:
                count += 1
                self.assertIsInstance(tag, Tag, f"Expected document.tag to be a Tag, got {type(tag)}")
                self.assertTrue(tag.id in document.tags, f"Expected tag.id to be in document.tags. {tag.id} not in {document.tags}")
                self.assertIsInstance(tag.name, str, f"Expected tag.name to be a string, got {type(tag.name)}")

            self.assertEqual(count, expected_count, f"Expected to iterate over {expected_count} tags, only saw {count}")
        """

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
            self.assertIsInstance(document.id, int, "Loading sample document, id wrong type")
            self.assertIsInstance(document.title, str, "Loading sample document, title wrong type")
            self.assertIsInstance(document.storage_path, str if sample_document["storage_path"] else type(None), "Loading sample document, storage_path wrong type")
            self.assertIsInstance(document.correspondent, int if sample_document["correspondent"] is not None else type(None), "Loading sample document, correspondent wrong type")
            self.assertIsInstance(document.document_type, int if sample_document["document_type"] is not None else type(None), "Loading sample document, document_type wrong type")
            self.assertIsInstance(document.created, datetime, "Loading sample document created wrong type")
            self.assertIsInstance(document.updated, datetime, "Loading sample document updated wrong type")
            self.assertIsInstance(document.tags, list, "Loading sample document, tags wrong type")
            self.assertEqual(document.id, sample_document["id"], "Loading sample document id mismatch")
            self.assertEqual(document.title, sample_document["title"], "Loading sample document title mismatch")
            self.assertEqual(document.storage_path, sample_document["storage_path"], "Loading sample document storage_path mismatch")
            self.assertEqual(document.correspondent, sample_document["correspondent"], "Loading sample document correspondent mismatch")
            self.assertEqual(document.document_type, sample_document["document_type"], "Loading sample document document_type mismatch")
            self.assertEqual(document.tags, sample_document["tags"], "Loading sample document tags mismatch")

    """
    # Working test when connected to a real server. Needs proper mocking for the request.
    def test_get_tags(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document
            document = self.client.documents().get(1)

        tags = document.get_tags()
        self.assertIsInstance(tags, QuerySet)
        for tag in tags:
            self.assertIsInstance(tag, Tag, f"Expected document.tag to be a Tag, got {type(tag)}")
            self.assertTrue(tag.id in document.tags, "Expected tag.id to be in document.tags")
            self.assertIsInstance(tag.name, str, f"Expected tag.name to be a string, got {type(tag.name)}")
    """

if __name__ == "__main__":
    unittest.main()
