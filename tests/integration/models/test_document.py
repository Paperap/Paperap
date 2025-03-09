"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
        Project: paperap
        Created: 2025-03-08
        Version: 0.0.4
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-08     By Jess Mann

"""
from __future__ import annotations

import os
from typing import Iterable
import unittest
from unittest.mock import patch, MagicMock
import logging
from datetime import datetime, timezone
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models import *
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag, TagQuerySet
from paperap.tests import load_sample_data, DocumentTest

logger = logging.getLogger(__name__)

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class IntegrationTest(DocumentTest):
    mock_env = False

    def setUp(self):
        super().setUp()
        self.model = self.client.documents().get(7411)
        self._initial_data = self.model.to_dict()

    def tearDown(self):
        # Request that paperless ngx reverts to the previous data
        self.model.update(**self._initial_data)

        # TODO: confirm without another query
        return super().tearDown()

class TestIntegrationTest(IntegrationTest):
    def test_integration(self):
        # Test if the document can be retrieved
        self.assertIsInstance(self.model, Document)
        self.assertEqual(self.model.id, 7411, "Document ID does not match expected value. Cannot run test")

        # Test if the document can be updated
        self.model.title = "Updated Test Document"
        self.model.save()
        self.assertEqual(self.model.title, "Updated Test Document", "Document title did not update as expected. Cannot test IntegrationTest class")

        # Manually call tearDown
        self.tearDown()

        # Retrieve the document again
        document = self.client.documents().get(7411)
        for field, value in self._initial_data.items():
            # Test notes individually
            # Temporarily skip dates (TODO)
            if field in ['added', 'created', 'updated', 'notes']:
                continue
            retrieved_value = getattr(document, field)
            self.assertEqual(retrieved_value, value, f"Field {field} did not revert to initial value on teardown. Integration tests will fail")

        self.assertEqual(len(document.notes), len(self._initial_data['notes']), "Note count did not revert to initial value on teardown. Integration tests will fail")
        for note in self._initial_data['notes']:
            self.assertTrue(self._has_note(document, note), "Note did not revert to initial value on teardown. Integration tests will fail")

    def _has_note(self, document : Document, note : dict):
        for doc_note in document.notes:
            if doc_note.matches_dict(note):
                return True
        return False

class TestSaveManual(IntegrationTest):
    def setup_model(self):
        super().setup_model()
        self.model._meta.save_on_write = False

    def test_save(self):
        # Append a bunch of random gibberish
        new_title = "Test Document " + str(datetime.now().timestamp())
        self.assertNotEqual(new_title, self.model.title, "Test assumptions are not true")
        self.model.title = new_title
        self.assertEqual(new_title, self.model.title, "Title not updated in local instance")
        self.assertEqual(self.model.id, 7411, "ID changed after update")
        self.model.save()
        self.assertEqual(new_title, self.model.title, "Title not updated after save")
        self.assertEqual(self.model.id, 7411, "ID changed after save")

        # Retrieve the document again
        document = self.client.documents().get(7411)
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

    def test_save_on_write_off(self):
        # Test that the document is not saved when a field is written to
        new_title = "Test Document " + str(datetime.now().timestamp())
        self.assertNotEqual(new_title, self.model.title, "Test assumptions are not true")
        self.model.title = new_title
        self.assertEqual(new_title, self.model.title, "Title not updated in local instance")

        # Retrieve the document again
        document = self.client.documents().get(7411)
        self.assertNotEqual(new_title, document.title, "Title updated in remote instance without calling write")

    def test_save_all_fields(self):
        #(field_name, [values_to_set])
        ts = datetime.now().timestamp()
        fields = [
            ("title", [f"Test Document {ts}"]),
            ("correspondent", [21, 37, None]),
            ("document_type", [10, 16, None]),
            ("tags", [[74], [254], [45, 80], [74, 254, 45]]),
        ]
        for field, values in fields:
            for value in values:
                current = getattr(self.model, field)
                setattr(self.model, field, value)
                if field == "tags":
                    self.assertCountEqual(value, self.model.tags, f"{field} not updated in local instance. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance. Previous value {current}")
                self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")
                self.model.save()
                if field == "tags":
                    self.assertCountEqual(value, self.model.tags, f"{field} not updated after save. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save. Previous value {current}")
                self.assertEqual(self.model.id, 7411, "ID changed after save")

                # Get a new copy
                document = self.client.documents().get(7411)
                if field == "tags":
                    self.assertCountEqual(value, document.tags, f"{field} not updated in remote instance. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance. Previous value {current}")

    def test_update_one_field(self):
        # Test that the document is saved when a field is written to
        new_title = "Test Document " + str(datetime.now().timestamp())
        self.assertNotEqual(new_title, self.model.title, "Test assumptions are not true")
        self.model.update(title=new_title)
        self.assertEqual(new_title, self.model.title, "Title not updated in local instance")

        # Retrieve the document again
        document = self.client.documents().get(7411)
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

    def test_update_all_fields(self):
        #(field_name, [values_to_set])
        ts = datetime.now().timestamp()
        fields = {
            "title": f"Test Document {ts}",
            "correspondent": 21,
            "document_type": 10,
            "tags": [38],
        }
        self.model.update(**fields)
        for field, value in fields.items():
            self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
            self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")

class TestSaveNone(IntegrationTest):
    def setUp(self):
        super().setUp()
        self.model._meta.save_on_write = False

        if not self.model.tags:
            self.model.tag_ids = [38]
            self.model.save()

        self.none_data = {
            "archive_serial_number": None,
            "content": "",
            "correspondent": None,
            "custom_fields": [],
            "deleted_at": None,
            "document_type": None,
            #"notes": [],
            "page_count": None,
            "storage_path": None,
            "tags": [],
            "title": "",
        }

        self.expected_data = {
            "archive_serial_number": 123456,
            "content": "Test Content",
            "correspondent": 31,
            "custom_fields": [{"field": 32, "value": "Test Value"}],
            "document_type": 16,
            "tags": [28],
            "title": "Test Document",
            #"notes": ["Test Note"],
            "storage_path": 1,
        }

    def test_update_tags_to_none(self):
        # Test that the document is saved when a field is written to
        self.model.update(tags=None)
        document = self.client.documents().get(7411)
        self.assertEqual([], document.tags, "Tags not cleared in remote instance when updated to None")

    def test_update_tags_to_empty(self):
        # Test that the document is saved when a field is written to
        self.model.update(tags=[])
        document = self.client.documents().get(7411)
        self.assertEqual([], document.tags, "Tags not cleared in remote instance when updated to empty list")

    def test_set_tags_to_none(self):
        # Test that the document is saved when a field is written to
        self.model.tag_ids = []
        self.model.save()
        document = self.client.documents().get(7411)
        self.assertEqual([], document.tags, "Tags not cleared in remote instance when set to empty list")

    def test_set_fields(self):
        # Ensure fields can be set and reset without consequences
        self.model.update(**self.expected_data)
        document = self.client.documents().get(7411)
        for field, value in self.expected_data.items():
            if field == "tags":
                self.assertCountEqual(value, self.model.tags, f"{field} not updated in local instance on first set to expected")
                self.assertCountEqual(value, document.tags, f"{field} not updated in remote instance on first set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on first set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on first set to expected")

        none_data = {k: None for k in self.none_data.keys()}
        self.model.update(**none_data)
        document = self.client.documents().get(7411)
        for field, value in self.none_data.items():
            if field == "tags":
                self.assertCountEqual(value, self.model.tags, f"{field} not updated in local instance on set to None")
                self.assertCountEqual(value, document.tags, f"{field} not updated in remote instance on set to None")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on set to None")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on set to None")

        self.model.update(**self.expected_data)
        document = self.client.documents().get(7411)
        for field, value in self.expected_data.items():
            if field == "tags":
                self.assertCountEqual(value, self.model.tags, f"{field} not updated in local instance on second set to expected")
                self.assertCountEqual(value, document.tags, f"{field} not updated in remote instance on second set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on second set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on second set to expected")

    def test_set_fields_to_none(self):
        # field_name -> expected value after being set to None
        for field, value in self.none_data.items():
            with self.subTest(field=field):
                setattr(self.model, field, None)
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
                self.model.save()
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save")

                # Get a new copy
                document = self.client.documents().get(7411)
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance")

    def test_set_fields_to_expected(self):
        for field, value in self.expected_data.items():
            with self.subTest(field=field):
                setattr(self.model, field, value)
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
                self.model.save()
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save")

                # Get a new copy
                document = self.client.documents().get(7411)
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance")

class TestSaveOnWrite(IntegrationTest):
    def setup_model(self):
        super().setup_model()
        self.model._meta.save_on_write = True

    def test_save_on_write(self):
        # Test that the document is saved when a field is written to
        new_title = "Test Document " + str(datetime.now().timestamp())
        self.assertNotEqual(new_title, self.model.title, "Test assumptions are not true")
        self.model.title = new_title
        self.assertEqual(new_title, self.model.title, "Title not updated in local instance")

        # Retrieve the document again
        document = self.client.documents().get(7411)
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

class TestTag(IntegrationTest):
    def test_get_list(self):
        documents = self.client.documents().all().tag_name("HRSH")
        self.assertIsInstance(documents, DocumentQuerySet)
        self.assertGreater(len(documents), 1000, "Incorrect number of documents retrieved")
        for i, document in enumerate(documents):
            self.assertIsInstance(document, Document)
            tags = [tag.name for tag in document.tags]
            self.assertIn("HRSH", tags, f"Document does not have HRSH tag. Tags: {tags}, tag_ids: {document.tags}")
            # avoid calling next a million times
            if i > 52:
                break

if __name__ == "__main__":
    unittest.main()
