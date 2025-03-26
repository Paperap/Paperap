
from __future__ import annotations

import logging
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, override
from unittest.mock import MagicMock, patch
import tempfile
from paperap.client import PaperlessClient
from paperap.exceptions import ReadOnlyFieldError, ResourceNotFoundError, APIError
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
    # Class variables to cache entity IDs
    _entity_ids = {
        'correspondent': [],
        'document_type': [],
        'tag': [],
        'storage_path': [],
        'custom_field': [],
    }
    _ids_initialized = False

    @classmethod
    def _initialize_entity_ids(cls, client):
        """Initialize entity IDs for use in tests if not already done."""
        if cls._ids_initialized:
            return

        # Get correspondent IDs
        correspondents = list(client.correspondents().all())
        cls._entity_ids['correspondent'] = [c.id for c in correspondents[:3] if c.id is not None]

        # Get document type IDs
        document_types = list(client.document_types().all())
        cls._entity_ids['document_type'] = [dt.id for dt in document_types[:3] if dt.id is not None]

        # Get tag IDs
        tags = list(client.tags().all())
        cls._entity_ids['tag'] = [t.id for t in tags[:5] if t.id is not None]

        # Get storage path IDs
        storage_paths = list(client.storage_paths().all())
        cls._entity_ids['storage_path'] = [sp.id for sp in storage_paths[:2] if sp.id is not None]

        # Get custom field IDs
        custom_fields = list(client.custom_fields().all())
        cls._entity_ids['custom_field'] = [cf.id for cf in custom_fields[:2] if cf.id is not None]

        cls._ids_initialized = True

    @override
    def setUp(self):
        super().setUp()
        self.model = self.client.documents().first()
        self._initial_data = self.model.to_dict()

        # Initialize entity IDs if not already done
        self._initialize_entity_ids(self.client)

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
        self.assertEqual(self.model.id, self._initial_data['id'], "Document ID does not match expected value. Cannot run test")

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
        document = self.client.documents().get(self._initial_data['id'])
        for field, initial_value in self._initial_data.items():
            # Skip read-only fields
            if field in self.model._meta.read_only_fields:
                continue
            # Test notes individually
            # Temporarily skip dates (TODO)
            if field in ['added', 'created', 'notes']:
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
        document = self.client.documents().get(self._initial_data['id'])
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
        document = self.client.documents().get(self._initial_data['id'])
        original_filename = document.archived_file_name
        if original_filename is None:
            self.skipTest("Document does not have an archived file name. Cannot run test")
        new_title = f"Test Document {datetime.now().timestamp()}"
        document.title = new_title
        document.save()
        self.assertNotEqual(original_filename, document.archived_file_name, "Archived file name did not change after title update")

    def test_equal(self):
        # Test that two documents are equal if they have the same ID
        document1 = self.client.documents().get(self._initial_data['id'])
        document2 = self.client.documents().get(self._initial_data['id'])
        self.assertEqual(document1, document2, "Documents with the same ID are not equal")

class TestUpload(IntegrationTest):
    save_on_write = False

    def test_upload(self):
        # Test that the document is saved when a file is uploaded
        filename = "Sample JPG.txt"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            filepath = temp_file.name
            contents = f"Sample content for the file. {datetime.now().timestamp()}"
            temp_file.write(contents.encode())
            temp_file.close()

            document = self.resource.upload_sync(filepath)

            self.assertIsInstance(document, Document)
            #self.assertEqual(document.original_filename, filename, f"Original file name does not match expected value: {document.to_dict()}")
            self.assertIsInstance(document.id, int)
            self.assertGreater(document.id, 0, "Document ID is not set")

            # Retrieve it
            retrieved_document = self.client.documents().get(document.id)
            self.assertEqual(document, retrieved_document)

            # Upload duplicate - should produce log message about duplicate
            with self.assertLogs(level='WARNING') as log:
                with self.assertRaises(APIError):
                    self.resource.upload_sync(filepath)
                # Verify the duplicate file error was logged
                self.assertTrue(any("Not consuming" in entry and "duplicate" in entry for entry in log.output))

            # Still there
            second_retrieved_document = self.client.documents().get(document.id)
            self.assertEqual(document, second_retrieved_document)

            # Delete it
            document.delete()

            # No longer available
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
        self.assertEqual(self.model.id, self._initial_data['id'], "ID changed after update")
        self.model.save()
        self.assertEqual(new_title, self.model.title, "Title not updated after save")
        self.assertEqual(self.model.id, self._initial_data['id'], "ID changed after save")

        # Retrieve the document again
        document = self.client.documents().get(self._initial_data['id'])
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

    def test_save_on_write_off(self):
        # Test that the document is not saved when a field is written to
        new_title = "Test Document " + str(datetime.now().timestamp())
        self.assertNotEqual(new_title, self.model.title, "Test assumptions are not true")
        self.model.title = new_title
        self.assertEqual(new_title, self.model.title, "Title not updated in local instance")

        # Retrieve the document again
        document = self.client.documents().get(self._initial_data['id'])
        self.assertNotEqual(new_title, document.title, "Title updated in remote instance without calling write")

    def test_save_all_fields(self):
        #(field_name, [values_to_set])
        ts = datetime.now().timestamp()

        # Use dynamically retrieved IDs
        correspondent_ids = self._entity_ids['correspondent']
        document_type_ids = self._entity_ids['document_type']
        tag_ids = self._entity_ids['tag']

        fields = [
            ("title", [f"Test Document {ts}"]),
            ("correspondent_id", [correspondent_ids[0] if correspondent_ids else None,
                                correspondent_ids[1] if len(correspondent_ids) > 1 else None,
                                None]),
            ("document_type_id", [document_type_ids[0] if document_type_ids else None,
                                document_type_ids[1] if len(document_type_ids) > 1 else None,
                                None]),
            ("tag_ids", [[tag_ids[0]] if tag_ids else [],
                       [tag_ids[1]] if len(tag_ids) > 1 else [],
                       [tag_ids[0], tag_ids[1]] if len(tag_ids) > 1 else [],
                       [tag_ids[0], tag_ids[1], tag_ids[2]] if len(tag_ids) > 2 else []]),
        ]
        for field, values in fields:
            for value in values:
                current = getattr(self.model, field)
                setattr(self.model, field, value)
                if field == "tag_ids":
                    self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance. Previous value {current}")
                self.assertEqual(self.model.id, self._initial_data['id'], f"ID changed after update to {field}")
                self.model.save()
                if field == "tag_ids":
                    self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated after save. Previous value {current}")
                else:
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save. Previous value {current}")
                self.assertEqual(self.model.id, self._initial_data['id'], "ID changed after save")

                # Get a new copy
                document = self.client.documents().get(self._initial_data['id'])
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
        document = self.client.documents().get(self._initial_data['id'])
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

    def test_update_all_fields(self):
        #(field_name, [values_to_set])
        ts = datetime.now().timestamp()

        # Use dynamically retrieved IDs
        correspondent_id = self._entity_ids['correspondent'][0] if self._entity_ids['correspondent'] else None
        document_type_id = self._entity_ids['document_type'][0] if self._entity_ids['document_type'] else None
        tag_id = self._entity_ids['tag'][0] if self._entity_ids['tag'] else None

        fields = {
            "title": f"Test Document {ts}",
            "correspondent_id": correspondent_id,
            "document_type_id": document_type_id,
            "tag_ids": [tag_id] if tag_id else [],
        }
        self.model.update(**fields)
        for field, value in fields.items():
            self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
            self.assertEqual(self.model.id, self._initial_data['id'], f"ID changed after update to {field}")

class TestSaveNone(IntegrationTest):
    save_on_write = False

    @override
    def setUp(self):
        super().setUp()

        # Get a tag ID to ensure the document has at least one tag
        tag_id = self._entity_ids['tag'][0] if self._entity_ids['tag'] else None

        if not self.model.tag_ids and tag_id:
            self.model.tag_ids = [tag_id]
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

        # Use dynamically retrieved IDs
        correspondent_id = self._entity_ids['correspondent'][0] if self._entity_ids['correspondent'] else None
        document_type_id = self._entity_ids['document_type'][0] if self._entity_ids['document_type'] else None
        tag_id = self._entity_ids['tag'][1] if len(self._entity_ids['tag']) > 1 else (self._entity_ids['tag'][0] if self._entity_ids['tag'] else None)
        storage_path_id = self._entity_ids['storage_path'][0] if self._entity_ids['storage_path'] else None
        custom_field_id = self._entity_ids['custom_field'][0] if self._entity_ids['custom_field'] else None

        self.expected_data = {
            "archive_serial_number": 123456,
            "content": "Test Content",
            "correspondent_id": correspondent_id,
            "custom_field_dicts": [{"field": custom_field_id, "value": "Test Value"}] if custom_field_id else [],
            "document_type_id": document_type_id,
            "tag_ids": [tag_id] if tag_id else [],
            "title": "Test Document",
            #"notes": ["Test Note"],
            "storage_path_id": storage_path_id,
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
        document = self.client.documents().get(self._initial_data['id'])
        for field, value in self.expected_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on first set to expected")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on first set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on first set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on first set to expected")

        none_data = {k: None for k in self.none_data.keys()}
        self.model.update(**none_data)
        document = self.client.documents().get(self._initial_data['id'])
        for field, value in self.none_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on set to None")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on set to None")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on set to None")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on set to None")

        self.model.update(**self.expected_data)
        document = self.client.documents().get(self._initial_data['id'])
        for field, value in self.expected_data.items():
            if field == "tag_ids":
                self.assertCountEqual(value, self.model.tag_ids, f"{field} not updated in local instance on second set to expected")
                self.assertCountEqual(value, document.tag_ids, f"{field} not updated in remote instance on second set to expected")
            else:
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance on second set to expected")
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance on second set to expected")

    def test_set_fields_to_none(self):
        # field_name -> expected value after being set to None
        with self.assertLogs(level='INFO') as log:
            for field, value in self.none_data.items():
                #with self.subTest(field=field):
                    setattr(self.model, field, None)
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
                    self.model.save()
                    self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save")

                    # Get a new copy
                    document = self.client.documents().get(self._initial_data['id'])
                    self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance")

            # Verify the "not dirty" messages were logged
            self.assertTrue(any("Model is not dirty, skipping save" in entry for entry in log.output))

    def test_set_fields_to_expected(self):
        for field, value in self.expected_data.items():
            with self.subTest(field=field):
                setattr(self.model, field, value)
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
                self.model.save()
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save")

                # Get a new copy
                document = self.client.documents().get(self._initial_data['id'])
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
        document = self.client.documents().get(self._initial_data['id'])
        self.assertEqual(new_title, document.title, "Title not updated in remote instance")

class TestTag(IntegrationTest):
    def test_get_list(self):
        # Find a tag with documents to test tag filtering
        test_tag = None
        for tag in self.client.tags().all():
            # Check if tag has documents
            tag_docs = self.client.documents().all().tag_id(tag.id)
            if len(tag_docs) > 0:
                test_tag = tag
                break

        # Skip test if no suitable tag is found
        if not test_tag:
            self.skipTest("No tag with documents found")

        documents = self.client.documents().all().tag_name(test_tag.name)
        self.assertIsInstance(documents, DocumentQuerySet)
        self.assertGreater(len(documents), 0, "No documents retrieved for tag")
        for i, document in enumerate(documents):
            self.assertIsInstance(document, Document)
            self.assertIn(test_tag.name, document.tag_names, f"Document does not have {test_tag.name} tag. tag_ids: {document.tag_ids}")
            # avoid calling next a million times
            if i > 52:
                break

if __name__ == "__main__":
    unittest.main()
