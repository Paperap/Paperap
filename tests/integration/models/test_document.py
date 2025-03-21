"""



----------------------------------------------------------------------------

METADATA:

File:    test_document.py
        Project: paperap
Created: 2025-03-08
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-08     By Jess Mann

"""
from __future__ import annotations

import logging
import os
import unittest
from datetime import datetime, timezone
from typing import Iterable, override
from unittest.mock import MagicMock, patch
from pathlib import Path

from paperap.client import PaperlessClient
from paperap.exceptions import ReadOnlyFieldError, ResourceNotFoundError
from paperap.models import *
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.documents import DocumentResource
from tests.lib import DocumentUnitTest, load_sample_data

logger = logging.getLogger(__name__)

#sample_document_list = load_sample_data('documents_list.json')
#sample_document = load_sample_data('documents_item.json')

class IntegrationTest(DocumentUnitTest):
    mock_env = False

    @override
    def setUp(self):
        super().setUp()
        self.model = self.client.documents().get(7411)
        self._initial_data = self.model.to_dict()

    @override
    def tearDown(self):
        # Request that paperless ngx reverts to the previous data
        self.model.update_locally(from_db=True, **self._initial_data)
        # Must be called manually in case subclasses turn off autosave and mocks self.is_new()
        self.model.save(force=True)

        # TODO: confirm without another query
        return super().tearDown()

class TestIntegrationTest(IntegrationTest):
    def test_integration(self):
        # Test if the document can be retrieved
        self.assertIsInstance(self.model, Document)
        self.assertEqual(self.model.id, 7411, "Document ID does not match expected value. Cannot run test")

        # Test if the document can be updated
        random_str = str(datetime.now().timestamp())
        self.model.title = f"Update Document {random_str}"
        self.model.content = f"Updated Test Document {random_str}"
        self.model.archive_serial_number = 123456
        self.model.save()
        self.assertEqual(self.model.title, f"Update Document {random_str}", "Document title did not update as expected. Cannot test IntegrationTest class")
        self.assertEqual(self.model.content, f"Updated Test Document {random_str}", "Document content did not update as expected. Cannot test IntegrationTest class")
        self.assertEqual(self.model.archive_serial_number, 123456, "Document archive_serial_number did not update as expected. Cannot test IntegrationTest class")

        # Manually call tearDown
        self.tearDown()

        # Retrieve the document again
        document = self.client.documents().get(7411)
        for field, initial_value in self._initial_data.items():
            # Skip read-only fields
            if field in self.model._meta.read_only_fields:
                continue
            # Test notes individually
            # Temporarily skip dates (TODO)
            if field in ['added', 'created', 'updated', 'notes']:
                continue
            paperless_value = getattr(document, field)
            self.assertEqual(paperless_value, initial_value, f"Field {field} did not revert to initial value on teardown. Integration tests will fail")

        self.assertEqual(len(document.notes), len(self._initial_data['notes']), "Note count did not revert to initial value on teardown. Integration tests will fail")
        for note in self._initial_data['notes']:
            self.assertTrue(self._has_note(document, note), "Note did not revert to initial value on teardown. Integration tests will fail")

    def _has_note(self, document : Document, note : dict):
        for doc_note in document.notes:
            if doc_note.matches_dict(note):
                return True
        return False

class TestFeatures(IntegrationTest):
    save_on_write = False

    def test_refresh(self):
        # Test that the document is updated locally when refresh is called
        document = self.client.documents().get(7411)
        original_title = document.title
        original_content = document.content

        new_title = "Test Document " + str(datetime.now().timestamp())
        new_content = "Test Content" + str(datetime.now().timestamp())
        document.title = new_title
        document.content = new_content
        self.assertEqual(document.title, new_title, "Test assumptions are not true")
        self.assertEqual(document.content, new_content, "Test assumptions are not true")

        changed = document.refresh()
        self.assertTrue(changed, "Document did not refresh")
        self.assertEqual(document.title, original_title, f"Title not refreshed from db. Update was: {new_title}")
        self.assertEqual(document.content, original_content, f"Content not refreshed from db. Update was: {new_content}")

    def test_set_archived_file_name(self):
        with self.assertRaises(ReadOnlyFieldError):
            self.model.update_locally(from_db=False, archived_file_name='example_test_name.pdf')

    def test_set_archived_filename_same_value(self):
        # Test that an error isn't thrown when "setting" a read only field to the same value
        original_filename = self.model.archived_file_name
        self.model.update_locally(from_db=False, archived_file_name=original_filename)
        self.assertEqual(original_filename, self.model.archived_file_name, "Archived file name changed after setting to the same value")

    def test_set_title_changes_archived_file_name(self):
        # This isn't a feature of ours, but it's functionality of paperless that is unexpected
        # This test ensures that if that feature changes, our test failures will notify us of the change.
        document = self.client.documents().get(7411)
        original_filename = document.archived_file_name
        new_title = f"Test Document {datetime.now().timestamp()}"
        document.title = new_title
        document.save()
        self.assertNotEqual(original_filename, document.archived_file_name, "Archived file name did not change after title update")

class TestUpload(IntegrationTest):
    save_on_write = False

    def test_upload(self):
        # Test that the document is saved when a file is uploaded
        filename = "Sample JPG.jpg"
        filepath = Path(__file__).parents[3] / "sample_data" / filename
        document = self.resource.upload(filepath)

        self.assertIsInstance(document, Document)
        self.assertEqual(document.original_file_name, filename, "Original file name does not match expected value")
        self.assertIsInstance(document.id, int)
        self.assertGreater(document.id, 0, "Document ID is not set")

        # Retrieve it
        retrieved_document = self.client.documents().get(document.id)
        self.assertEqual(document, retrieved_document)

        # Delete it
        document.delete()
        with self.assertRaises(ResourceNotFoundError):
            self.client.documents().get(document.id)

class TestSaveManual(IntegrationTest):
    save_on_write = False

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
            ("correspondent_id", [21, 37, None]),
            ("document_type_id", [10, 16, None]),
            ("tag_ids", [[74], [254], [45, 80], [74, 254, 45]]),
        ]
        for field, values in fields:
            for value in values:
                current = getattr(self.model, field)
                setattr(self.model, field, value)
                if field == "tag_ids":
                    self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance. Previous value {current}")
                self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")
                self.model.save()
                if field == "tag_ids":
                    self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated after save. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save. Previous value {current}")
                self.assertEqual(self.model.id, 7411, "ID changed after save")

                # Get a new copy
                document = self.client.documents().get(7411)
                if field == "tag_ids":
                    self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance. Previous value {current}")
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
            "correspondent_id": 21,
            "document_type_id": 10,
            "tag_ids": [38],
        }
        self.model.update(**fields)
        for field, value in fields.items():
            self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
            self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")

class TestSaveNone(IntegrationTest):
    save_on_write = False

    @override
    def setUp(self):
        super().setUp()

        if not self.model.tag_ids:
            self.model.tag_ids = [38]
            self.model.save()

        self.none_data = {
            "archive_serial_number": None,
            "content": "",
            "correspondent_id": None,
            "custom_field_dicts": [],
            "deleted_at": None,
            "document_type_id": None,
            #"notes": [],
            "page_count": None,
            "storage_path_id": None,
            "title": "",
        }

        self.expected_data = {
            "archive_serial_number": 123456,
            "content": "Test Content",
            "correspondent_id": 31,
            "custom_field_dicts": [{"field": 32, "value": "Test Value"}],
            "document_type_id": 16,
            "tag_ids": [28],
            "title": "Test Document",
            #"notes": ["Test Note"],
            "storage_path_id": 1,
        }

    def test_update_tags_to_none(self):
        # Test that tags can't be emptied (because paperless doesn't support this)
        with self.assertRaises(NotImplementedError):
            self.model.update_locally(tags=None)

    def test_update_tag_ids_to_empty(self):
        # Test that tags can't be emptied (because paperless doesn't support this)
        with self.assertRaises(NotImplementedError):
            self.model.update(tag_ids=[])

    def test_set_fields(self):
        # Ensure fields can be set and reset without consequences
        self.model.update(**self.expected_data)
        document = self.client.documents().get(7411)
        for field, value in self.expected_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on first set to expected")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on first set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on first set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on first set to expected")

        none_data = {k: None for k in self.none_data.keys()}
        self.model.update(**none_data)
        document = self.client.documents().get(7411)
        for field, value in self.none_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on set to None")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on set to None")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on set to None")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on set to None")

        self.model.update(**self.expected_data)
        document = self.client.documents().get(7411)
        for field, value in self.expected_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on second set to expected")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on second set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on second set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on second set to expected")

    def test_set_fields_to_none(self):
        # field_name -> expected value after being set to None
        for field, value in self.none_data.items():
            #with self.subTest(field=field):
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
    save_on_write = True

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
            self.assertIn("HRSH", document.tag_names, f"Document does not have HRSH tag. tag_ids: {document.tag_ids}")
            # avoid calling next a million times
            if i > 52:
                break

if __name__ == "__main__":
    unittest.main()
