

from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from typing import Iterable, override
from unittest.mock import MagicMock, patch

from paperap.client import PaperlessClient
from paperap.models.abstract.queryset import BaseQuerySet
from paperap.models.document import Document
from paperap.models.tag import Tag
from paperap.resources.documents import DocumentResource
from tests.lib import DocumentUnitTest, UnitTestCase, load_sample_data
from tests.lib.factories import DocumentFactory

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class TestFactories(DocumentUnitTest):
    @override
    def setUp(self):
        super().__init__()
        self.factory = DocumentFactory # type: ignore

    def test_get_resource(self):
        self.assertIsInstance(self.factory.get_resource(), DocumentResource)
        self.assertEqual(self.factory._meta.model, Document) # type: ignore
