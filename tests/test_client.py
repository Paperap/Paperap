"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    test_client.py                                                                                       *
*        Project: tests                                                                                                *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""
import json
from typing import Iterator
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from paperwrap.tests import TestCase, load_sample_data
from paperwrap.models.queryset import QuerySet
from paperwrap.models.document import Document
from paperwrap.models.tag import Tag
from paperwrap.client import PaperlessClient

# Load sample response from tests/sample_data/documents_list.json
sample_data = load_sample_data('documents_list.json')

class TestClient(TestCase):
    def setUp(self):
        self.client = PaperlessClient()

    @patch("paperwrap.client.PaperlessClient.request")
    def test_get_documents(self, mock_request):
        mock_request.return_value = sample_data
        documents = self.client.documents()
        self.assertIsInstance(documents, QuerySet)
        total = documents.count()
        self.assertEqual(total, sample_data['count'], "Count of documents incorrect")
        total_on_page = documents.count_this_page()
        self.assertEqual(total_on_page, len(sample_data['results']), "Count of documents on this page incorrect")

        count = 0
        # Ensure paging works (twice), then break
        test_iterations = (total_on_page * 2) + 2
        for document in documents:
            count += 1
            self.assertIsInstance(document, Document, f"Expected Document, got {type(document)}")
            self.assertIsInstance(document.id, int, f"Document id is wrong type: {type(document.id)}")
            self.assertIsInstance(document.title, str, f"Document title is wrong type: {type(document.title)}")
            if document.correspondent:
                self.assertIsInstance(document.correspondent, int, f"Document correspondent is wrong type: {type(document.correspondent)}")
            self.assertIsInstance(document.document_type, int, f"Document document_type is wrong type: {type(document.document_type)}")
            self.assertIsInstance(document.tags, list, f"Document tags is wrong type: {type(document.tags)}")

            for tag in document.tags:
                self.assertIsInstance(tag, int, f"Document tag is wrong type: {type(tag)}")

            # Ensure paging works (twice), then break
            if count >= test_iterations:
                break

        self.assertEqual(count, test_iterations, f"Document queryset did not iterate over 3 pages.")

if __name__ == "__main__":
    unittest.main()
