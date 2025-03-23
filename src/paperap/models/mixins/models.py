

from __future__ import annotations

from pydantic import Field

from paperap.const import MatchingAlgorithmType


class MatcherMixin:
    match: str | None = None
    matching_algorithm: MatchingAlgorithmType | None = Field(default=None, ge=MatchingAlgorithmType.UNKNOWN, le=7)
    is_insensitive: bool | None = None
