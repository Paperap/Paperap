"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_factories.py
        Project: paperap
        Created: 2025-03-12
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-12     By Jess Mann

"""
from __future__ import annotations

import os
from typing import Iterable, override
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from paperap.models.abstract.queryset import BaseQuerySet
from paperap.models.document import Document
from paperap.client import PaperlessClient
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag
from tests.lib import UnitTestCase, load_sample_data, DocumentUnitTest
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
