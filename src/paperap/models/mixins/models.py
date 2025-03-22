"""



----------------------------------------------------------------------------

METADATA:

File:    models.py
        Project: paperap
Created: 2025-03-09
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-09     By Jess Mann

"""

from __future__ import annotations

from pydantic import Field

from paperap.const import MatchingAlgorithmType


class MatcherMixin:
    match: str | None = None
    matching_algorithm: MatchingAlgorithmType | None = Field(default=None, ge=MatchingAlgorithmType.UNKNOWN, le=7)
    is_insensitive: bool | None = None
