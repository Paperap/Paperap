"""
----------------------------------------------------------------------------

   METADATA:

       File:    parser.py
        Project: paperap
       Created: 2025-03-08
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-08     By Jess Mann

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast, override

from typing_extensions import TypeVar

if TYPE_CHECKING:
    from paperap.models.document.model import Document


class CustomFieldDict(TypedDict):
    field: int
    value: Any
