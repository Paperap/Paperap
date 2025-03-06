"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document_queryset.py
        Project: paperap
        Created: 2025-03-05
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-05     By Jess Mann

"""
from __future__ import annotations

import os
from typing import Any, Callable, Iterable
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
from paperap.exceptions import FilterDisabledError

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class TestDocumentQuerySet(TestCase):
    def setUp(self):
        super().setUp()
        self.queryset = self.client.documents()

    def test_disabled_filters(self):
        suffixes = [
            "__eq",
            "__range",
            "__lt",
            "__lte",
            "__gt",
            "__gte",
        ]
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                key = f"page_count{suffix}"
                kwargs = {key: 5}
                with self.assertRaises(FilterDisabledError, msg=f"Filtering with {suffix} does not raise exception"):
                    self.queryset.filter(**kwargs)
                
    def test_correspondent_id(self):
        test_cases = [
            1, 1000,
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.correspondent_id(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document, "Expected document to be an instance of Document when filtering by correspondent id")
                    self.assertIsNotNone(document.correspondent, "Expected document to have a correspondent")
                    self.assertEqual(test_case, document.correspondent.id, "Expected document to have a correspondent with the specified id")

    def _test_method(self, sample_data : dict[str, Any], attr_name : str, expected_value : Any, fn : Callable, *args, **kwargs):
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = fn(*args, **kwargs)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                value = getattr(document, attr_name)
                self.assertEqual(value, expected_value, f"Expected document.{attr_name} to be {expected_value}, got {value}")

    def test_correspondent(self):
        sample_data = load_sample_data('documents___correspondent__21.json')
        correspondent_id = 21
        methods = [
            (self.queryset.correspondent_id, 21),
            (self.queryset.correspondent_slug, 'example-correspondent'),
            (self.queryset.correspondent_name, 'Example Correspondent'),
        ]
        for fn, args in methods:
            self._test_method(sample_data, 'correspondent', correspondent_id, fn, *args)

    def test_tag(self):
        sample_data = load_sample_data('documents___tags__179.json')
        tag_id = 179
        methods = [
            (self.queryset.tag_id, tag_id),
            (self.queryset.tag_slug, 'example-tag'),
            (self.queryset.tag_name, 'Example Tag'),
        ]
        for fn, args in methods:
            self._test_method(sample_data, 'tags', tag_id, fn, args)

    def _test_no_results(self, fn : Callable, *args, **kwargs):
        sample_data = load_sample_data('documents___list__no_results.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = fn(*args, **kwargs)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), 0, "Expected 0 results")
            for document in qs:
                self.fail("Should not have any results")

    def test_method_with_no_results(self):
        test_cases = [
            (self.queryset.correspondent_id, 1),
            (self.queryset.correspondent_slug, 'example-correspondent'),
            (self.queryset.correspondent_name, 'Example Correspondent'),
            (self.queryset.tag_id, 179),
            (self.queryset.tag_slug, 'example-tag'),
            (self.queryset.tag_name, 'Example Tag'),
            (self.queryset.title, 'Example Title'),
            (self.queryset.content, 'Example Content'),
            (self.queryset.added_before, '2025-01-01'),
            (self.queryset.added_after, '2025-01-01'),
            (self.queryset.deleted_before, '2025-01-01'),
            (self.queryset.deleted_after, '2025-01-01'),
            (self.queryset.created_before, '2025-01-01'),
            (self.queryset.created_after, '2025-01-01'),
            (self.queryset.updated_after, '2025-01-01'),
            (self.queryset.shared, True),
            (self.queryset.shared, False),
            (self.queryset.document_type_id, 8),
            (self.queryset.storage_path_id, 1),
        ]
        for fn, args in test_cases:
            self._test_no_results(fn, args)

    def test_title_iexact(self):
        sample_data = load_sample_data('documents___title__iexact.json')
        #with patch('paperap.client.PaperlessClient.request') as mock_request:
        #    mock_request.return_value = sample_data
        qs = self.queryset.title("Hudson")
        self.assertIsInstance(qs, DocumentQuerySet)
        for document in qs:
            self.assertIsInstance(document, Document)
            self.assertEqual(document.title.lower(), "test")

    def test_correspondent_kwargs(self):
        test_cases = {
            {"id": 21},
            {"slug": "example-correspondent"},
            {"name": "Example Correspondent"},
        }
        sample_data = load_sample_data('documents___correspondent__21.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            for kwargs in test_cases:
                qs = self.queryset.correspondent(**kwargs)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)
                    self.assertIsInstance(document.correspondent, int)
                    self.assertEqual(document.correspondent, 21)
                
    def test_correspondent_args(self):
        test_cases = [
            21,
            "Example Correspondent",
        ]
        sample_data = load_sample_data('documents___correspondent__21.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            for arg in test_cases:
                qs = self.queryset.correspondent(arg)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)
                    self.assertIsInstance(document.correspondent, int)
                    self.assertEqual(document.correspondent, 21)

    def test_correspondent_arg_and_kwargs(self):
        sample_data = load_sample_data('documents___correspondent__21.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.correspondent(21, slug="example-correspondent")
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIsInstance(document.correspondent, int)
                self.assertEqual(document.correspondent, 21)

    def test_correspondent_no_params(self):
        with self.assertRaises(ValueError):
            self.queryset.correspondent()

    def test_document_type_id(self):
        #sample_data = load_sample_data('documents___document_type_8.json')
        document_type_id = 8
        #with patch('paperap.client.PaperlessClient.request') as mock_request:
        #    mock_request.return_value = sample_data
        qs = self.queryset.document_type_id(document_type_id)
        self.assertIsInstance(qs, DocumentQuerySet)
        for document in qs:
            self.assertIsInstance(document, Document)
            self.assertEqual(document.document_type, document_type_id, f"Expected document to have document_type {document_type_id}")

    def test_storage_path_id(self):
        sample_data = load_sample_data('documents___storage_path__52.json')
        storage_path_id = 52
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.storage_path_id(storage_path_id)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIsNotNone(document.storage_path, "Expected document to have a storage path")
                self.assertEqual(document.storage_path, storage_path_id)

    def test_content_contains(self):
        sample_data = load_sample_data('documents___content__contains.json')
        search_string = "do eiusmod tempor incididunt ut labore et dolore magna"
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.content(search_string)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIn(search_string, document.content)

    def test_added_before(self):
        #sample_data = load_sample_data('documents___added__lt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        #mock_request.return_value = sample_data
        qs = self.queryset.added_before(date_str)
        self.assertIsInstance(qs, DocumentQuerySet)
        for document in qs:
            self.assertIsInstance(document, Document)
            self.assertLess(document.added, date_obj)
                
    def test_added_after(self):
        sample_data = load_sample_data('documents___added__gt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.added_after(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertGreater(document.added, date_obj)

    def test_deleted_before(self):
        sample_data = load_sample_data('documents___deleted_at__lt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.deleted_before(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document, "Expected document to be an instance of Document when filtering by deleted_at")
                self.assertIsNotNone(document.deleted_at, "Expected deleted_at to be set")
                self.assertLess(document.deleted_at, date_obj, "Expected deleted_at to be less than date_obj")
                
    def test_deleted_after(self):
        #sample_data = load_sample_data('documents___deleted_at__gt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        #with patch('paperap.client.PaperlessClient.request') as mock_request:
        #mock_request.return_value = sample_data
        qs = self.queryset.deleted_after(date_str)
        self.assertIsInstance(qs, DocumentQuerySet)
        for document in qs:
            self.assertIsInstance(document, Document, "Expected document to be an instance of Document when filtering by deleted_after")
            self.assertIsNotNone(document.deleted_at, "Expected deleted_at to be set")
            self.assertGreater(document.deleted_at, date_obj, "Expected deleted_at to be greater than date_obj")

    def test_created_before(self):
        sample_data = load_sample_data('documents___created__lt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.created_before(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertLess(document.created, date_obj)

    def test_created_after(self):
        #sample_data = load_sample_data('documents___created__gt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        #with patch('paperap.client.PaperlessClient.request') as mock_request:
        #mock_request.return_value = sample_data
        qs = self.queryset.created_after(date_str)
        self.assertIsInstance(qs, DocumentQuerySet)
        for document in qs:
            self.assertIsInstance(document, Document)
            self.assertGreater(document.created, date_obj)

    def test_updated_after(self):
        sample_data = load_sample_data('documents___updated__gt.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.updated_after(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertGreater(document.updated, date_obj)
                   
    def test_shared(self):
        test_cases = [True, False]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                qs = self.queryset.shared(test_case)
                self.assertIsInstance(qs, DocumentQuerySet)
                for document in qs:
                    self.assertIsInstance(document, Document)

if __name__ == "__main__":
    unittest.main()
