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