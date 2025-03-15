"""



----------------------------------------------------------------------------

METADATA:

File:    list.py
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

from paperap.models.abstract import StandardModel


class ListResponse(StandardModel):
    """
    Not currently used, but kept for documentation or future expansion.

    The structure of an api response from paperless ngx for a list of models.
    """

    count: int
    next: str | None
    previous: str | None
    all: list[int]
    results: list[StandardModel]
