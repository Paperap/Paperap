"""*****************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* ----------------------------------------------------------------------------                                         *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    test_queryset.py                                                                                     *
*        Project: paperap                                                                                              *
*        Created: 2025-03-04                                                                                           *
*        Version: <<version>>                                                                                          *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* ----------------------------------------------------------------------------                                         *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-04     By Jess Mann                                                                                   *
*                                                                                                                      *
*****************************************************************************"""
"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    test_queryset.py                                                                                     *
*        Project: models                                                                                               *
*        Created: 2025-03-03                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-03     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""
import logging
from string import Template
import unittest
from unittest.mock import MagicMock, patch

# Import the exceptions used by QuerySet.
from paperap.exceptions import ObjectNotFoundError, MultipleObjectsFoundError
from paperap.models import PaperlessModel, QuerySet
from paperap.models.document import Document
from paperap.resources import PaperlessResource
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.tests import load_sample_data, TestCase

MockClient = MagicMock(PaperlessClient)

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')
sample_document_item_404 = load_sample_data('documents_item_404.json')

class DummyModel(PaperlessModel):
    pass

class DummyResource(PaperlessResource[DummyModel]):
    model_class = DummyModel
    endpoints = {
        "list": Template("http://dummy/api/list"),
        "detail": Template("http://dummy/api/detail/$id"),
    }
    client = MockClient

    def __init__(self):
        self.name = "dummy"

class TestQuerySetFilter(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_filter_returns_new_queryset(self):
        qs2 = self.qs.filter(new_filter=123)
        self.assertIsNot(qs2, self.qs)
        expected = {"init": "value", "new_filter": 123}
        self.assertEqual(qs2.filters, expected)

    def test_exclude_returns_new_queryset(self):
        qs2 = self.qs.exclude(field=1, title__contains="invoice")
        expected = {"init": "value", "field__not": 1, "title__not_contains": "invoice"}
        self.assertEqual(qs2.filters, expected)

class TestQuerySetGetNoCache(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = QuerySet(self.resource)

    def test_get_with_id(self):
        doc_id = sample_document["id"]
        result = self.qs.get(doc_id)
        self.assertIsInstance(result, Document)
        self.assertEqual(result.id, doc_id)
        self.assertEqual(result.title, sample_document["title"])

class TestQuerySetGetNoCacheFailure(unittest.TestCase):
    def setUp(self):
        self.client = PaperlessClient()
        self.resource = DocumentResource(self.client)
        self.qs = QuerySet(self.resource)

    @patch("paperap.client.PaperlessClient.request")
    def test_get_with_id(self, mock_request):
        mock_request.return_value = sample_document_item_404
        with self.assertRaises(ObjectNotFoundError):
            self.qs.get(999999)

class TestQuerySetGetCache(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        mock_request.return_value = sample_document
        self.resource = DocumentResource(MockClient)
        self.resource.client.request = mock_request
        self.qs = QuerySet(self.resource)

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

class TestQuerySetGetCacheFailure(unittest.TestCase):
    def setUp(self):
        self.client = PaperlessClient()
        self.resource = DocumentResource(self.client)
        self.qs = QuerySet(self.resource)

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

class TestQuerySetAll(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_all_returns_copy(self):
        qs_all = self.qs.all()
        self.assertIsNot(qs_all, self.qs)
        self.assertEqual(qs_all.filters, self.qs.filters)


class TestQuerySetOrderBy(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_order_by(self):
        qs_ordered = self.qs.order_by("name", "-date")
        expected_order = "name,-date"
        self.assertEqual(qs_ordered.filters.get("ordering"), expected_order)

class TestQuerySetFirst(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

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

class TestQuerySetLast(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_last(self):
        self.qs._result_cache = ["first", "middle", "last"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertEqual(self.qs.last(), "last")
        self.qs._result_cache = []
        self.assertIsNone(self.qs.last())

class TestQuerySetExists(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_exists(self):
        self.qs._result_cache = ["exists"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        self.assertTrue(self.qs.exists())
        self.qs._result_cache = []
        self.assertFalse(self.qs.exists())

class TestQuerySetIter(unittest.TestCase):
    @patch("paperap.client.PaperlessClient.request")
    def setUp(self, mock_request):
        self.mock_request = mock_request
        self.mock_request.return_value = sample_document_list
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

    def test_iter_with_fully_fetched_cache(self):
        self.qs._result_cache = ["a", "b"]  # type: ignore # Allow edit ClassVar in tests
        self.qs._fetch_all = True
        result = list(iter(self.qs))
        self.assertEqual(result, ["a", "b"])

    def test_request_iter_no_endpoint_raises(self):
        class DummyResourceNoEndpoint(PaperlessResource):
            model_class = MagicMock(spec=PaperlessModel).__class__
            endpoints = {}
        resource_no_endpoint = DummyResourceNoEndpoint(MagicMock())
        qs_no_endpoint = QuerySet(resource_no_endpoint)
        with self.assertRaises(ValueError):
            list(qs_no_endpoint._request_iter())

class TestQuerySetGetItem(unittest.TestCase):
    def setUp(self):
        self.resource = DummyResource()
        # Some tests expect a nonempty filter; others require an empty filter.
        # By default, we use a nonempty filter.
        self.qs = QuerySet(self.resource, filters={"init": "value"})

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
        qs_clone = QuerySet(self.resource, filters={})
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
