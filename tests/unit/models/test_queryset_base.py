

from __future__ import annotations

import logging
import os
import unittest
from datetime import datetime
from string import Template
from typing import override
from unittest.mock import MagicMock, patch

from paperap.client import PaperlessClient

# Import the exceptions used by BaseQuerySet.
from paperap.exceptions import MultipleObjectsFoundError, ObjectNotFoundError, ResponseParsingError
from paperap.models import BaseQuerySet, StandardModel
from paperap.models.abstract.queryset import StandardQuerySet
from paperap.models.document import Document
from paperap.resources import BaseResource, StandardResource
from paperap.resources.documents import DocumentResource
from tests.lib import DocumentUnitTest, UnitTestCase, load_sample_data
from tests.lib.factories import DocumentFactory, PydanticFactory

MockClient = MagicMock(PaperlessClient)

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')
sample_document_item_404 = load_sample_data('documents_item_404.json')

class DummyModel(StandardModel):
    a_str : str | None = None
    an_int : int | None = None
    a_datetime : datetime | None = None
    a_list_str : list[str] = []
    a_list_int : list[int] = []

class DummyResource(StandardResource[DummyModel]):
    model_class = DummyModel
    endpoints = {
        "list": Template("http://dummy/api/list"),
        "detail": Template("http://dummy/api/detail/$id"),
    }

class DummyFactory(PydanticFactory[DummyModel]):
    a_str = "some string"
    an_int = 5
    a_datetime = datetime.now()
    a_list_str = ["a", "b", "c"]
    a_list_int = [1, 2, 3]

    class Meta: # type: ignore
        model = DummyModel

class TestQuerySetFilterBase(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

class TestUpdateFilters(TestQuerySetFilterBase):
    def test_update_filters(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")
        self.qs._update_filters({"new_filter": 123}) # type: ignore
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 123})
        self.qs._update_filters({"another_new_filter": 456}) # type: ignore
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 123, "another_new_filter": 456})
        self.qs._update_filters({"new_filter": 789}) # type: ignore
        self.assertEqual(self.qs.filters, {"init": "value", "new_filter": 789, "another_new_filter": 456})

class TestChain(TestQuerySetFilterBase):
    def test_chain_no_parms(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test no params
        qs2 = self.qs._chain()  # type: ignore
        self.assertIsInstance(qs2, StandardQuerySet, "chain did not return a queryset instance")
        self.assertIsNot(qs2, self.qs, "chain did not return a NEW queryset")
        self.assertEqual(qs2.filters, {"init": "value"}, "chain modified the original filters")

        # Do it again for qs2
        qs3 = qs2._chain()  # type: ignore
        self.assertIsInstance(qs3, StandardQuerySet, "chain did not return a queryset instance")
        self.assertIsNot(qs3, qs2, "chain did not return a NEW queryset")
        self.assertEqual(qs3.filters, {"init": "value"}, "chain modified the original filters on the second chain")

    def test_chain_one_parm(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test new filter
        qs3 = self.qs._chain(filters={"new_filter": 123}) # type: ignore
        self.assertIsInstance(qs3, StandardQuerySet, "chain did not return a queryset instance when filters were passed")
        self.assertIsNot(qs3, self.qs, "chain did not return a NEW queryset when filters were passed")
        self.assertEqual(qs3.filters, {"init": "value", "new_filter": 123}, "chain did not add new filters correctly")

        # Do it again for qs3
        qs4 = qs3._chain(filters={"another_new_filter": 456}) # type: ignore
        self.assertIsInstance(qs4, StandardQuerySet, "chain did not return a queryset instance when filters were passed")
        self.assertIsNot(qs4, qs3, "chain did not return a NEW queryset when filters were passed")
        self.assertEqual(qs4.filters, {"init": "value", "new_filter": 123, "another_new_filter": 456}, "chain did not add new filters correctly")

    def test_chain_multiple_params(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")

        # Test 2 new filters
        qs4 = self.qs._chain(filters={"another_new_filter": 456, "third_new_filter": 123}) # type: ignore
        self.assertIsInstance(qs4, StandardQuerySet, "chain did not return a queryset instance when 2 filters were passed")
        self.assertIsNot(qs4, self.qs, "chain did not return a NEW queryset when 2 filters were passed")
        self.assertEqual(qs4.filters, {"init": "value", "another_new_filter": 456, "third_new_filter": 123}, "chain did not add 2 new filters correctly")

        # Do it again for qs4
        qs5 = qs4._chain(filters={"fourth_new_filter": 789, "fifth_new_filter": 101112}) # type: ignore
        self.assertIsInstance(qs5, StandardQuerySet, "chain did not return a queryset instance when 2 filters were passed")
        self.assertIsNot(qs5, qs4, "chain did not return a NEW queryset when 2 filters were passed")
        self.assertEqual(qs5.filters, {"init": "value", "another_new_filter": 456, "third_new_filter": 123, "fourth_new_filter": 789, "fifth_new_filter": 101112}, "chain did not add 2 new filters correctly")

    def test_chain_update_filter(self):
        self.assertEqual(self.qs.filters, {"init": "value"}, "test assumptions failed")
        # Test update filter
        qs5 = self.qs._chain(filters={"init": "new_value"}) # type: ignore
        self.assertIsInstance(qs5, StandardQuerySet, "chain did not return a queryset instance when updating a filter")
        self.assertIsNot(qs5, self.qs, "chain did not return a NEW queryset when updating a filter")
        self.assertEqual(qs5.filters, {"init": "new_value"}, "chain did not update the filter correctly")

        # Do it again for qs5
        qs6 = qs5._chain(filters={"init": "another_new_value"}) # type: ignore
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

class TestQuerySetGetNoCache(DocumentUnitTest):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = StandardQuerySet(self.resource)

    def __disabled_test_get_with_id(self):
        doc_id = sample_document["id"]
        result = self.qs.get(doc_id)
        self.assertIsInstance(result, Document)
        self.assertEqual(result.id, doc_id)
        self.assertEqual(result.title, sample_document["title"])

class TestQuerySetGetNoCacheFailure(DocumentUnitTest):
    @override
    def setUp(self):
        super().setUp()
        self.qs = StandardQuerySet(self.resource)

    @patch("paperap.client.PaperlessClient.request")
    def test_get_with_id(self, mock_request):
        mock_request.return_value = sample_document_item_404
        with self.assertRaises(ObjectNotFoundError):
            self.qs.get(999999)

class TestQuerySetGetCache(DocumentUnitTest):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = StandardQuerySet(self.resource)

        self.modified_doc_id = 1337
        self.modified_doc_title = "Paperap Unit Test - Modified Title"
        self.modified_document = DocumentFactory.create(id=self.modified_doc_id, title=self.modified_doc_title)
        self.qs._result_cache = [self.modified_document] # type: ignore

    def test_get_with_id(self):
        result = self.qs.get(self.modified_doc_id)
        self.assertIsInstance(result, Document)
        self.assertEqual(result.id, self.modified_doc_id)
        self.assertEqual(result.title, self.modified_doc_title)

class TestQuerySetGetCacheFailure(DocumentUnitTest):
    @override
    def setUp(self):
        super().setUp()
        self.qs = StandardQuerySet(self.resource)

        self.modified_doc_id = 1337
        self.modified_doc_title = "Paperap Unit Test - Modified Title"
        self.modified_document = DocumentFactory.create(id=self.modified_doc_id, title=self.modified_doc_title)
        self.qs._result_cache = [self.modified_document] # type: ignore

    @patch("paperap.client.PaperlessClient.request")
    def test_get_with_id(self, mock_request):
        mock_request.return_value = sample_document_item_404
        with self.assertRaises(ObjectNotFoundError):
            self.qs.get(999999)

class TestQuerySetAll(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_all_returns_copy(self):
        qs_all = self.qs.all()
        self.assertIsNot(qs_all, self.qs)
        self.assertEqual(qs_all.filters, self.qs.filters)

class TestQuerySetOrderBy(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_order_by(self):
        qs_ordered = self.qs.order_by("name", "-date")
        expected_order = "name,-date"
        self.assertEqual(qs_ordered.filters.get("ordering"), expected_order)

class TestQuerySetFirst(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_first_with_cache(self):
        self.qs._result_cache = ["first", "second"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        self.assertEqual(self.qs.first(), "first")

    def test_first_without_cache(self):
        with patch("paperap.models.abstract.queryset.BaseQuerySet._chain", return_value=iter(["chain_item"])) as mock_chain:
            qs = StandardQuerySet(resource=self.resource, filters={})
            qs._result_cache = [] # type: ignore
            result = qs.first()
            self.assertEqual(result, "chain_item")
            mock_chain.assert_called_once()

class TestQuerySetLast(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_last(self):
        self.qs._result_cache = ["first", "middle", "last"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        self.assertEqual(self.qs.last(), "last")
        self.qs._result_cache = [] # type: ignore
        self.assertIsNone(self.qs.last())

class TestQuerySetExists(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_exists(self):
        self.qs._result_cache = ["exists"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        self.assertTrue(self.qs.exists())
        self.qs._result_cache = [] # type: ignore
        self.assertFalse(self.qs.exists())

class TestQuerySetIter(UnitTestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        super().setUp()
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    """
    # Expect this test to work after QuerySet is a pydantic model (i.e. has validation on attributes)
    def test_iter_raises_parsing_error(self):
        # Set the result cache to a bad type
        self.qs._result_cache = ["a", "b"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        with self.assertRaises(ResponseParsingError):
            list(iter(self.qs))
    """

    def test_iter_with_fully_fetched_cache(self):
        # Create proper mock objects instead of strings
        mock_models = [DummyFactory.create() for _ in range(2)]
        self.qs._result_cache = mock_models  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore

        with patch.object(self.client, "request") as mock_request:
            mock_request.return_value = None
            result = list(iter(self.qs))
            # Ensure request is never called
            mock_request.assert_not_called()

        self.assertEqual(result, mock_models)

    @patch("paperap.models.abstract.queryset.StandardQuerySet._request_iter")
    def __disabled_test_iter_with_pagination(self, mock_request_iter):
        """Test iteration with pagination."""
        # TODO: AI Generated Test
        # Setup mock to return different results for first and second page
        first_page_results = [DummyFactory.create() for _ in range(2)]
        second_page_results = [DummyFactory.create() for _ in range(2)]

        # Configure the mock to return different iterators for different calls
        mock_request_iter.side_effect = [
            iter(first_page_results),
            iter(second_page_results)
        ]

        # Setup pagination
        self.qs._result_cache = []  # type: ignore
        self.qs._fetch_all = False  # type: ignore
        self.qs._next_url = "http://example.com/api/next-page" # type: ignore
        self.qs._last_response = sample_document_list # type: ignore

        # Get all results
        results = list(self.qs)

        # Verify results
        self.assertEqual(len(results), 4)
        self.assertEqual(results, first_page_results + second_page_results)

        # Verify _request_iter was called twice (once for each page)
        self.assertEqual(mock_request_iter.call_count, 2)

        # Verify _fetch_all is True after all pages are fetched
        self.assertTrue(self.qs._fetch_all) # type: ignore

class TestQuerySetGetItem(UnitTestCase):
    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = StandardQuerySet(self.resource, filters={"init": "value"})

    def test_getitem_index_cached(self):
        self.qs._result_cache = ["zero", "one", "two"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        self.assertEqual(self.qs[1], "one")

    @patch("paperap.models.abstract.queryset.BaseQuerySet._chain", return_value=iter(["fetched_item"]))
    def test_getitem_index_not_cached(self, mock_chain):
        # Reset filters to empty so that the expected filters match.
        qs = StandardQuerySet(resource=self.resource, filters={})
        qs.filters = {}
        qs._result_cache = [] # type: ignore
        result = qs[5]
        self.assertEqual(result, "fetched_item")
        mock_chain.assert_called_once_with(filters={'limit': 1, 'offset': 5})

    def test_getitem_index_negative(self):
        self.qs._result_cache = ["a", "b", "c"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        self.assertEqual(self.qs[-1], "c")

    def test_getitem_slice_positive(self):
        # Use a fresh BaseQuerySet with empty filters to test slicing optimization.
        qs_clone = StandardQuerySet(self.resource, filters={})
        with patch.object(qs_clone, "_chain", return_value=iter(["item1", "item2"])) as mock_chain:
            qs_clone._result_cache = [] # type: ignore # force using _chain
            result = qs_clone[0:2]
            self.assertEqual(result, ["item1", "item2"])
            mock_chain.assert_called_once_with(filters={'limit': 2})

    def test_getitem_slice_negative(self):
        self.qs._result_cache = ["a", "b", "c", "d"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True # type: ignore
        result = self.qs[1:-1]
        self.assertEqual(result, ["b", "c"])

    @patch("paperap.models.abstract.queryset.BaseQuerySet._chain")
    def test_getitem_index_not_cached_empty_result(self, mock_chain):
        """Test that accessing an index with no results raises IndexError."""
        mock_chain.return_value = iter([])  # Empty result
        self.qs._result_cache = [] # type: ignore

        with self.assertRaises(IndexError):
            _ = self.qs[0]

class TestContains(UnitTestCase):

    """Test the __contains__ method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch("paperap.models.abstract.queryset.StandardQuerySet.__iter__")
    def test_contains_with_model(self, mock_iter):
        """Test checking if a model is in the queryset."""
        # Create a model and a mock iterator that returns it
        model = DummyFactory.create()
        mock_iter.return_value = iter([model])

        # Check if the model is in the queryset
        self.assertTrue(model in self.qs)

    @patch.object(StandardQuerySet, "__iter__")
    def test_contains_with_non_model(self, mock_iter):
        """Test checking if a non-model is in the queryset."""
        # Create a non-model object
        non_model = "not a model"

        # Check if the non-model is in the queryset
        self.assertFalse(non_model in self.qs)
        # Verify __iter__ was not called
        mock_iter.assert_not_called()

    @patch.object(StandardQuerySet, "__iter__")
    def test_contains_with_id(self, mock_iter):
        """Test checking if a model ID is in the queryset."""
        # Create models with different IDs
        model1 = DummyFactory.create()
        model1.id = 1
        model2 = DummyFactory.create()
        model2.id = 2

        mock_iter.return_value = iter([model1, model2])

        # Check if the ID is in the queryset
        self.assertTrue(1 in self.qs)


class TestRequestIter(UnitTestCase):

    """Test the _request_iter method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch.object(DummyResource, "request_raw")
    @patch.object(DummyResource, "handle_response")
    def test_request_iter_with_url(self, mock_handle_response, mock_request_raw):
        """Test requesting with a specific URL."""
        # Setup mocks
        mock_request_raw.return_value = {"results": [{"id": 1}, {"id": 2}]}
        mock_handle_response.return_value = iter([DummyFactory.create()])

        # Call _request_iter with a URL
        url = "http://example.com/api/endpoint"
        results = list(self.qs._request_iter(url=url)) # type: ignore

        # Verify request_raw was called with the URL
        mock_request_raw.assert_called_once_with(url=url, params=None)

        # Verify handle_response was called with the response
        mock_handle_response.assert_called_once_with(mock_request_raw.return_value)

        # Verify results
        self.assertEqual(len(results), 1)

    @patch.object(DummyResource, "request_raw")
    def test_request_iter_no_response(self, mock_request_raw):
        """Test requesting with no response."""
        # Setup mock to return None
        mock_request_raw.return_value = None

        # Call _request_iter
        results = list(self.qs._request_iter()) # type: ignore

        # Verify request_raw was called
        mock_request_raw.assert_called_once()

        # Verify no results
        self.assertEqual(len(results), 0)


class TestGetNext(UnitTestCase):

    """Test the _get_next method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    def test_get_next_with_next_url(self):
        """Test getting the next URL from a response with a next URL."""
        # Create a response with a next URL
        response = {"next": "http://example.com/api/next-page"}

        # Get the next URL
        next_url = self.qs._get_next(response) # type: ignore

        # Verify the next URL
        self.assertEqual(next_url, "http://example.com/api/next-page")
        self.assertEqual(self.qs._next_url, "http://example.com/api/next-page") # type: ignore
        self.assertEqual(self.qs._urls_fetched, ["http://example.com/api/next-page"]) # type: ignore

    def test_get_next_without_next_url(self):
        """Test getting the next URL from a response without a next URL."""
        # Create a response without a next URL
        response = {"results": []}

        # Get the next URL
        next_url = self.qs._get_next(response) # type: ignore

        # Verify no next URL
        self.assertIsNone(next_url)
        self.assertIsNone(self.qs._next_url) # type: ignore

    def test_get_next_with_already_fetched_url(self):
        """Test getting the next URL when it's already been fetched."""
        # Set up a URL that's already been fetched
        self.qs._urls_fetched = ["http://example.com/api/next-page"] # type: ignore

        # Create a response with the same next URL
        response = {"next": "http://example.com/api/next-page"}

        # Get the next URL
        next_url = self.qs._get_next(response) # type: ignore

        # Verify no next URL is returned
        self.assertIsNone(next_url)
        self.assertIsNone(self.qs._next_url) # type: ignore


class TestReset(UnitTestCase):

    """Test the _reset method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    def test_reset(self):
        """Test resetting the queryset."""
        # Set up the queryset with some data
        self.qs._result_cache = ["a", "b"]  # type: ignore
        self.qs._fetch_all = True  # type: ignore
        self.qs._next_url = "http://example.com/api/next-page" # type: ignore
        self.qs._urls_fetched = ["http://example.com/api/page-1"] # type: ignore
        self.qs._last_response = {"results": []} # type: ignore
        self.qs._iter = iter([])  # type: ignore

        # Reset the queryset
        self.qs._reset() # type: ignore

        # Verify all attributes are reset
        self.assertEqual(self.qs._result_cache, []) # type: ignore
        self.assertFalse(self.qs._fetch_all) # type: ignore
        self.assertIsNone(self.qs._next_url) # type: ignore
        self.assertEqual(self.qs._urls_fetched, []) # type: ignore
        self.assertIsNone(self.qs._last_response) # type: ignore
        self.assertIsNone(self.qs._iter) # type: ignore


class TestFetchAllResults(UnitTestCase):

    """Test the _fetch_all_results method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch.object(StandardQuerySet, "_request_iter")
    def test_fetch_all_results_already_fetched(self, mock_request_iter):
        """Test fetching all results when they're already fetched."""
        # Set up the queryset as already fetched
        self.qs._fetch_all = True  # type: ignore

        # Call _fetch_all_results
        self.qs._fetch_all_results() # type: ignore

        # Verify _request_iter was not called
        mock_request_iter.assert_not_called()

    @patch.object(StandardQuerySet, "_request_iter")
    def test_fetch_all_results_single_page(self, mock_request_iter):
        """Test fetching all results with a single page."""
        # Set up mock to return a single page with no next URL
        results = [DummyFactory.create() for _ in range(2)]
        mock_request_iter.return_value = iter(results)
        self.qs._last_response = {"results": results, "next": None} # type: ignore

        # Call _fetch_all_results
        self.qs._fetch_all_results() # type: ignore

        # Verify _request_iter was called once
        mock_request_iter.assert_called_once_with(params=self.qs.filters)

        # Verify results were cached
        self.assertEqual(self.qs._result_cache, results) # type: ignore

        # Verify _fetch_all is True
        self.assertTrue(self.qs._fetch_all) # type: ignore

    @patch.object(StandardQuerySet, "_request_iter")
    def test_fetch_all_results_multiple_pages(self, mock_request_iter):
        """Test fetching all results with multiple pages."""
        # Set up mock to return multiple pages
        page1_results = [DummyFactory.create() for _ in range(2)]
        page2_results = [DummyFactory.create() for _ in range(2)]

        # Function to mock _request_iter behavior dynamically
        def mock_request_iter_side_effect(*args, **kwargs):
            if self.qs._next_url == "http://example.com/api/next-page": # type: ignore
                # Simulate another page
                self.qs._next_url = "http://example.com/api/final-page"  # type: ignore
                return iter(page1_results)
            elif self.qs._next_url == "http://example.com/api/final-page": # type: ignore
                # Simulate last page, stop pagination
                self.qs._next_url = None  # type: ignore
                return iter(page2_results)
            # No more pages
            return iter([])

        mock_request_iter.side_effect = mock_request_iter_side_effect

        # Set up pagination
        self.qs._next_url = "http://example.com/api/next-page"  # type: ignore
        self.qs._last_response = sample_document_list  # type: ignore

        # Call _fetch_all_results
        self.qs._fetch_all_results()  # type: ignore

        # Verify _request_iter was called twice
        self.assertEqual(mock_request_iter.call_count, 2)

        # Verify results were cached
        self.assertEqual(self.qs._result_cache, page1_results + page2_results)  # type: ignore

        # Verify _fetch_all is True
        self.assertTrue(self.qs._fetch_all)  # type: ignore



class TestNone(UnitTestCase):

    """Test the none method."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch.object(StandardQuerySet, "_chain")
    def test_none(self, mock_chain):
        """Test getting an empty queryset."""
        # Call none
        self.qs.none()

        # Verify _chain was called with limit=0
        mock_chain.assert_called_once_with(filters={"limit": 0})


class TestFilterFieldByStr(UnitTestCase):

    """Test the filter_field_by_str method."""

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch.object(StandardQuerySet, "filter")
    def test_filter_field_by_str_exact_case_sensitive(self, mock_filter):
        """Test filtering by exact match, case sensitive."""
        # Call filter_field_by_str
        self.qs.filter_field_by_str("name", "test", exact=True, case_insensitive=False)

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(name="test")

    @patch.object(StandardQuerySet, "filter")
    def test_filter_field_by_str_exact_case_insensitive(self, mock_filter):
        """Test filtering by exact match, case insensitive."""
        # Call filter_field_by_str
        self.qs.filter_field_by_str("name", "test", exact=True, case_insensitive=True)

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(name__iexact="test")

    @patch.object(StandardQuerySet, "filter")
    def test_filter_field_by_str_contains_case_sensitive(self, mock_filter):
        """Test filtering by contains, case sensitive."""
        # Call filter_field_by_str
        self.qs.filter_field_by_str("name", "test", exact=False, case_insensitive=False)

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(name__contains="test")

    @patch.object(StandardQuerySet, "filter")
    def test_filter_field_by_str_contains_case_insensitive(self, mock_filter):
        """Test filtering by contains, case insensitive."""
        # Call filter_field_by_str
        self.qs.filter_field_by_str("name", "test", exact=False, case_insensitive=True)

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(name__icontains="test")


class TestStandardQuerySetMethods(UnitTestCase):

    """Test the StandardQuerySet-specific methods."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this comment when they are removed.

    @override
    def setUp(self):
        super().setUp()
        self.resource = DummyResource(client=self.client)
        self.qs = StandardQuerySet(self.resource)

    @patch.object(StandardQuerySet, "filter")
    def test_id_with_single_id(self, mock_filter):
        """Test filtering by a single ID."""
        # Call id
        self.qs.id(1)

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(id=1)

    @patch.object(StandardQuerySet, "filter")
    def test_id_with_list_of_ids(self, mock_filter):
        """Test filtering by a list of IDs."""
        # Call id
        self.qs.id([1, 2, 3])

        # Verify filter was called with the correct arguments
        mock_filter.assert_called_once_with(id__in=[1, 2, 3])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
