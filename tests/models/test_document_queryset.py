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

class BaseTest(TestCase):
    def setUp(self):
        super().setUp()
        self.queryset = self.client.documents()

    def _test_method(self, sample_data : dict[str, Any], attr_name : str, expected_value : Any, fn : Callable, *args, action : str = "equal", **kwargs):
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = fn(*args, **kwargs)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                value = getattr(document, attr_name)
                if action == "equal":
                    self.assertEqual(value, expected_value, f"Expected document.{attr_name} to be {expected_value}, got {value}")
                elif action == "in":
                    self.assertIn(expected_value, value, f"Expected {expected_value} to be in document.{attr_name}")


    def _test_no_results(self, fn : Callable, *args, **kwargs):
        sample_data = load_sample_data('documents___list__no_results.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = fn(*args, **kwargs)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), 0, "Expected 0 results")
            for _ in qs:
                self.fail("Should not have any results")

class TestMethodsProcedural(BaseTest):

    def test_method_with_no_results(self):
        test_cases = [
            (self.queryset.correspondent_id, 1),
            (self.queryset.correspondent_slug, 'example-correspondent'),
            (self.queryset.correspondent_name, 'Example Correspondent'),
            (self.queryset.tag_id, 179),
            #(self.queryset.tag_slug, 'example-tag'),
            (self.queryset.tag_name, 'Example Tag'),
            (self.queryset.title, 'Example Title'),
            (self.queryset.content, 'Example Content'),
            (self.queryset.added_before, '2025-01-01'),
            (self.queryset.added_after, '2025-01-01'),
            (self.queryset.created_before, '2025-01-01'),
            (self.queryset.created_after, '2025-01-01'),
            (self.queryset.document_type_id, 8),
            (self.queryset.storage_path_id, 1),
        ]
        for fn, args in test_cases:
            self._test_no_results(fn, args)
            
class TestMeta(BaseTest):
        
    def test_disabled_filters(self):
        disabled_filters = [
            'page_count', 
            'deleted_at', 
            'updated', 
            'is_shared_by_requester'
        ]
        suffixes = [
            "__eq",
            "__range",
            "__lt",
            "__lte",
            "__gt",
            "__gte",
        ]
        for filter_name in disabled_filters:
            for suffix in suffixes:
                with self.subTest(suffix=suffix, filter_name=filter_name):
                    key = f"{filter_name}{suffix}"
                    kwargs = {key: 5}
                    with self.assertRaises(FilterDisabledError, msg=f"Filtering with {suffix} does not raise exception"):
                        self.queryset.filter(**kwargs)

    def test_filtering_fields(self):
        # Non Exhaustive list, just in case the fields change
        expected_fields = [
            # Inherited from StandardModel
            'id',
            'created_on',
            # Custom Fields for Document
            'content',
            'custom_fields',
            'document_type',
            'tags',
            'title',
        ]
        for field_name in expected_fields:
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, Document._meta.filtering_fields)


    def test_read_only_fields(self):
        # Non Exhaustive list, just in case the fields change
        expected_fields = [
            'page_count',
            'deleted_at',
            'updated',
            'is_shared_by_requester',
        ]
        for field_name in expected_fields:
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, Document._meta.read_only_fields)

class TestCorrespondent(BaseTest):

    def test_correspondent(self):
        sample_data = load_sample_data('documents___correspondent__21.json')
        correspondent_id = 21
        methods = [
            (self.queryset.correspondent_id, 21),
            (self.queryset.correspondent_slug, 'example-correspondent'),
            (self.queryset.correspondent_name, 'Example Correspondent'),
        ]
        for fn, args in methods:
            self._test_method(sample_data, 'correspondent', correspondent_id, fn, args)
            
    def test_correspondent_kwargs(self):
        test_cases = [
            {"id": 21},
            {"slug": "example-correspondent"},
            {"name": "Example Correspondent"},
        ]
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
            
class TestTag(BaseTest):
    def test_tag(self):
        sample_data = load_sample_data('documents___tags__179.json')
        tag_id = 179
        methods = [
            (self.queryset.tag_id, tag_id),
            #(self.queryset.tag_slug, 'example-tag'),
            (self.queryset.tag_name, 'Example Tag'),
        ]
        for fn, args in methods:
            self._test_method(sample_data, 'tags', tag_id, fn, args, action="in")

class TestTitle(BaseTest):

    def test_title_iexact(self):
        sample_data = load_sample_data('documents___title__pinecamp.json')
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.title("Pinecamp")
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertEqual(document.title.lower(), "pinecamp")

class TestDocumentType(BaseTest):

    def test_document_type_id(self):
        sample_data = load_sample_data('documents___document_type__8.json')
        document_type_id = 8
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.document_type_id(document_type_id)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertEqual(document.document_type, document_type_id, f"Expected document to have document_type {document_type_id}")

class TestStoragePath(BaseTest):

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

class TestContent(BaseTest):

    def test_content_contains(self):
        sample_data = load_sample_data('documents___content__contains.json')
        search_string = "do eiusmod tempor incididunt ut labore et dolore magna"
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.content(search_string)
            self.assertIsInstance(qs, DocumentQuerySet)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIsNotNone(document.content, "Expected document to have content")
                self.assertIn(search_string, document.content or '')

class TestAdded(BaseTest):

    def test_added_before(self):
        sample_data = load_sample_data('documents___added__lt__20250101.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        expected_count = 158
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.added_before(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), expected_count)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIsNotNone(document.added, "Expected added attribute to be set")
                assert document.added is not None # make mypy happy
                self.assertLess(document.added, date_obj)
                
    def test_added_after(self):
        sample_data = load_sample_data('documents___added__gt__20250101.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        expected_count = 6299
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.added_after(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), expected_count)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertIsNotNone(document.added, "Expected added to be set")
                assert document.added is not None # make mypy happy
                self.assertGreater(document.added, date_obj)

class TestCreated(BaseTest):

    def test_created_before(self):
        sample_data = load_sample_data('documents___created__lt__20250101.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        expected_count = 3822
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.created_before(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), expected_count)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertLess(document.created, date_obj)

    def test_created_after(self):
        sample_data = load_sample_data('documents___created__gt__20250101.json')
        date_str = '2025-01-01'
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        expected_count = 2638
        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            qs = self.queryset.created_after(date_str)
            self.assertIsInstance(qs, DocumentQuerySet)
            self.assertEqual(qs.count(), expected_count)
            for document in qs:
                self.assertIsInstance(document, Document)
                self.assertGreater(document.created, date_obj)
                 
if __name__ == "__main__":
    unittest.main()
