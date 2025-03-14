"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_custom_field.py
        Project: paperap
        Created: 2025-03-11
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-11     By Jess Mann

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
from paperap.tests import UnitTestCase, load_sample_data, CustomFieldUnitTest


# TODO: Use conversion table in pydantic to expand these tests
# TODO: Import testing custom framework?
string_tests = [
            ("a", "a"),
            ("Valid Name", "Valid Name"),
            ("verylongnamewithnospaces verylongsecond verylongthird", "verylongnamewithnospaces verylongsecond verylongthird"),
            ("", ""),
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

class TestCustomFieldValidation(CustomFieldUnitTest):
    def test_name_field(self):
        self.validate_field("name", [
            *string_tests,
            (None, ValidationError),
        ])

    def test_data_type_field(self):
        self.validate_field("data_type", [
            ("string", "string"),
            ("integer", "integer"),
            (None, None),
            (123, ValidationError),
            (["list"], ValidationError),
            ({"dict": "value"}, ValidationError),
            (object(), ValidationError),
            (5.5, ValidationError),
        ])

    def test_extra_data_field(self):
        self.validate_field("extra_data", [
            ({}, {}),
            ({"key": "value"}, {"key": "value"}),
            ({"int": 123, "bool": True}, {"int": 123, "bool": True}),
            ([], ValidationError),
            ("string", ValidationError),
            (None, ValidationError),
            (5.5, ValidationError),
            (object(), ValidationError),
        ])

    def test_document_count_field(self):
        self.validate_field("document_count", [
            *any_int_tests,
            (None, ValidationError),
        ])
