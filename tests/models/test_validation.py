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
from paperap.tests import UnitTestCase, load_sample_data, CorrespondentUnitTest

from hypothesis import given, strategies as st
from hypothesis.strategies import text, integers, one_of, booleans, none
from pydantic import ValidationError
from paperap.models import Correspondent
import pytest


class TestCorrespondentValidation:
    """Hypothesis-powered test cases for the Correspondent model."""

    @given(text() | none())
    def test_slug_field(self, slug):
        if isinstance(slug, str) or slug is None:
            correspondent = Correspondent(slug=slug)
            assert correspondent.slug == slug
        else:
            with pytest.raises(ValidationError):
                Correspondent(slug=slug)

    @given(text() | none())
    def test_name_field(self, name):
        if isinstance(name, str) or name is None:
            correspondent = Correspondent(name=name)
            assert correspondent.name == name
        else:
            with pytest.raises(ValidationError):
                Correspondent(name=name)

    @given(integers() | none())
    def test_document_count_field(self, document_count):
        if isinstance(document_count, int):
            correspondent = Correspondent(document_count=document_count)
            assert correspondent.document_count == document_count
        else:
            with pytest.raises(ValidationError):
                Correspondent(document_count=document_count)

    @given(integers() | none())
    def test_owner_field(self, owner):
        if isinstance(owner, int) or owner is None:
            correspondent = Correspondent(owner=owner)
            assert correspondent.owner == owner
        else:
            with pytest.raises(ValidationError):
                Correspondent(owner=owner)

    @given(one_of(booleans(), none()))
    def test_user_can_change_field(self, user_can_change):
        if isinstance(user_can_change, bool) or user_can_change is None:
            correspondent = Correspondent(user_can_change=user_can_change)
            assert correspondent.user_can_change == user_can_change
        else:
            with pytest.raises(ValidationError):
                Correspondent(user_can_change=user_can_change)
