"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_tag.py
        Project: paperap
        Created: 2025-03-14
        Version: 0.0.7
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-14     By Jess Mann

"""
from __future__ import annotations
import os
from typing import Iterable, override
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from pydantic import ValidationError
from paperap.models.tag import Tag
from paperap.client import PaperlessClient
from paperap.resources.tags import TagResource
from paperap.tests import UnitTestCase, load_sample_data, TagUnitTest

# Load sample response from tests/sample_data/tags_list.json
sample_data = load_sample_data('tags_list.json')

class TestTagInit(TagUnitTest):

    def test_from_dict(self):
        model = Tag.from_dict(self.model_data_parsed)
        self.assertIsInstance(model, Tag, f"Expected Tag, got {type(model)}")
        self.assertEqual(model.id, self.model_data_parsed["id"], f"Tag id is wrong when created from dict: {model.id}")
        self.assertEqual(model.name, self.model_data_parsed["name"], f"Tag name is wrong when created from dict: {model.name}")
        self.assertEqual(model.slug, self.model_data_parsed["slug"], f"Tag slug is wrong when created from dict: {model.slug}")
        self.assertEqual(model.colour, self.model_data_parsed["colour"], f"Tag color is wrong when created from dict: {model.colour}")
        self.assertEqual(model.match, self.model_data_parsed["match"], f"Tag match is wrong when created from dict: {model.match}")
        self.assertEqual(model.matching_algorithm, self.model_data_parsed["matching_algorithm"], f"Tag matching_algorithm is wrong when created from dict: {model.matching_algorithm}")
        self.assertEqual(model.is_insensitive, self.model_data_parsed["is_insensitive"], f"Tag is_insensitive is wrong when created from dict: {model.is_insensitive}")
        self.assertEqual(model.is_inbox_tag, self.model_data_parsed["is_inbox_tag"], f"Tag is_inbox_tag is wrong when created from dict: {model.is_inbox_tag}")

class TestTag(TagUnitTest):
    def test_model_string_parsing(self):
        # Test if string fields are parsed correctly
        self.assertEqual(self.model.name, self.model_data_parsed["name"])

    def test_model_int_parsing(self):
        # Test if integer fields are parsed correctly
        self.assertEqual(self.model.matching_algorithm, self.model_data_parsed["matching_algorithm"])

    def test_model_to_dict(self):
        # Test if the model can be converted back to a dictionary
        self.assertIsInstance(self.model, Tag, "test prerequisit failed")
        model_dict = self.model.to_dict(exclude_unset=False)

        for key, value in self.model_data_parsed.items():
            self.assertIn(key, model_dict, f"Key {key} not found in model_dict")
            self.assertEqual(value, model_dict[key], f"Value for key {key} is incorrect")

# TODO: Use conversion table in pydantic to expand these tests
string_tests = [
            ("a", "a"),
            ("Valid Name", "Valid Name"),
            ("verylongnamewithnospaces verylongsecond verylongthird", "verylongnamewithnospaces verylongsecond verylongthird"),
            ("", ""),
            (None, None),
            (123, ValidationError),
            (["list"], ValidationError),
            ({"dict", "value"}, ValidationError),
            (object(), ValidationError),
            (5.5, ValidationError),
        ]

int_base_tests = [
            (1, 1),
            (0, 0),
            (100, 100),
            ("ten", ValidationError),
            ("somestring", ValidationError),
            ("string with numbers 123", ValidationError),
            (["list"], ValidationError),
            ({"dict", "value"}, ValidationError),
            (3.5, ValidationError),
            (object(), ValidationError),
]

any_int_tests = [
    *int_base_tests,
    (-1, -1),
    (-100, -100),
]

positive_int_tests = [
    *int_base_tests,
    (-1, ValidationError),
    (-100, ValidationError),
]

bool_base_tests = [
            (True, True),
            (False, False),
            (5, ValidationError),
            (3.5, ValidationError),
            (object(), ValidationError),
]

bool_strict_tests = [
            ("1", ValidationError),
            ("0", ValidationError),
            ("yes", ValidationError),
            ("no", ValidationError),
            (1, ValidationError),
            (0, ValidationError),
            ("true", ValidationError),
            ("false", ValidationError),
]

bool_loose_tests = [
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            (1, True),
            (0, False),
            ("true", True),
            ("false", False),
]

class TestTagValidation(TagUnitTest):
    def test_name_field(self):
        self.validate_field("name", string_tests)

    def test_slug_field(self):
        self.validate_field("slug", string_tests)

    def test_colour_field(self):
        self.validate_field("colour", [
            ("#ff0000", "#ff0000"),
            ("blue", "blue"),
            ("invalid-color", "invalid-color"),
            (None, None),
            (12345, 12345), # Paperless allows ints for color
            (object(), TypeError),
            (["list"], TypeError),
            ({"dict", "value"}, TypeError),
            (5.5, TypeError),
        ])

    def test_is_inbox_tag_field(self):
        self.validate_field("is_inbox_tag", bool_loose_tests)

    def test_document_count_field(self):
        self.validate_field("document_count", [
            #*positive_int_tests, # TODO
            *any_int_tests,
            (None, ValidationError),
        ])

    def test_owner_field(self):
        self.validate_field("owner", [
            #*positive_int_tests # TODO
            *any_int_tests,
            (None, None),
        ])

    def test_user_can_change_field(self):
        self.validate_field("user_can_change", bool_loose_tests)

    def test_match_field(self):
        self.validate_field("match", [
            ("regex pattern", "regex pattern"),
            (None, None),
            (123, ValidationError),
            (True, ValidationError),
        ])

    def test_matching_algorithm_field(self):
        self.validate_field("matching_algorithm", [
            #*positive_int_tests # TODO
            *any_int_tests,
            (None, None),
        ])

    def test_is_insensitive_field(self):
        self.validate_field("is_insensitive", bool_loose_tests)

if __name__ == "__main__":
    unittest.main()
