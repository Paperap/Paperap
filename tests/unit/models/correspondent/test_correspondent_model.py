"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    test_correspondent.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations

import os
from typing import Iterable, override
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from paperap.models.abstract.queryset import BaseQuerySet
from paperap.models.correspondent import Correspondent
from paperap.client import PaperlessClient
from paperap.resources.correspondents import CorrespondentResource
from paperap.models import Tag, DocumentQuerySet
from tests.lib import UnitTestCase, load_sample_data, CorrespondentUnitTest

sample_correspondent_list = load_sample_data('correspondents_list.json')
sample_correspondent = load_sample_data('correspondents_item.json')

class TestInit(CorrespondentUnitTest):

    def test_from_dict(self):
        model = Correspondent.from_dict(self.model_data_parsed)
        self.assertIsInstance(model, Correspondent, f"Expected Correspondent, got {type(model)}")
        self.assertEqual(model.id, self.model_data_parsed["id"], f"Correspondent id is wrong when created from dict: {model.id}")
        self.assertEqual(model.slug, self.model_data_parsed["slug"], f"Correspondent slug is wrong when created from dict: {model.slug}")
        self.assertEqual(model.name, self.model_data_parsed["name"], f"Correspondent name is wrong when created from dict: {model.name}")
        self.assertEqual(model.document_count, self.model_data_parsed["document_count"], f"Correspondent document_count is wrong when created from dict: {model.document_count}")
        self.assertEqual(model.owner, self.model_data_parsed["owner"], f"Correspondent owner is wrong when created from dict: {model.owner}")
        self.assertEqual(model.user_can_change, self.model_data_parsed["user_can_change"], f"Correspondent user_can_change is wrong when created from dict: {model.user_can_change}")
        self.assertEqual(model.is_insensitive, self.model_data_parsed["is_insensitive"], f"Correspondent is_insensitive is wrong when created from dict: {model.is_insensitive}")
        self.assertEqual(model.match, self.model_data_parsed["match"], f"Correspondent match is wrong when created from dict: {model.match}")
        self.assertEqual(model.matching_algorithm, self.model_data_parsed["matching_algorithm"], f"Correspondent matching_algorithm is wrong when created from dict: {model.matching_algorithm}")

    def test_documents(self):
        model = Correspondent.from_dict(self.model_data_parsed)
        self.assertIsInstance(model.documents, DocumentQuerySet, f"Expected BaseQuerySet, got {type(model.documents)}")
