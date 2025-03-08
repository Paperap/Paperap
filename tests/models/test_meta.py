"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_meta.py
        Project: paperap
        Created: 2025-03-07
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-07     By Jess Mann

"""
import unittest
from unittest.mock import MagicMock
from typing import Iterable, Literal
from enum import StrEnum

from paperap.const import ModelStatus
from paperap.models.abstract.meta import StatusContext
from paperap.tests import TestCase, load_sample_data
from paperap.models.document import Document
from paperap.resources.documents import DocumentResource


# Unit tests
class TestStatusContext(TestCase):
    def setUp(self):
        super().setUp()
        sample_data = load_sample_data("documents_item.json")
        self.resource = DocumentResource(self.client)
        self.model = Document.from_dict(sample_data, self.resource)

    def test_status_changes_and_reverts(self):
        """Ensure that status changes and reverts after the context exits."""
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Test assumptions failed. Cannot run test")
        with StatusContext(self.model, ModelStatus.UPDATING):
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
        self.assertEqual(self.model._meta.status, ModelStatus.READY)

    def test_status_changes_and_reverts_to_non_default(self):
        """Ensure that status changes and reverts to a non-default status after the context exits."""
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Test assumptions failed. Cannot run test")
        self.model._meta.status = ModelStatus.SAVING
        with StatusContext(self.model, ModelStatus.UPDATING):
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
        self.assertEqual(self.model._meta.status, ModelStatus.SAVING)
        
    def test_status_reverts_on_exception(self):
        """Ensure that the previous status is restored even if an exception occurs."""
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Test assumptions failed. Cannot run test")
        try:
            with StatusContext(self.model, ModelStatus.UPDATING):
                self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
                raise ValueError("Intentional exception")
        except ValueError:
            self.assertEqual(self.model._meta.status, ModelStatus.READY, "Status was not reverted within except block.")
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Status change did not persist after catching exception.")

    def test_status_reverts_after_change(self):
        """Ensure that the status reverts after a change is made."""
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Test assumptions failed. Cannot run test")
        with StatusContext(self.model, ModelStatus.UPDATING):
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
            self.model._meta.status = ModelStatus.SAVING
            self.assertEqual(self.model._meta.status, ModelStatus.SAVING)
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Status change did not revert after manual change.")

    def test_nested(self):
        """Ensure that nested contexts work as expected."""
        self.assertEqual(self.model._meta.status, ModelStatus.READY, "Test assumptions failed. Cannot run test")
        with StatusContext(self.model, ModelStatus.UPDATING):
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
            with StatusContext(self.model, ModelStatus.SAVING):
                self.assertEqual(self.model._meta.status, ModelStatus.SAVING)
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)
        self.assertEqual(self.model._meta.status, ModelStatus.READY)

if __name__ == "__main__":
    unittest.main()
