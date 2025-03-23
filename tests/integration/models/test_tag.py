
from __future__ import annotations

import logging
import os
import unittest
from datetime import datetime, timezone
from typing import Iterable, override
from unittest.mock import MagicMock, patch

from paperap.client import PaperlessClient
from paperap.exceptions import ReadOnlyFieldError, ResourceNotFoundError
from paperap.models import *
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.tags import TagResource
from tests.lib import TagUnitTest, factories, load_sample_data

logger = logging.getLogger(__name__)

sample_tag_list = load_sample_data('tags_list.json')
sample_tag = load_sample_data('tags_item.json')

class IntegrationTest(TagUnitTest):
    mock_env = False

    @override
    def setUp(self):
        super().setUp()
        #self.model = self.client.tags().get(7411)
        #self._initial_data = self.model.to_dict()

    @override
    def tearDown(self):
        # Request that paperless ngx reverts to the previous data
        #self.model.update_locally(from_db=True, **self._initial_data)
        # Must be called manually in case subclasses turn off autosave and mocks self.is_new()
        #self.model.save(force=True)

        # TODO: confirm without another query
        return super().tearDown()

class TestFeatures(IntegrationTest):
    @override
    def setup_model(self):
        super().setup_model()
        self._meta.save_on_write = False

    def test_create(self):
        # Ensure name is unique
        name = f"test_create_tag {datetime.now().isoformat()}"
        model = factories.TagFactory.build(name=name, id=0, owner=1)
        data = model.to_dict()
        tag = Tag.create(**data)
        self.assertIsNotNone(tag.id)
        self.assertEqual(tag.name, model.name)
        #self.assertEqual(tag.slug, data['slug'])

        # Retrieve it
        retrieved_tag = self.client.tags().get(tag.id)
        self.assertEqual(retrieved_tag.name, model.name)
        #self.assertEqual(retrieved_tag.slug, data['slug'])
        self.assertIsNotNone(retrieved_tag.id)
        self.assertGreater(retrieved_tag.id, 0)

        # Delete it
        tag.delete()
        with self.assertRaises(ResourceNotFoundError):
            self.client.tags().get(tag.id)
