"""
Model mixins for Paperless-ngx models.

This module provides mixins that can be used to add common functionality to models
that interact with the Paperless-ngx API.
"""

from __future__ import annotations

from pydantic import Field

from paperap.const import MatchingAlgorithmType


class MatcherMixin:
    """
    Mixin for models that support automatic matching functionality.

    This mixin provides fields and functionality for models that can be automatically
    matched against documents using Paperless-ngx's matching algorithms. Models like
    Correspondent, DocumentType, and StoragePath use this mixin to implement their
    matching behavior.

    Attributes:
        match (str | None): The text pattern to match against document content or metadata.
            When a document is processed, this pattern is used to determine if the document
            should be associated with this model instance.

        matching_algorithm (MatchingAlgorithmType | None): The algorithm to use for matching.
            Possible values are defined in the MatchingAlgorithmType enum, including options
            like exact match, regular expression, fuzzy match, etc. Defaults to None.

        is_insensitive (bool | None): Whether the matching should be case-insensitive.
            If True, the match pattern will be applied without considering letter case.
            If None, the system default will be used.

    Examples:
        ```python
        # Creating a correspondent with matching rules
        correspondent = Correspondent(
            name="Electric Company",
            match="electric bill",
            matching_algorithm=MatchingAlgorithmType.ANY_WORD,
            is_insensitive=True
        )

        # This correspondent will be automatically assigned to documents
        # containing any of the words "electric" or "bill" (case-insensitive)
        ```

    """

    match: str | None = None
    matching_algorithm: MatchingAlgorithmType | None = Field(
        default=None, ge=-1, le=7, description="Algorithm used for matching documents to this entity"
    )
    is_insensitive: bool | None = None
