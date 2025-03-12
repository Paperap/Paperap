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
from hypothesis import given, strategies as st
from paperap.models.document import CustomFieldDict
from paperap.models.document.model import DocumentNote
import paperap.models.document.parser
from paperap.client import PaperlessClient
from paperap.resources.correspondents import CorrespondentResource
from unittest.mock import patch

# TODO: replace st.nothing() with an appropriate strategy

# patch env
env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
with patch.dict(os.environ, env_data, clear=True):
    client = PaperlessClient()
    resource = CorrespondentResource(client=client)

@given(
    id=st.integers(),
    added=st.none(),
    archive_serial_number=st.none(),
    archived_file_name=st.none(),
    content=st.text(),
    is_shared_by_requester=st.booleans(),
    notes=st.lists(
        st.builds(
            DocumentNote,
            created=st.datetimes(),
            deleted_at=st.one_of(st.none(), st.none(), st.datetimes()),
            document=st.integers(),
            id=st.one_of(st.just(0), st.integers()),
            note=st.text(),
            restored_at=st.one_of(st.none(), st.none(), st.datetimes()),
            transaction_id=st.one_of(st.none(), st.none(), st.integers()),
            user=st.integers(),
        )
    ),
    original_file_name=st.none(),
    owner=st.none(),
    page_count=st.none(),
    title=st.text(),
    user_can_change=st.none(),
    created_on=st.none(),
    created_date=st.none(),
    updated_on=st.none(),
    deleted_at=st.none(),
    custom_field_dicts=st.from_type(
        list[paperap.models.document.parser.CustomFieldDict]
    ),
    correspondent_id=st.none(),
    document_type_id=st.none(),
    storage_path_id=st.none(),
    tag_ids=st.lists(st.integers()),
)
def test_fuzz_Document(
    id: int,
    added: Union[datetime.datetime, None],
    archive_serial_number: Union[int, None],
    archived_file_name: Union[str, None],
    content: str,
    is_shared_by_requester: bool,
    notes: list[paperap.models.document.model.DocumentNote],
    original_file_name: Union[str, None],
    owner: Union[int, None],
    page_count: Union[int, None],
    title: str,
    user_can_change: Union[bool, None],
    created_on: Union[datetime.datetime, None],
    created_date: Union[str, None],
    updated_on: Union[datetime.datetime, None],
    deleted_at: Union[datetime.datetime, None],
    custom_field_dicts: list[paperap.models.document.CustomFieldDict],
    correspondent_id: Union[int, None],
    document_type_id: Union[int, None],
    storage_path_id: Union[int, None],
    tag_ids: list[int],
) -> None:
    paperap.models.document.model.Document(
        resource=resource,
        id=id,
        added=added,
        archive_serial_number=archive_serial_number,
        archived_file_name=archived_file_name,
        content=content,
        is_shared_by_requester=is_shared_by_requester,
        notes=notes,
        original_file_name=original_file_name,
        owner=owner,
        page_count=page_count,
        title=title,
        user_can_change=user_can_change,
        created_on=created_on,
        created_date=created_date,
        updated_on=updated_on,
        deleted_at=deleted_at,
        custom_field_dicts=custom_field_dicts,
        correspondent_id=correspondent_id,
        document_type_id=document_type_id,
        storage_path_id=storage_path_id,
        tag_ids=tag_ids,
    )


@given(
    value=st.from_type(
        list[paperap.models.document.parser.CustomFieldDict] | None
    )
)
def test_fuzz_Document_validate_custom_fields(
    value: Union[list[paperap.models.document.CustomFieldDict], None],
) -> None:
    paperap.models.document.model.Document.validate_custom_fields(value=value)


@given(value=st.one_of(st.none(), st.booleans()))
def test_fuzz_Document_validate_is_shared_by_requester(
    value: Union[bool, None],
) -> None:
    paperap.models.document.model.Document.validate_is_shared_by_requester(value=value)


@given(value=st.from_type(list[Any] | None))
def test_fuzz_Document_validate_notes(
    value: Union[list[Any], None],
) -> None:
    paperap.models.document.model.Document.validate_notes(value=value)


@given(value=st.one_of(st.none(), st.lists(st.integers())))
def test_fuzz_Document_validate_tags(value: Union[list[int], None]) -> None:
    paperap.models.document.model.Document.validate_tags(value=value)


@given(value=st.one_of(st.none(), st.text()))
def test_fuzz_Document_validate_text(value: Union[str, None]) -> None:
    paperap.models.document.model.Document.validate_text(value=value)


@given(
    id=st.integers(),
    deleted_at=st.one_of(st.none(), st.datetimes()),
    restored_at=st.one_of(st.none(), st.datetimes()),
    transaction_id=st.one_of(st.none(), st.integers()),
    note=st.text(),
    created=st.datetimes(),
    document=st.integers(),
    user=st.integers(),
)
def test_fuzz_DocumentNote(
    id: int,
    deleted_at: Union[datetime.datetime, None],
    restored_at: Union[datetime.datetime, None],
    transaction_id: Union[int, None],
    note: str,
    created: datetime.datetime,
    document: int,
    user: int,
) -> None:
    paperap.models.document.model.DocumentNote(
        resource=resource,
        id=id,
        deleted_at=deleted_at,
        restored_at=restored_at,
        transaction_id=transaction_id,
        note=note,
        created=created,
        document=document,
        user=user,
    )


@given(
    filters=st.none(),
    _cache=st.none(),
    _fetch_all=st.booleans(),
    _next_url=st.none(),
    _last_response=st.none(),
    _iter=st.none(),
    _urls_fetched=st.none(),
)
def test_fuzz_DocumentQuerySet(
    filters: Optional[dict[str, Any]],
    _cache: Optional[list],
    _fetch_all: bool,
    _next_url: Union[str, None],
    _last_response: Optional[dict[str, Any]],
    _iter: Optional[Iterator],
    _urls_fetched: Optional[list[str]],
) -> None:
    paperap.models.document.model.DocumentQuerySet(
        resource=resource,
        filters=filters,
        _cache=_cache,
        _fetch_all=_fetch_all,
        _next_url=_next_url,
        _last_response=_last_response,
        _iter=_iter,
        _urls_fetched=_urls_fetched,
    )

