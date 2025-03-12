"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    text_write.py
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
# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

import paperap.models.correspondent.model
import typing
from hypothesis import given, strategies as st

# TODO: replace st.nothing() with an appropriate strategy


@given(
    resource=st.none(),
    match=st.one_of(st.none(), st.text()),
    matching_algorithm=st.one_of(st.none(), st.integers()),
    is_insensitive=st.booleans(),
    id=st.integers(),
    slug=st.one_of(st.none(), st.text()),
    name=st.one_of(st.none(), st.text()),
    document_count=st.integers(),
    owner=st.one_of(st.none(), st.integers()),
    user_can_change=st.one_of(st.none(), st.booleans()),
)
def test_fuzz_Correspondent(
    resource,
    match: typing.Union[str, None],
    matching_algorithm: typing.Union[int, None],
    is_insensitive: bool,
    id: int,
    slug: typing.Union[str, None],
    name: typing.Union[str, None],
    document_count: int,
    owner: typing.Union[int, None],
    user_can_change: typing.Union[bool, None],
) -> None:
    paperap.models.correspondent.model.Correspondent(
        resource=resource,
        match=match,
        matching_algorithm=matching_algorithm,
        is_insensitive=is_insensitive,
        id=id,
        slug=slug,
        name=name,
        document_count=document_count,
        owner=owner,
        user_can_change=user_can_change,
    )


@given(
    resource=st.nothing(),
    filters=st.none(),
    _cache=st.none(),
    _fetch_all=st.booleans(),
    _next_url=st.none(),
    _last_response=st.none(),
    _iter=st.none(),
    _urls_fetched=st.none(),
)
def test_fuzz_CorrespondentQuerySet(
    resource,
    filters: typing.Optional[dict[str, typing.Any]],
    _cache: typing.Optional[list],
    _fetch_all: bool,
    _next_url: typing.Union[str, None],
    _last_response: typing.Optional[dict[str, typing.Any]],
    _iter: typing.Optional[typing.Iterator],
    _urls_fetched: typing.Optional[list[str]],
) -> None:
    paperap.models.correspondent.model.CorrespondentQuerySet(
        resource=resource,
        filters=filters,
        _cache=_cache,
        _fetch_all=_fetch_all,
        _next_url=_next_url,
        _last_response=_last_response,
        _iter=_iter,
        _urls_fetched=_urls_fetched,
    )
