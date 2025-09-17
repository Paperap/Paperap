
from __future__ import annotations

import logging
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, override
from unittest.mock import MagicMock, patch
import tempfile
from paperap.client import PaperlessClient
from paperap.exceptions import ReadOnlyFieldError, ResourceNotFoundError, APIError
from paperap.models import *
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.documents import DocumentResource
from tests.lib import DocumentUnitTest, load_sample_data

logger = logging.getLogger(__name__)

class IntegrationTest(DocumentUnitTest):
    mock_env = False

    @override
    def setup_client(self):
        url = os.getenv("PAPERLESS_REAL_BASE_URL")
        token = os.getenv("PAPERLESS_REAL_TOKEN")
        self.client = PaperlessClient(
            url=url,
            token=token
        )

class TestList(IntegrationTest):
    def test_signin(self):
        documents = self.client.documents().document_type("Guest Sign-In")
        self.assertIsInstance(documents, DocumentQuerySet, "Expected a DocumentQuerySet when filtering by document type")
        count = documents.count()
        self.assertEqual(count, 108, "Expected 108 documents of type Guest Sign-In")
        total = len(documents)
        self.assertEqual(total, 108, "Count correct, but len wrong. Expected 108 documents of type Guest Sign-In")
        i = 0
        for document in documents:
            i += 1
            self.assertIsInstance(document, Document, "Expected document to be an instance of Document")
            self.assertEqual(document.document_type_id, 31, "Expected document type id to be 31 for Guest Sign-In")
            self.assertEqual(document.document_type.name, "Guest Sign-In", "Expected document type name to be Guest Sign-In")

        self.assertEqual(i, 108, "Count and len correct, but did not iterate over 108 documents")

if __name__ == "__main__":
    unittest.main()