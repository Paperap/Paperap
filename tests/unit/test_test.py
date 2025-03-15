"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-12     By Jess Mann

"""
from __future__ import annotations

import copy
import os
from random import sample
from typing import Any, Iterable, List, Optional, override
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import logging
from datetime import datetime, timezone
from paperap.client import PaperlessClient
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models import *
from paperap.resources.documents import DocumentResource
from paperap.models.tag import Tag, TagQuerySet
from paperap.models.document.model import CustomFieldValues, CustomFieldTypedDict, DocumentNote
from tests.lib import load_sample_data, DocumentUnitTest, factories, TestConfigurationError, UnitTestCase

logger = logging.getLogger(__name__)

class TestUnitTestCase(DocumentUnitTest):
    @override
    def setUp(self):
        super().setUp()
        self.model = self.bake_model(**{
            "id": 1,
            "title": "Test Document",
            "storage_path": 1,
        })
        self.client.settings.save_on_write = False

    def test_default_patch(self):
        """Test that client.request is patched by default"""
        with self.assertRaises(TestConfigurationError):
            self.client.request("GET", "documents/1")
        
    def test_patch_request(self):
        """Test that the patch request method works as expected"""
        api_data = {'abc': 123}
        with self.assertRaises(TestConfigurationError):
            self.client.request("GET", "documents/1")
            
        with self.patch_request(**api_data):
            response = self.client.request("GET", "documents/1")
            self.assertEqual(response, api_data)

        with self.assertRaises(TestConfigurationError):
            self.client.request("GET", "documents/1")

    def test_patch_request_factory(self):
        """Test that the patch request method works as expected"""
        api_data = {'id': 1337}
        with self.assertRaises(TestConfigurationError):
            self.client.request("GET", "documents/1337")
            
        with self.patch_request_factory(**api_data):
            response = self.client.request("GET", "documents/1337")
            self.assertIn('title', response)
            self.assertEqual(response['id'], api_data['id'])

        with self.assertRaises(TestConfigurationError):
            self.client.request("GET", "documents/1337")

class TestFactories(UnitTestCase):
    def test_storagepath_api_data_noparams(self):
        api_data = factories.StoragePathFactory.create_api_data()
        # Must contain "name"
        self.assertIsInstance(api_data, dict)
        self.assertIn("name", api_data)
        self.assertIsNotNone(api_data["name"])

    def test_storagepath_api_data_id(self):
        api_data = factories.StoragePathFactory.create_api_data(id=1)
        self.assertEqual(api_data["id"], 1)
        # Must contain "name"
        self.assertIsInstance(api_data, dict)
        self.assertIn("name", api_data)
        self.assertIsNotNone(api_data["name"])