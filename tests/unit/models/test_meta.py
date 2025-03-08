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
from paperap.tests import TestCase, load_sample_data, DocumentTest
from paperap.models.document import Document
from paperap.resources.documents import DocumentResource


# Unit tests
class TestStatusContext(DocumentTest):
    def test_status_changes_and_reverts(self):
        """Ensure that all statuses are valid."""
        for status_initial in ModelStatus:
            for status_context in ModelStatus:
                with self.subTest(status_initial=status_initial, status_context=status_context):
                    self.model._meta.status = status_initial
                    with StatusContext(self.model, status_context):
                        self.assertEqual(self.model._meta.status, status_context)
                    self.assertEqual(self.model._meta.status, status_initial)

    def test_default_initial(self):
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

    def test_status_reverts_with_no_initial_status(self):
        """Ensure that the status properly reverts even when no initial status exists."""
        self.model._meta.status = None # type: ignore
        with StatusContext(self.model, ModelStatus.UPDATING):
            self.assertEqual(self.model._meta.status, ModelStatus.UPDATING)

        self.assertEqual(self.model._meta.status, ModelStatus.ERROR)

    def test_passing_bad_model(self):
        """Ensure that passing a bad model raises an exception."""
        class Foo:
            pass

        test_cases = [
            None,
            {},
            [],
            set(),
            1,
            "str",
            Foo(),
        ]
        for value in test_cases:
            with self.assertRaises(AttributeError):
                with StatusContext(value, ModelStatus.UPDATING):
                    pass

    def test_params_are_required(self):
        """Ensure that the context requires parameters."""
        with self.assertRaises(TypeError):
            with StatusContext(): # type: ignore
                pass
        with self.assertRaises(TypeError):
            with StatusContext(self.model): # type: ignore
                pass

    def test_context_manager_is_not_returned(self):
        """Ensure that the context manager is not returned."""
        with StatusContext(self.model, ModelStatus.UPDATING) as context:
            self.assertIsNone(context, "Context manager was returned.")
        self.assertIsNone(context, "Context manager was not destroyed.")

    def test_attributes_read_only(self):
        """Ensure that the attributes are read-only."""
        context = StatusContext(self.model, ModelStatus.UPDATING)
        with self.assertRaises(AttributeError):
            context.model = self.model # type: ignore
        with self.assertRaises(AttributeError):
            context.new_status = ModelStatus.UPDATING # type: ignore
        with self.assertRaises(AttributeError):
            context.previous_status = ModelStatus.READY # type: ignore

if __name__ == "__main__":
    unittest.main()
