"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    text_write.py
        Project: paperap
        Created: 2025-03-12
        Version: 0.0.6
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-12     By Jess Mann

"""
import datetime
import os

from pydantic import ValidationError
from paperap.models.correspondent.queryset import CorrespondentQuerySet
import paperap.models.document
import paperap.models.document.model
from typing import Any, Iterator, Union, Optional
from hypothesis import example, given, strategies as st
from paperap.models import Correspondent
from paperap.tests import random_json, create_resource, defaults as d
from paperap.resources.correspondents import CorrespondentResource
from paperap.tests.factories import CorrespondentFactory

resource = create_resource(CorrespondentResource)
correspondent_data = CorrespondentFactory.to_dict()

@given(
    id=st.integers(min_value=1, max_value=10**6),
    slug=st.one_of(st.none(), st.text(min_size=1, max_size=255)),
    name=st.one_of(st.none(), st.text(min_size=1, max_size=255)),
    document_count=st.integers(min_value=0, max_value=10**6),
    owner=st.one_of(st.none(), st.integers(min_value=0, max_value=10**6)),
    user_can_change=st.one_of(st.none(), st.booleans()),
    is_insensitive=st.booleans(),
    match=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    matching_algorithm=st.one_of(st.none(), st.integers(min_value=0)),
)
@example(**d(correspondent_data, id=1, name="Test Correspondent", document_count=0, owner=None))
@example(**d(correspondent_data, id=10**6, name="X" * 255, document_count=10**6, owner=10**6))
#@example(**d(correspondent_data, id=-1, name="Valid Name", document_count=0)).xfail(raises=ValidationError, reason="ID cannot be negative")
#@example(**d(correspondent_data, id=1, name="A" * 256, document_count=0)).xfail(raises=ValidationError, reason="Name exceeds max length")
@example(**d(correspondent_data, id=2, name="Valid", document_count="invalid")).xfail(raises=ValidationError, reason="Document count must be an integer")
def test_fuzz_Correspondent(**kwargs) -> None:
    correspondent = Correspondent(resource=resource, **kwargs)  # type: ignore
    assert correspondent.id == kwargs.get("id", 0)
    assert correspondent.slug == kwargs.get("slug", None)
    assert correspondent.name == kwargs.get("name", None)
    assert correspondent.document_count == kwargs.get("document_count", 0)
    assert correspondent.owner == kwargs.get("owner", None)
    assert correspondent.user_can_change == kwargs.get("user_can_change", None)
