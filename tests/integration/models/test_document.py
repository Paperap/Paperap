"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
        Project: paperap
        Created: 2025-03-08
        Version: 0.0.2
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
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
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
            # Temporarily skip dates (TODO)
            if field in ['added', 'created', 'updated']:
                continue
            retrieved_value = getattr(document, field)
            self.assertEqual(retrieved_value, value, f"Field {field} did not revert to initial value on teardown. Integration tests will fail")

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
            ("tags", [[74], [254], [45, 80]]),
        ]
        for field, values in fields:
            for value in values:
                current = getattr(self.model, field)
                self.assertNotEqual(value, current, f"Test assumptions are not true for {field}")
                setattr(self.model, field, value)
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
                self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")
                self.model.save()
                self.assertEqual(value, getattr(self.model, field), f"{field} not updated after save")
                self.assertEqual(self.model.id, 7411, "ID changed after save")

                # Get a new copy
                document = self.client.documents().get(7411)
                self.assertEqual(value, getattr(document, field), f"{field} not updated in remote instance")

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
            "tags": [74],
        }
        self.model.update(**fields)
        for field, value in fields.items():
            self.assertEqual(value, getattr(self.model, field), f"{field} not updated in local instance")
            self.assertEqual(self.model.id, 7411, f"ID changed after update to {field}")

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

if __name__ == "__main__":
    unittest.main()
