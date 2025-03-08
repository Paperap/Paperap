"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_queryset.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations

import logging
import os
from string import Template
import unittest
from unittest.mock import MagicMock, patch

# Import the exceptions used by QuerySet.
from paperap.exceptions import ObjectNotFoundError, MultipleObjectsFoundError
from paperap.models import StandardModel, QuerySet
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.models.document import Document
from paperap.resources import PaperlessResource, StandardResource
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.tests import load_sample_data, TestCase, DocumentTest

MockClient = MagicMock(PaperlessClient)

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')
sample_document_item_404 = load_sample_data('documents_item_404.json')

class DummyModel(StandardModel):
    pass

class DummyResource(StandardResource[DummyModel]):
    model_class = DummyModel
    endpoints = {
        "list": Template("http://dummy/api/list"),
        "detail": Template("http://dummy/api/detail/$id"),
    }
    client = MockClient

    def __init__(self):
        self.name = "dummy"

class TestQuerySetFilterBase(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})


class TestUpdateFilters(TestQuerySetFilterBase):
    def test_update_filters(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")
        self.qs._update_filters({"new_filter": 123})
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 123})
        self.qs._update_filters({"another_new_filter": 456})
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 123, "another_new_filter": 456})
        self.qs._update_filters({"new_filter": 789})
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 789, "another_new_filter": 456})

class TestChain(TestQuerySetFilterBase):
    def test_chain_no_parms(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test no params
        qs2 = self.qs._chain()
        self.assertIsInstance(qs2, StandardQuerySet, "chain did not return a queryset instance")
        self.assertIsNot(qs2, self.qs, "chain did not return a NEW queryset")
        self.assertEqual(qs2.filters, {"init": "value"}, "chain modified the original filters")

        # Do it again for qs2
        qs3 = qs2._chain()
        self.assertIsInstance(qs3, StandardQuerySet, "chain did not return a queryset instance")
        self.assertIsNot(qs3, qs2, "chain did not return a NEW queryset")
        self.assertEqual(qs3.filters, {"init": "value"}, "chain modified the original filters on the second chain")

    def test_chain_one_parm(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test new filter
        qs3 = self.qs._chain(filters={"new_filter": 123})
        self.assertIsInstance(qs3, StandardQuerySet, "chain did not return a queryset instance when filters were passed")
        self.assertIsNot(qs3, self.qs, "chain did not return a NEW queryset when filters were passed")
        self.assertEqual(qs3.filters, {"init": "value", "new_filter": 123}, "chain did not add new filters correctly")

        # Do it again for qs3
        qs4 = qs3._chain(filters={"another_new_filter": 456})
        self.assertIsInstance(qs4, StandardQuerySet, "chain did not return a queryset instance when filters were passed")
        self.assertIsNot(qs4, qs3, "chain did not return a NEW queryset when filters were passed")
        self.assertEqual(qs4.filters, {"init": "value", "new_filter": 123, "another_new_filter": 456}, "chain did not add new filters correctly")

    def test_chain_multiple_params(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test 2 new filters
        qs4 = self.qs._chain(filters={"another_new_filter": 456, "third_new_filter": 123})
        self.assertIsInstance(qs4, StandardQuerySet, "chain did not return a queryset instance when 2 filters were passed")
        self.assertIsNot(qs4, self.qs, "chain did not return a NEW queryset when 2 filters were passed")
        self.assertEqual(qs4.filters, {"init": "value", "another_new_filter": 456, "third_new_filter": 123}, "chain did not add 2 new filters correctly")

        # Do it again for qs4
        qs5 = qs4._chain(filters={"fourth_new_filter": 789, "fifth_new_filter": 101112})
        self.assertIsInstance(qs5, StandardQuerySet, "chain did not return a queryset instance when 2 filters were passed")
        self.assertIsNot(qs5, qs4, "chain did not return a NEW queryset when 2 filters were passed")
        self.assertEqual(qs5.filters, {"init": "value", "another_new_filter": 456, "third_new_filter": 123, "fourth_new_filter": 789, "fifth_new_filter": 101112}, "chain did not add 2 new filters correctly")

    def test_chain_update_filter(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")
        # Test update filter
        qs5 = self.qs._chain(filters={"init": "new_value"})
        self.assertIsInstance(qs5, StandardQuerySet, "chain did not return a queryset instance when updating a filter")
        self.assertIsNot(qs5, self.qs, "chain did not return a NEW queryset when updating a filter")
        self.assertEqual(qs5.filters, {"init": "new_value"}, "chain did not update the filter correctly")

        # Do it again for qs5
        qs6 = qs5._chain(filters={"init": "another_new_value"})
        self.assertIsInstance(qs6, StandardQuerySet, "chain did not return a queryset instance when updating a filter")
        self.assertIsNot(qs6, qs5, "chain did not return a NEW queryset when updating a filter")
        self.assertEqual(qs6.filters, {"init": "another_new_value"}, "chain did not update the filter correctly")

class TestFilter(TestQuerySetFilterBase):
    def test_filter_returns_new_queryset(self):
        qs2 = self.qs.filter(new_filter=123)
        self.assertIsNot(qs2, self.qs)
        expected = {"init": "value", "new_filter": 123}
        self.assertEqual(qs2.filters, expected)

class TestExclude(TestQuerySetFilterBase):
    def test_exclude_returns_new_queryset(self):
        qs2 = self.qs.exclude(field=1, title__contains="invoice")
        expected = {"init": "value", "field__not": 1, "title__not_contains": "invoice"}
        self.assertEqual(qs2.filters, expected)

class TestQuerySetGetNoCache(DocumentTest):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = StandardQuerySet(self.resource)

    def test_get_with_id(self):
        doc_id = sample_document["id"]
        result = self.qs.get(doc_id)
        self.assertIsInstance(result, Document)
        self.assertEqual(result.id, doc_id)
        self.assertEqual(result.title, sample_document["title"])

class TestQuerySetGetNoCacheFailure(DocumentTest):
    def setUp(self):
        super().setUp()
        self.qs = StandardQuerySet(self.resource)

    @patch("paperap.client.PaperlessClient.request")
    def test_get_with_id(self, mock_request):
        mock_request.return_value = sample_document_item_404
        with self.assertRaises(ObjectNotFoundError):
            self.qs.get(999999)

class TestQuerySetGetCache(DocumentTest):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = StandardQuerySet(self.resource)

        self.modified_doc_id = 1337
        self.modified_doc_title = "Paperap Unit Test - Modified Title"
        self.modified_document = MagicMock(spec=Document)
        self.modified_document.id = self.modified_doc_id
        self.modified_document.title = self.modified_doc_title
        self.qs._result_cache = [self.modified_document]

    def test_get_with_id(self):
        result = self.qs.get(self.modified_doc_id)
        self.assertIsInstance(result, Document)
        self.assertEqual(result.id, self.modified_doc_id)
        self.assertEqual(result.title, self.modified_doc_title)

class TestQuerySetGetCacheFailure(DocumentTest):
    def setUp(self):
        super().setUp()
        self.qs = StandardQuerySet(self.resource)

        self.modified_doc_id = 1337
        self.modified_doc_title = "Paperap Unit Test - Modified Title"
        self.modified_document = MagicMock(spec=Document)
        self.modified_document.id = self.modified_doc_id
        self.modified_document.title = self.modified_doc_title
        self.qs._result_cache = [self.modified_document]

    @patch("paperap.client.PaperlessClient.request")
    def test_get_with_id(self, mock_request):
        mock_request.return_value = sample_document_item_404
        with self.assertRaises(ObjectNotFoundError):
            self.qs.get(999999)

class TestQuerySetAll(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_all_returns_copy(self):
        qs_all = self.qs.all()
        self.assertIsNot(qs_all, self.qs)
        self.assertEqual(qs_all.filters, self.qs.filters)


class TestQuerySetOrderBy(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_order_by(self):
        qs_ordered = self.qs.order_by("name", "-date")
        expected_order = "name,-date"
        self.assertEqual(qs_ordered.filters.get("ordering"), expected_order)

class TestQuerySetFirst(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_first_with_cache(self):
        self.qs._result_cache = ["first", "second"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertEqual(self.qs.first(), "first")

    def test_first_without_cache(self):
        with patch.object(self.qs, "_chain", return_value=iter(["chain_item"])) as mock_chain:
            self.qs._result_cache = []
            result = self.qs.first()
            self.assertEqual(result, "chain_item")
            mock_chain.assert_called_once()

class TestQuerySetLast(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_last(self):
        self.qs._result_cache = ["first", "middle", "last"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertEqual(self.qs.last(), "last")
        self.qs._result_cache = []
        self.assertIsNone(self.qs.last())

class TestQuerySetExists(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_exists(self):
        self.qs._result_cache = ["exists"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertTrue(self.qs.exists())
        self.qs._result_cache = []
        self.assertFalse(self.qs.exists())

class TestQuerySetIter(TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_iter_with_fully_fetched_cache(self):
        self.qs._result_cache = ["a", "b"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        result = list(iter(self.qs))
        self.assertEqual(result, ["a", "b"])

class TestQuerySetGetItem(TestCase):
    def setUp(self):
        super().setUp()
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_getitem_index_cached(self):
        self.qs._result_cache = ["zero", "one", "two"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertEqual(self.qs[1], "one")

    @patch.object(QuerySet, "_chain", return_value=iter(["fetched_item"]))
    def test_getitem_index_not_cached(self, mock_chain):
        # Reset filters to empty so that the expected filters match.
        self.qs.filters = {}
        self.qs._result_cache = []
        result = self.qs[5]
        self.assertEqual(result, "fetched_item")
        mock_chain.assert_called_once_with(filters={'limit': 1, 'offset': 5})

    def test_getitem_index_negative(self):
        self.qs._result_cache = ["a", "b", "c"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertEqual(self.qs[-1], "c")

    def test_getitem_slice_positive(self):
        # Use a fresh QuerySet with empty filters to test slicing optimization.
        qs_clone = StandardQuerySet(self.resource, filters={})
        with patch.object(qs_clone, "_chain", return_value=iter(["item1", "item2"])) as mock_chain:
            qs_clone._result_cache = []  # force using _chain
            result = qs_clone[0:2]
            self.assertEqual(result, ["item1", "item2"])
            mock_chain.assert_called_once_with(filters={'limit': 2})

    def test_getitem_slice_negative(self):
        self.qs._result_cache = ["a", "b", "c", "d"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        result = self.qs[1:-1]
        self.assertEqual(result, ["b", "c"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
