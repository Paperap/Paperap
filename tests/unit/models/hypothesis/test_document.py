"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_document.py
        Project: paperap
        Created: 2025-03-12
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-12     By Jess Mann

"""
import datetime
import os
import paperap.models.document
import paperap.models.document.model
from typing import Any, Iterator, Union, Optional
from hypothesis import example, given, strategies as st
from paperap.models import CustomFieldDict, Document, DocumentNote, DocumentQuerySet
import paperap.models.document.parser
from paperap.tests import random_json, defaults as d
from paperap.client import PaperlessClient
from paperap.resources.correspondents import CorrespondentResource
from unittest.mock import patch
import json
import random
import string

# TODO: replace st.nothing() with an appropriate strategy

# patch env
env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
with patch.dict(os.environ, env_data, clear=True):
    client = PaperlessClient()
    resource = CorrespondentResource(client=client)

doc = {
    "id": 1,
    "added": datetime.datetime.now(),
    "archive_serial_number": 1,
    "archived_file_name": "test.pdf",
    "content": "Test content",
    "is_shared_by_requester": True,
    "notes": None,
    "original_file_name": "test.pdf",
    "owner": 1,
    "page_count": 1,
    "title": "Test title",
    "user_can_change": True,
    "created_on": datetime.datetime.now(),
    "created_date": "2025-03-12",
    "updated_on": datetime.datetime.now(),
    "deleted_at": None,
    "custom_field_dicts": None,
    "correspondent_id": 1,
    "document_type_id": 1,
    "storage_path_id": 1,
    "tag_ids": [],
}
@given(
    id=st.integers(min_value=0),
    added=st.one_of(st.none(), st.datetimes()),
    archive_serial_number=st.one_of(st.none(), st.integers(min_value=0, max_value=10**6)),
    archived_file_name=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    content=st.text(min_size=0, max_size=100000),
    is_shared_by_requester=st.booleans(),
    notes=st.lists(
        st.builds(
            DocumentNote,
            created=st.datetimes(),
            deleted_at=st.one_of(st.none(), st.datetimes()),
            document=st.integers(min_value=0),
            id=st.one_of(st.just(0), st.integers(min_value=0, max_value=10**6)),
            note=st.text(min_size=0, max_size=10000),
            restored_at=st.one_of(st.none(), st.datetimes()),
            transaction_id=st.one_of(st.none(), st.integers(min_value=0)),
            user=st.integers(min_value=0),
        )
    ),
    original_file_name=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    owner=st.one_of(st.none(), st.integers(min_value=0)),
    page_count=st.one_of(st.none(), st.integers(min_value=0, max_value=10**5)),
    title=st.text(min_size=1, max_size=300),
    user_can_change=st.one_of(st.none(), st.booleans()),
    created_on=st.one_of(st.none(), st.datetimes()),
    created_date=st.one_of(st.none(), st.text().map(lambda x: x[:10] if x else None)),  # Limit to YYYY-MM-DD
    updated_on=st.one_of(st.none(), st.datetimes()),
    deleted_at=st.one_of(st.none(), st.datetimes()),
    custom_field_dicts=st.one_of(st.lists(st.builds(CustomFieldDict)), st.none()),
    correspondent_id=st.one_of(st.none(), st.integers(min_value=0)),
    document_type_id=st.one_of(st.none(), st.integers(min_value=0)),
    storage_path_id=st.one_of(st.none(), st.integers(min_value=0)),
    tag_ids=st.lists(st.integers(min_value=0, max_value=10**6), max_size=1000),
)
@example(**d(doc, id=1, title="", content="", tag_ids=[]))  # Edge case: minimal data
@example(**d(doc, id=10**9, title="A"*300, content="B"*5000, tag_ids=[1, 2, 3]*100))  # Max limits
def test_fuzz_Document(**kwargs) -> None:
    Document(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining

@given(value=st.one_of(st.lists(st.builds(CustomFieldDict)), st.none()))
@example(value=None)
@example(value=[])
@example(value=[{"id":1, "value": None}])  # None value
@example(value=[{"id":10**9, "value": "x" * 100}])  # Large id, long text
@example(value=[{"id":123, "value": json.loads(random_json())}])  # Random JSON
def test_fuzz_document_validate_custom_fields(value: list[CustomFieldDict] | None) -> None:
    Document.validate_custom_fields(value=value)

@given(value=st.one_of(st.lists(st.builds(DocumentNote)), st.none()))
@example(value=None)
@example(value=[])
@example(value=[DocumentNote(id=0, note="", created=datetime.datetime.now(), document=1, user=1)])
@example(value=[DocumentNote(id=10**9, note="Extreme Note!", created=datetime.datetime.now(), document=2, user=2)])
def test_fuzz_document_validate_notes(value: list[DocumentNote] | None) -> None:
    Document.validate_notes(value=value)

@given(value=st.one_of(st.none(), st.booleans()))
@example(value=None)
@example(value=True)
@example(value=False)
def test_fuzz_document_validate_is_shared_by_requester(value: Union[bool, None]) -> None:
    Document.validate_is_shared_by_requester(value=value)

@given(value=st.one_of(st.none(), st.lists(st.integers())))
@example(value=None)
@example(value=[])
@example(value=[1, 2, 3])
@example(value=[10**6]*100)  # Large list
def test_fuzz_document_validate_tags(value: Union[list[int], None]) -> None:
    Document.validate_tags(value=value)

@given(value=st.one_of(st.none(), st.text()))
@example(value=None)
@example(value="")
@example(value="Hello, world!")
@example(value="𓀀𓂀𓃰")  # Unicode characters
def test_fuzz_document_validate_text(value: Union[str, None]) -> None:
    Document.validate_text(value=value)

note = {
    "id": 1,
    "deleted_at": None,
    "restored_at": None,
    "transaction_id": None,
    "note": "Test note",
    "created": datetime.datetime.now(),
    "document": 1,
    "user": 1,
}
@given(
    id=st.integers(min_value=1, max_value=10**6),
    deleted_at=st.one_of(st.none(), st.datetimes()),
    restored_at=st.one_of(st.none(), st.datetimes()),
    transaction_id=st.one_of(st.none(), st.integers()),
    note=st.text(min_size=0, max_size=1000),
    created=st.datetimes(),
    document=st.integers(),
    user=st.integers(),
)
@example(**d(note, id=0, note="", created=datetime.datetime.now(), document=1, user=1))
@example(**d(note, id=10**6, note="Extreme Case Note!", created=datetime.datetime.now(), document=99999, user=99999))
def test_fuzz_DocumentNote(**kwargs) -> None:
    DocumentNote(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining

@given(
    filters=st.one_of(st.none(), st.dictionaries(keys=st.text(), values=st.text())),
    _cache=st.one_of(st.none(), st.lists(st.dictionaries(keys=st.text(), values=st.text()))),
    _fetch_all=st.booleans(),
    _next_url=st.one_of(st.none(), st.text()),
    _last_response=st.one_of(st.none(), st.dictionaries(keys=st.text(), values=st.text())),
    _iter=st.one_of(st.none(), st.iterables(st.text())),
    _urls_fetched=st.one_of(st.none(), st.lists(st.text())),
)
def test_fuzz_DocumentQuerySet(**kwargs) -> None:
    DocumentQuerySet(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining
