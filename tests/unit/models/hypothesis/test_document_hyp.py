

import datetime
import json
from typing import Union

from faker import Faker
from hypothesis import example, given
from hypothesis import strategies as st
from pydantic import ValidationError

from paperap.models import CustomFieldValues, Document, DocumentNote, DocumentQuerySet
from paperap.resources.documents import DocumentResource
from tests.lib import create_resource
from tests.lib import defaults as d
from tests.lib.factories import DocumentFactory, DocumentNoteFactory

resource = create_resource(DocumentResource)
doc = DocumentFactory.to_dict()
faker = Faker()

custom_field_strategy = st.fixed_dictionaries(
    {
        "field": st.integers(min_value=1, max_value=10**6),
        "value": st.one_of(
                 st.none(),
                 st.integers(),
                 st.floats(allow_nan=False),
                 st.booleans(),
                 st.text(min_size=1, max_size=200),
                 st.lists(st.integers(), max_size=10),
                 st.lists(st.text(), max_size=10),
                 st.dictionaries(keys=st.text(), values=st.integers(), max_size=5),
                 st.dictionaries(keys=st.text(), values=st.text(), max_size=5),
                 st.lists(
                    st.dictionaries(keys=st.text(), values=st.one_of(st.integers(), st.text())),
                    max_size=100
            ),
        )
    }
)


@given(
    id=st.integers(min_value=0),
    added=st.one_of(st.none(), st.datetimes()),
    archive_serial_number=st.one_of(st.none(), st.integers(min_value=0, max_value=10**6)),
    archived_file_name=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    archive_checksum=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    archive_filename=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    filename=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    storage_type=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
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
    original_filename=st.one_of(st.none(), st.text(min_size=0, max_size=255)),
    owner=st.one_of(st.none(), st.integers(min_value=0)),
    page_count=st.one_of(st.none(), st.integers(min_value=0, max_value=10**5)),
    title=st.text(min_size=1, max_size=300),
    user_can_change=st.one_of(st.none(), st.booleans()),
    created_date=st.one_of(st.none(), st.text().map(lambda x: x[:10] if x else None)),  # Limit to YYYY-MM-DD
    created=st.one_of(st.none(), st.datetimes()),
    deleted_at=st.one_of(st.none(), st.datetimes()),
    custom_field_dicts=st.one_of(st.lists(custom_field_strategy), st.none()),
    correspondent_id=st.one_of(st.none(), st.integers(min_value=0)),
    document_type_id=st.one_of(st.none(), st.integers(min_value=0)),
    storage_path_id=st.one_of(st.none(), st.integers(min_value=0)),
    tag_ids=st.lists(st.integers(min_value=0, max_value=10**6), max_size=1000),
    checksum=st.none(),
)
@example(**d(doc, id=1, title="", content="", tag_ids=[]))  # Edge case: minimal data
@example(**d(doc, id=10**9, title="A"*300, content="B"*5000, tag_ids=[1, 2, 3]*100))  # Max limits
@example(**d(doc, custom_field_dicts=[{}])).xfail(raises=ValidationError)
#@example(**d(doc, id=-1, title="Invalid", content="Valid", created_date="NotADate")).xfail(raises=ValueError)
#@example(**d(doc, id=1, title="A" * 301, content="Valid", created_date="2024-12-32")).xfail(raises=ValueError)
#@example(**d(doc, id=2, title="Valid", content="B" * 100001, created_date="2024-13-01")).xfail(raises=ValueError)
#@example(**d(doc, id=3, title="Valid", content="Valid", created_date="not-a-date")).xfail(raises=ValueError)
def test_fuzz_Document(**kwargs) -> None:
    document = Document(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining
    assert document.id == kwargs.get("id", 0)
    assert document.correspondent_id == kwargs.get("correspondent_id", None)
    assert document.document_type_id == kwargs.get("document_type_id", None)
    assert document.storage_path_id == kwargs.get("storage_path_id", None)
    assert document.title == str(kwargs.get("title", ""))
    assert document.content == str(kwargs.get("content", ""))
    assert document.page_count == kwargs.get("page_count", None)
    assert document.owner == kwargs.get("owner", None)
    assert document.user_can_change == kwargs.get("user_can_change", None)
    assert document.is_shared_by_requester == kwargs.get("is_shared_by_requester", False)
    assert document.archive_serial_number == kwargs.get("archive_serial_number", None)
    assert document.archived_file_name == kwargs.get("archived_file_name", None)
    assert document.original_filename == kwargs.get("original_filename", None)
    #assert document.created_date == kwargs.get("created_date", None)
    #assert document.created == kwargs.get("created", None)
    #assert document.deleted_at == kwargs.get("deleted_at", None)
    #assert document.added == kwargs.get("added", None)
    #assert document.custom_field_dicts == kwargs.get("custom_field_dicts", [])

@given(value=st.one_of(st.lists(custom_field_strategy), st.none()))
@example(value=None)
@example(value=[])
@example(value=[{"id":1, "value": None}])  # None value
@example(value=[{"id":10**9, "value": "x" * 100}])  # Large id, long text
@example(value=[{"id":123, "value": json.loads(faker.json())}])  # Random JSON
#@example(value=[None]).xfail(raises=ValueError)
#@example(value=[{"id":None, "value": None}]).xfail(raises=ValueError)
#@example(value=[{"value": "something"}]).xfail(raises=ValueError)
#@example(value=[{"id": 5}]).xfail(raises=ValueError)
def test_fuzz_document_validate_custom_fields(value: list[CustomFieldValues] | None) -> None:
    # Will raise error if invalid
    Document.validate_custom_fields(value=value)

@given(value=st.one_of(st.lists(st.builds(DocumentNote)), st.none()))
@example(value=None)
@example(value=[])
@example(value=[DocumentNote(id=0, note="", created=datetime.datetime.now(), document=1, user=1)])
@example(value=[DocumentNote(id=10**9, note="Extreme Note!", created=datetime.datetime.now(), document=2, user=2)])
def test_fuzz_document_validate_notes(value: list[DocumentNote] | None) -> None:
    # Will raise error if invalid
    Document.validate_notes(value=value)

@given(value=st.one_of(st.none(), st.booleans()))
@example(value=None)
@example(value=True)
@example(value=False)
def test_fuzz_document_validate_is_shared_by_requester(value: Union[bool, None]) -> None:
    # Will raise error if invalid
    Document.validate_is_shared_by_requester(value=value)

@given(value=st.one_of(st.none(), st.lists(st.integers())))
@example(value=None)
@example(value=[])
@example(value=[1, 2, 3])
@example(value=[10**6]*100)  # Large list
def test_fuzz_document_validate_tags(value: Union[list[int], None]) -> None:
    # Will raise error if invalid
    Document.validate_tags(value=value)

@given(value=st.one_of(st.none(), st.text()))
@example(value=None)
@example(value="")
@example(value="Hello, world!")
@example(value="𓀀𓂀𓃰")  # Unicode characters
def test_fuzz_document_validate_text(value: Union[str, None]) -> None:
    # Will raise error if invalid
    Document.validate_text(value=value)

    # Second test indirectly through instantiation
    document = DocumentFactory.create(content = value, title = value)

note = DocumentNoteFactory.to_dict()
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
#@example(**d(note, id=-1, note="Invalid", created=datetime.datetime.now(), document=1, user=1)).xfail(raises=ValueError)
#@example(**d(note, id=10**6, note="Extreme Case Note!", created=datetime.datetime.now(), document=99999, user=99999)).xfail(raises=ValueError)
def test_fuzz_DocumentNote(**kwargs) -> None:
    document_note = DocumentNote(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining
    assert document_note.id == kwargs.get("id", 0)
    assert document_note.note == str(kwargs.get("note", ""))
    assert document_note.user == kwargs.get("user", 0)
    #assert document_note.deleted_at == kwargs.get("deleted_at", None)
    #assert document_note.restored_at == kwargs.get("restored_at", None)
    #assert document_note.transaction_id == kwargs.get("transaction_id", None)
    #assert document_note.created == kwargs.get("created", None)
    #assert document_note.document == kwargs.get("document", 0)

queryset = {
    "filters": None,
    "_cache": None,
    "_fetch_all": False,
    "_next_url": None,
    "_last_response": None,
    "_iter": None,
    "_urls_fetched": None,
}

@given(
    filters=st.one_of(st.none(), st.dictionaries(keys=st.text(), values=st.text())),
    _cache=st.one_of(st.none(), st.lists(st.dictionaries(keys=st.text(), values=st.text()))),
    _fetch_all=st.booleans(),
    _next_url=st.one_of(st.none(), st.text()),
    _last_response=st.one_of(st.none(), st.dictionaries(keys=st.text(), values=st.text())),
    _iter=st.one_of(st.none(), st.iterables(st.text())),
    _urls_fetched=st.one_of(st.none(), st.lists(st.text())),
)
#@example(**d(queryset, filters=[1.0])).xfail(raises=ValueError)
#@example(**d(queryset, filters=[None])).xfail(raises=ValueError)
#@example(**d(queryset, filters=[-1])).xfail(raises=ValueError)
def test_fuzz_DocumentQuerySet(**kwargs) -> None:
    qs = DocumentQuerySet(resource=resource, **kwargs) # type: ignore # I'm not sure why pyright is complaining
    assert qs.filters == (kwargs.get("filters", {}) or {})
    #assert qs._cache == kwargs.get("_cache", None) # type: ignore
    assert qs._fetch_all == kwargs.get("_fetch_all", False) # type: ignore
    assert qs._next_url == kwargs.get("_next_url", None) # type: ignore
    assert qs._last_response == kwargs.get("_last_response", None) # type: ignore
    assert qs._iter == kwargs.get("_iter", None) # type: ignore
