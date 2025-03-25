

from __future__ import annotations

import copy
import logging
import os
import unittest
from datetime import datetime, timezone
from random import sample
from typing import Any, Iterable, List, override
from unittest.mock import MagicMock, PropertyMock, patch

from paperap.client import PaperlessClient
from paperap.models import *
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.document.model import CustomFieldTypedDict, CustomFieldValues, DocumentNote
from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.documents import DocumentResource
from tests.lib import DocumentUnitTest, factories, load_sample_data

logger = logging.getLogger(__name__)

sample_document_list = load_sample_data('documents_list.json')
sample_document = load_sample_data('documents_item.json')

class TestDocumentInit(DocumentUnitTest):
    @override
    def setup_model_data(self):
        self.model_data_unparsed = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tags": [1, 2, 3],
        }
        self.model_data_parsed = {
            **self.model_data_unparsed,
        }
        self.model_data_parsed['tag_ids'] = self.model_data_parsed.pop('tags')

    def test_from_dict(self):
        fields = {
            "id": int,
            "title": str,
        }
        for field, field_type in fields.items():
            value = getattr(self.model, field)
            if self.model_data_parsed[field] is None:
                self.assertIsNone(value)
            else:
                self.assertIsInstance(value, field_type, f"Expected {field} to be a {field_type}, got {type(value)}")
            self.assertEqual(value, self.model_data_unparsed[field], f"Expected {field} to match sample data")
        self.assertIsInstance(self.model.created, datetime, f"created wrong type after from_dict {type(self.model.created)}")
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc), f"created wrong value after from_dict {self.model.created}")
        self.assertIsInstance(self.model.tag_ids, Iterable)
        self.assertEqual(self.model.tag_ids, [1, 2, 3])
        self.assertIsInstance(self.model.correspondent_id, int)
        self.assertEqual(self.model.correspondent_id, 1)
        self.assertIsInstance(self.model.document_type_id, int)
        self.assertEqual(self.model.document_type_id, 1)
        self.assertIsInstance(self.model.tags, TagQuerySet)

class TestDocumentBase(DocumentUnitTest):
    @override
    def setup_model_data(self):
        self.model_data_unparsed = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tag_ids": [1, 2, 3],
        }

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.created, datetime, f"created wrong type after from_dict {type(self.model.created)}")

        # TZ UTC
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.title, "Test Document")

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.correspondent_id, 1)
        self.assertEqual(self.model.document_type_id, 1)

    def test_model_list_parsing(self):
        # Test if list fields are parsed correctly
        self.assertIsInstance(self.model.tag_ids, Iterable)
        self.assertEqual(self.model.tag_ids, [1, 2, 3])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["created"], '2025-03-01T12:00:00+00:00')
        self.assertEqual(model_dict["title"], "Test Document")
        self.assertEqual(model_dict["correspondent_id"], 1)
        self.assertEqual(model_dict["document_type_id"], 1)
        self.assertEqual(model_dict["tag_ids"], [1, 2, 3])

    def test_equals(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document
            document1 = self.get_resource(DocumentResource, 1)
            document2 = self.get_resource(DocumentResource, 1)
            self.assertEqual(document1, document2)

class TestGetRelationships(DocumentUnitTest):
    def __temp_disable_test_get_tags(self):
        sample_data = load_sample_data('tags_list_id__in_38,162,160,191.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            expected_count = len(self.model.tag_ids)
            tags = self.model.tags
            self.assertIsInstance(tags, TagQuerySet)
            actual_count = tags.count()
            self.assertEqual(expected_count, actual_count, f"Expected {expected_count} tags, got {actual_count}")

            count = 0
            for tag in tags:
                self.assertIsInstance(tag, Tag, f"Expected tag to be a Tag, got {type(tag)}")

                count += 1
                fields = {
                    "id": int,
                    "name": str,
                    "slug": str,
                    "match": str,
                    "matching_algorithm": int,
                    "is_insensitive": bool,
                    "is_inbox_tag": bool,
                    "document_count": int,
                    "owner": int,
                    "user_can_change": bool
                }
                for field, field_type in fields.items():
                    value = getattr(tag, field)
                    if value is not None:
                        self.assertIsInstance(value, field_type, f"Expected tag.{field} to be a {field_type}, got {type(value)}")

                if tag.colour is not None:
                    self.assertTrue(isinstance(tag.colour, (str, int)), f"Expected tag.colour to be a string or int, got {type(tag.colour)}")
                self.assertGreater(tag.document_count, 0, f"Expected tag.document_count to be greater than 0, got {tag.document_count}")
                self.assertTrue(tag in self.model.tags, f"Expected tag to be in document.tags. {tag.id} not in {self.model.tag_ids}")
                self.assertTrue(tag.id in self.model.tag_ids, f"Expected tag.id to be in document.tag_ids. {tag.id} not in {self.model.tag_ids}")

            self.assertEqual(count, expected_count, f"Expected to iterate over {expected_count} tags, only saw {count}")

    def test_get_correspondent(self):
        sample_data = load_sample_data('correspondents_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.model.correspondent_id = sample_data["id"]
            correspondent = self.model.correspondent
            self.assertIsInstance(correspondent, Correspondent, f"Expected document.correspondent_id to be a Correspondent, got {type(correspondent)}")
            # Make mypy happy
            assert correspondent is not None
            fields = {
                "id": int,
                "slug": str,
                "name": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(correspondent, field)
                if sample_data[field] is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsInstance(value, field_type, f"Expected correspondent.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_data[field], f"Expected correspondent.{field} to match sample data")

    def test_get_document_type(self):
        sample_data = load_sample_data('document_types_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.model.document_type_id = sample_data["id"]
            document_type = self.model.document_type
            self.assertIsInstance(document_type, DocumentType, f"Expected document.document_type_id to be a DocumentType, got {type(document_type)}")
            # Make mypy happy
            assert document_type is not None
            fields = {
                "id": int,
                "name": str,
                "slug": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(document_type, field)
                if sample_data[field] is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsInstance(value, field_type, f"Expected document_type.{field} to be a {field_type}, got {type(value)}")
                    self.assertEqual(value, sample_data[field], f"Expected document_type.{field} to match sample data")

    def test_get_storage_path(self):
        sample_data = load_sample_data('storage_paths_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_data
            self.model.storage_path_id = sample_data["id"]
            storage_path = self.model.storage_path
            self.assertIsInstance(storage_path, StoragePath, f"Expected document.storage_path to be a StoragePath, got {type(storage_path)}")
            # Make mypy happy
            assert storage_path is not None
            fields = {
                "id": int,
                "name": str,
                "slug": str,
                "path": str,
                "match": str,
                "matching_algorithm": int,
                "is_insensitive": bool,
                "document_count": int,
                "owner": int,
                "user_can_change": bool
            }
            for field, field_type in fields.items():
                value = getattr(storage_path, field)
                self.assertIsInstance(value, field_type, f"Expected storage_path.{field} to be a {field_type}, got {type(value)}")
                self.assertEqual(value, sample_data[field], f"Expected storage_path.{field} to match sample data")

class TestRequestDocumentList(DocumentUnitTest):
    def test_request_list(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document_list
            documents = self.client.documents()
            self.assertIsInstance(documents, BaseQuerySet)
            total = documents.count()
            expected = sample_document_list["count"]
            self.assertEqual(total, expected, f"Expected {expected} documents, got {total}")

class TestRequestDocument(DocumentUnitTest):
    def test_manual(self):
        """Test getting the document without using any of our custom unit test functionality, just in case."""
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = copy.deepcopy(sample_document)
            document = self.client.documents.get(1)

            self.assertIsInstance(document, Document)
            self.assertEqual(document.id, sample_document['id'])
            self.assertEqual(document.title, sample_document['title'])
            self.assertEqual(document.correspondent_id, sample_document['correspondent'])
            self.assertEqual(document.document_type_id, sample_document['document_type'])
            self.assertEqual(document.storage_path_id, sample_document['storage_path'])
            self.assertEqual(document.tag_ids, sample_document['tags'])

    def test_get(self):
        document = self.get_resource(DocumentResource, self.model_data_parsed["id"])
        self.assertIsInstance(document, Document)
        fields = {
            "id": int,
            "title": str,
        }
        for field, field_type in fields.items():
            value = getattr(document, field)
            if self.model_data_parsed[field] is None:
                self.assertIsNone(value)
            else:
                self.assertIsInstance(value, field_type, f"Expected document.{field} to be a {field_type}, got {type(value)}")
                self.assertEqual(value, self.model_data_parsed[field], f"Expected document.{field} to match sample data")

        if document.created is not None:
            self.assertIsInstance(document.created, datetime, f"created wrong type after from_dict {type(document.created)}")
        self.assertIsInstance(document.tag_ids, Iterable)
        self.assertEqual(document.tag_ids, self.model_data_parsed["tags"])

        if self.model_data_parsed["correspondent"] is None:
            self.assertIsNone(document.correspondent_id)
        else:
            self.assertIsInstance(document.correspondent_id, int)
            self.assertEqual(document.correspondent_id, self.model_data_parsed["correspondent"])

        if self.model_data_parsed["document_type"] is None:
            self.assertIsNone(document.document_type_id)
        else:
            self.assertIsInstance(document.document_type_id, int)
            self.assertEqual(document.document_type_id, self.model_data_parsed["document_type"])

        if self.model_data_parsed["storage_path"] is None:
            self.assertIsNone(document.storage_path_id)
        else:
            self.assertIsInstance(document.storage_path_id, int)
            self.assertEqual(document.storage_path_id, self.model_data_parsed["storage_path"])

class TestCustomFieldAccess(DocumentUnitTest):

    @override
    def setUp(self):
        super().setUp()
        self.custom_fields = [
            {"field": 1, "value": "Test Value 1"},
            {"field": 2, "value": "Test Value 2"},
            {"field": 53, "value": "Test Value 53"},
            {"field": 54, "value": 54},
            {"field": 55, "value": 55.50},
            {"field": 56, "value": True},
            {"field": 57, "value": False},
            {"field": 58, "value": None},
        ]
        self.model = self.bake_model(**{
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tag_ids": [1, 2, 3],
            "custom_field_dicts": self.custom_fields
        })

    def test_custom_field_success(self):
        for field in self.custom_fields:
            field_id = field["field"]
            expected = field["value"]
            actual = self.model.custom_field_value(field_id) # type: ignore
            self.assertEqual(expected, actual, f"Expected {expected}, got {actual} of type {type(actual)}")

    def test_custom_field_default(self):
        default = "Default Value"
        actual = self.model.custom_field_value(3, default=default)
        self.assertEqual(default, actual, f"Expected {default}, got {actual} of type {type(actual)}")

    def test_custom_field_raises(self):
        with self.assertRaises(ValueError):
            self.model.custom_field_value(3, raise_errors=True)
        with self.assertRaises(ValueError):
            self.model.custom_field_value(3, default="Some Default", raise_errors=True)

    def test_custom_field_ids_property(self):
        """Test the custom_field_ids property returns the correct field IDs."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        expected_ids = [field["field"] for field in self.custom_fields]
        self.assertEqual(self.model.custom_field_ids, expected_ids)

    def test_custom_field_values_property(self):
        """Test the custom_field_values property returns the correct values."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        expected_values = [field["value"] for field in self.custom_fields]
        self.assertEqual(self.model.custom_field_values, expected_values)


class TestDocumentNotes(DocumentUnitTest):

    """Test the DocumentNote model and related functionality."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    @override
    def setUp(self):
        super().setUp()
        self.note_data = {
            "id": 1,
            "note": "Test note content",
            "created": "2025-03-01T12:00:00Z",
            "document": 1,
            "user": 1
        }
        self.document_with_notes = self.bake_model(**{
            "id": 1,
            "title": "Test Document with Notes",
            "notes": [self.note_data]
        })

    def test_document_note_init(self):
        """Test creating a DocumentNote instance."""
        note = DocumentNote(**self.note_data) # type: ignore
        self.assertEqual(note.id, 1)
        self.assertEqual(note.note, "Test note content")
        self.assertIsInstance(note.created, datetime)
        self.assertEqual(note.document, 1)
        self.assertEqual(note.user, 1)

    def test_document_notes_property(self):
        """Test that document.notes returns the correct list of notes."""
        self.assertEqual(len(self.document_with_notes.notes), 1)
        self.assertIsInstance(self.document_with_notes.notes[0], DocumentNote)
        self.assertEqual(self.document_with_notes.notes[0].note, "Test note content")

    def test_document_note_serialization(self):
        """Test that DocumentNote objects are properly serialized."""
        note = DocumentNote(**self.note_data) # type: ignore
        serialized = note.to_dict()
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized["id"], 1)
        self.assertEqual(serialized["note"], "Test note content")

    @patch("paperap.client.PaperlessClient.request")
    def test_get_document_method(self, mock_request):
        """Test the get_document method on DocumentNote."""
        mock_request.return_value = {"id": 1, "title": "Test Document"}
        note = DocumentNote(**self.note_data) # type: ignore
        document = note.get_document()
        self.assertIsInstance(document, Document)
        self.assertEqual(document.id, 1)

    @patch("paperap.client.PaperlessClient.request")
    def test_get_user_method(self, mock_request):
        """Test the get_user method on DocumentNote."""
        mock_request.return_value = {"id": 1, "username": "testuser"}
        note = DocumentNote(**self.note_data) # type: ignore
        user = note.get_user()
        self.assertEqual(user.id, 1)


class TestCustomFieldValues(unittest.TestCase):

    """Test the CustomFieldValues model."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    def test_init(self):
        """Test creating a CustomFieldValues instance."""
        cfv = CustomFieldValues(field=1, value="test value")
        self.assertEqual(cfv.field, 1)
        self.assertEqual(cfv.value, "test value")

    def test_equality_with_dict(self):
        """Test equality comparison with a dictionary."""
        cfv = CustomFieldValues(field=1, value="test value")

        # Equal dict
        self.assertEqual(cfv, {"field": 1, "value": "test value"})

        # Different field
        self.assertNotEqual(cfv, {"field": 2, "value": "test value"})

        # Different value
        self.assertNotEqual(cfv, {"field": 1, "value": "different value"})

        # Missing key
        self.assertNotEqual(cfv, {"field": 1})

        # Extra key
        self.assertNotEqual(cfv, {"field": 1, "value": "test value", "extra": "key"})

    def test_equality_with_custom_field_values(self):
        """Test equality comparison with another CustomFieldValues instance."""
        cfv1 = CustomFieldValues(field=1, value="test value")
        cfv2 = CustomFieldValues(field=1, value="test value")
        cfv3 = CustomFieldValues(field=2, value="test value")
        cfv4 = CustomFieldValues(field=1, value="different value")

        self.assertEqual(cfv1, cfv2)
        self.assertNotEqual(cfv1, cfv3)
        self.assertNotEqual(cfv1, cfv4)

    def test_equality_with_other_types(self):
        """Test equality comparison with other types."""
        cfv = CustomFieldValues(field=1, value="test value")

        # Should use the parent class's __eq__ method
        self.assertNotEqual(cfv, "not a dict or CustomFieldValues")
        self.assertNotEqual(cfv, 123)
        self.assertNotEqual(cfv, None)


class TestDocumentSetters(DocumentUnitTest):

    """Test the setter methods for Document relationships."""

    # TODO: All methods in this class are AI Generated Tests (Claude 3.7). Will remove this note when it is reviewed.

    @override
    def setUp(self):
        super().setUp()
        self.model = self.bake_model(**{
            "id": 1,
            "title": "Test Document"
        })
        self.client.settings.save_on_write = False

    def test_tags_setter_with_none(self):
        """Test setting tags to None."""
        self.model.tags = None
        self.assertEqual(self.model.tag_ids, [])

    def test_tags_setter_with_integers(self):
        """Test setting tags with integer IDs."""
        self.model.tags = [1, 2, 3]
        self.assertEqual(self.model.tag_ids, [1, 2, 3])
        self.assertIsInstance(self.model.tags, TagQuerySet)

    def test_tags_setter_with_tag_objects(self):
        """Test setting tags with Tag objects."""
        tag1 = Tag(id=1, name="Tag 1", is_insensitive=False) # type: ignore
        tag2 = Tag(id=2, name="Tag 2", is_insensitive=False) # type: ignore
        self.model.tags = [tag1, tag2]
        self.assertEqual(self.model.tag_ids, [1, 2])
        self.assertIsInstance(self.model.tags, TagQuerySet)

    def test_tags_setter_with_mixed_types(self):
        """Test setting tags with a mix of integers and Tag objects."""
        tag = Tag(id=2, name="Tag 2", is_insensitive=False) # type: ignore
        self.model.tags = [1, tag, 3]
        self.assertEqual(self.model.tag_ids, [1, 2, 3])
        self.assertIsInstance(self.model.tags, TagQuerySet)

    def test_tags_setter_with_invalid_type(self):
        """Test setting tags with an invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.model.tags = "not an iterable" # type: ignore

    def test_tags_setter_with_invalid_item_type(self):
        """Test setting tags with invalid item types raises TypeError."""
        with self.assertRaises(TypeError):
            self.model.tags = [1, "not an int or Tag", 3] # type: ignore

    def test_correspondent_setter_with_none(self):
        """Test setting correspondent to None."""
        self.model.correspondent = None
        self.assertIsNone(self.model.correspondent_id)
        self.assertIsNone(self.model.correspondent)

    def test_correspondent_setter_with_integer(self):
        """Test setting correspondent with an integer ID."""
        self.model.correspondent = 1
        self.assertEqual(self.model.correspondent_id, 1)
        sample_correspondent = load_sample_data('correspondents_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_correspondent
            self.assertIsInstance(self.model.correspondent, Correspondent)

    def test_correspondent_setter_with_correspondent_object(self):
        """Test setting correspondent with a Correspondent object."""
        correspondent = Correspondent(id=1, name="Test Correspondent", is_insensitive = True) # type: ignore
        self.model.correspondent = correspondent
        self.assertEqual(self.model.correspondent_id, 1)
        sample_correspondent = load_sample_data('correspondents_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_correspondent
            self.assertIsInstance(self.model.correspondent, Correspondent)

        # Test that the cache is populated
        self.assertEqual(self.model._correspondent, (1, correspondent)) # type: ignore

    def test_correspondent_setter_with_invalid_type(self):
        """Test setting correspondent with an invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.model.correspondent = "not an int or Correspondent" # type: ignore

    def test_document_type_setter_with_none(self):
        """Test setting document_type to None."""
        self.model.document_type = None
        self.assertIsNone(self.model.document_type_id)
        self.assertIsNone(self.model.document_type)

    def test_document_type_setter_with_integer(self):
        """Test setting document_type with an integer ID."""
        self.model.document_type = 1
        self.assertEqual(self.model.document_type_id, 1)
        sample_document_type = load_sample_data('document_types_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document_type
            self.assertIsInstance(self.model.document_type, DocumentType)

    def test_document_type_setter_with_document_type_object(self):
        """Test setting document_type with a DocumentType object."""
        doc_type = DocumentType(id=1, name="Test Document Type", is_insensitive = False) # type: ignore
        self.model.document_type = doc_type
        self.assertEqual(self.model.document_type_id, 1)
        sample_document_type = load_sample_data('document_types_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document_type
            self.assertIsInstance(self.model.document_type, DocumentType)

        # Test that the cache is populated
        self.assertEqual(self.model._document_type, (1, doc_type)) # type: ignore

    def test_document_type_setter_with_invalid_type(self):
        """Test setting document_type with an invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.model.document_type = "not an int or DocumentType" # type: ignore

    def test_storage_path_setter_with_none(self):
        """Test setting storage_path to None."""
        self.model.storage_path = None
        self.assertIsNone(self.model.storage_path_id)
        self.assertIsNone(self.model.storage_path)

    def test_storage_path_setter_with_integer(self):
        """Test setting storage_path with an integer ID."""
        self.model.storage_path = 1
        self.assertEqual(self.model.storage_path_id, 1)
        sample_storage_path = load_sample_data('storage_paths_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_storage_path
            self.assertIsInstance(self.model.storage_path, StoragePath)

    def test_storage_path_setter_with_storage_path_object(self):
        """Test setting storage_path with a StoragePath object."""
        data = {"id": 1, "name": "Test Storage Path", "is_insensitive": False}
        storage_path = StoragePath(**data) # type: ignore
        self.model.storage_path = storage_path
        self.assertEqual(self.model.storage_path_id, 1)
        sample_storage_path = load_sample_data('storage_paths_item.json')
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_storage_path
            self.assertIsInstance(self.model.storage_path, StoragePath)

        # Test that the cache is populated
        self.assertEqual(self.model._storage_path, (1, storage_path)) # type: ignore

    def test_storage_path_setter_with_invalid_type(self):
        """Test setting storage_path with an invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            self.model.storage_path = "not an int or StoragePath" # type: ignore

class TestDocumentInitialization(DocumentUnitTest):
    @override
    def setUp(self):
        super().setUp()
        # Setup a sample model instance
        self.resource = self.client.documents
        self.model_data_parsed = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tag_ids": [1, 2, 3],
        }

    def test_from_dict(self):
        model = Document.from_dict(self.model_data_parsed)
        self.assertIsInstance(model, Document, f"Expected Document, got {type(model)}")
        self.assertEqual(model.id, self.model_data_parsed["id"], f"Document id is wrong when created from dict: {model.id}")
        self.assertEqual(model.title, self.model_data_parsed["title"], f"Document title is wrong when created from dict: {model.title}")
        self.assertEqual(model.correspondent_id, self.model_data_parsed["correspondent_id"], f"Document correspondent is wrong when created from dict: {model.correspondent_id}")
        self.assertEqual(model.document_type_id, self.model_data_parsed["document_type_id"], f"Document document_type is wrong when created from dict: {model.document_type_id}")
        self.assertIsInstance(model.tag_ids, Iterable, f"Document tags is wrong type when created from dict: {type(model.tag_ids)}")
        self.assertEqual(model.tag_ids, self.model_data_parsed["tag_ids"], f"Document tags is wrong when created from dict: {model.tag_ids}")
        self.assertIsInstance(model.created, datetime, f"created wrong type after from_dict {type(model.created)}")
        self.assertEqual(model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc), f"created wrong value after from_dict {model.created}")

class TestDocument(DocumentUnitTest):
    @override
    def setUp(self):
        super().setUp()
        # Setup a sample model instance
        self.resource = self.client.documents
        self.model_data_parsed = {
            "id": 1,
            "created": "2025-03-01T12:00:00Z",
            "title": "Test Document",
            "correspondent_id": 1,
            "document_type_id": 1,
            "tag_ids": [1, 2, 3],
        }
        self.model = Document.from_dict(self.model_data_parsed)

    def test_model_date_parsing(self):
        # Test if date strings are parsed into datetime objects
        self.assertIsInstance(self.model.created, datetime, f"created wrong type after from_dict {type(self.model.created)}")

        # TZ UTC
        self.assertEqual(self.model.created, datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc))

    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.title, "Test Document")

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.correspondent_id, 1)
        self.assertEqual(self.model.document_type_id, 1)

    def test_model_list_parsing(self):
        # Test if list fields are parsed correctly
        self.assertIsInstance(self.model.tag_ids, Iterable)
        self.assertEqual(self.model.tag_ids, [1, 2, 3])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        model_dict = self.model.to_dict()

        self.assertEqual(model_dict["created"], "2025-03-01T12:00:00+00:00")
        self.assertEqual(model_dict["title"], "Test Document")
        self.assertEqual(model_dict["correspondent_id"], 1)
        self.assertEqual(model_dict["document_type_id"], 1)
        self.assertEqual(model_dict["tag_ids"], [1, 2, 3])

class TestRequest(DocumentUnitTest):
    def test_get_document(self):
        with patch("paperap.client.PaperlessClient.request") as mock_request:
            mock_request.return_value = sample_document
            document : Document = self.get_resource(DocumentResource, 7313) # type: ignore
            self.assertIsInstance(document, Document)
            self.assertIsInstance(document.id, int, "Loading sample document, id wrong type")
            self.assertIsInstance(document.title, str, "Loading sample document, title wrong type")
            self.assertEqual(document.id, sample_document["id"], "Loading sample document id mismatch")
            self.assertEqual(document.title, sample_document["title"], "Loading sample document title mismatch")

            if getattr(sample_document, 'storage_path   ', None) is not None:
                self.assertIsInstance(document.storage_path_id, int if sample_document["storage_path"] else type(None), "Loading sample document, storage_path wrong type")
                self.assertEqual(document.storage_path_id, sample_document["storage_path"], "Loading sample document storage_path mismatch")
            if getattr(sample_document, 'correspondent', None) is not None:
                self.assertIsInstance(document.correspondent_id, int if sample_document["correspondent"] is not None else type(None), "Loading sample document, correspondent wrong type")
                self.assertEqual(document.correspondent_id, sample_document["correspondent"], "Loading sample document correspondent mismatch")
            if getattr(sample_document, 'document_type', None) is not None:
                self.assertIsInstance(document.document_type_id, int if sample_document["document_type"] is not None else type(None), "Loading sample document, document_type wrong type")
                self.assertEqual(document.document_type_id, sample_document["document_type"], "Loading sample document document_type mismatch")
            if getattr(sample_document, 'created', None) is not None:
                self.assertIsInstance(document.created, datetime, "Loading sample document created wrong type")
                # TODO
            if getattr(sample_document, 'tags', None) is not None:
                self.assertIsInstance(document.tag_ids, list, "Loading sample document, tags wrong type")
                self.assertEqual(document.tag_ids, sample_document["tag_ids"], "Loading sample document tags mismatch")

if __name__ == "__main__":
    unittest.main()
