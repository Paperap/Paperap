

from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from typing import Iterable, override
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from tests.lib import CorrespondentUnitTest, UnitTestCase, load_sample_data

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

class TestCorrespondentValidation(CorrespondentUnitTest):
    def test_slug_field(self):
        self.validate_field("slug", [
            *string_tests,
            (None, None),
        ])

    def test_name_field(self):
        self.validate_field("name", [
            *string_tests,
            (None, None),
        ])

    def test_document_count_field(self):
        self.validate_field("document_count", [
            *any_int_tests,
            (None, ValidationError),
        ])

    def test_owner_field(self):
        self.validate_field("owner", [
            *any_int_tests,
            (None, None),
        ])

    def test_user_can_change_field(self):
        self.validate_field("user_can_change", [
            *bool_loose_tests,
            (None, None),
        ])
