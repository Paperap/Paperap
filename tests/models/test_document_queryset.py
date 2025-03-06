"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document_queryset.py
        Project: paperap
        Created: 2025-03-05
        Version: 0.0.1
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
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from paperap.models import (
    Document, DocumentQuerySet, 
    Tag, TagQuerySet,
    Correspondent, CorrespondentQuerySet,
    DocumentType, DocumentTypeQuerySet,
    StoragePath, StoragePathQuerySet,
    Profile, ProfileQuerySet,
    User, UserQuerySet,
)
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag, TagQuerySet
from paperap.tests import TestCase, load_sample_data

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class TestDocumentQuerySet(TestCase):
    def setUp(self):
        super().setUp()
        self.queryset = self.client.documents()

    def test_tag_id(self):
        test_cases = [
            1, 1000,
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.tag_id(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)
                    self.assertIn(test_case, document.tags)

    def test_tag_name(self):
        test_cases = [
            'test', 'tag',
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.tag_name(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_correspondent_id(self):
        test_cases = [
            1, 1000,
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.correspondent_id(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)
                    self.assertEqual(test_case, document.correspondent.id)

    def test_correspondent_name(self):
        test_cases = [
            'test', 'correspondent',
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.correspondent_name(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)


    def test_title(self):
        test_cases = ["Test Document", "Sample Title"]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.title(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)
                    self.assertEqual(document.title, test_case)

    def test_correspondent(self):
        test_cases = [1, "John Doe"]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.correspondent(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_document_type_id(self):
        test_cases = [1, 2]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.document_type_id(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_storage_path_id(self):
        test_cases = [1, 3]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.storage_path_id(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_content(self):
        test_cases = ["sample text", "important"]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.content(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_added_after(self):
        test_cases = ["2025-01-01", "2024-06-15"]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.added_after(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_deleted_before(self):
        test_cases = ["2025-01-01", "2024-12-31"]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.deleted_before(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_shared(self):
        test_cases = [True, False]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.shared(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_created_before(self):
        test_cases = [datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2024, 5, 10, tzinfo=timezone.utc)]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.created_before(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_updated_after(self):
        test_cases = [datetime(2025, 2, 1, tzinfo=timezone.utc), datetime(2024, 8, 1, tzinfo=timezone.utc)]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.updated_after(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

    def test_page_count_between(self):
        test_cases = [(5, 10), (1, 20)]
        for min_pages, max_pages in test_cases:
            with self.subTest(min_pages=min_pages, max_pages=max_pages):
                qs = self.queryset.page_count_between(min_pages, max_pages)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

if __name__ == "__main__":
    unittest.main()
