"""
----------------------------------------------------------------------------

METADATA:

File:    suggestions.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.8
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from paperap.models.abstract import StandardModel


class DocumentSuggestions(StandardModel):
    """
    Represents suggestions for a Paperless-NgX document.

    Attributes:
        correspondents: List of suggested correspondent IDs.
        tags: List of suggested tag IDs.
        document_types: List of suggested document type IDs.
        storage_paths: List of suggested storage path IDs.
        dates: List of suggested dates.

    """

    correspondents: list[int] = []
    tags: list[int] = []
    document_types: list[int] = []
    storage_paths: list[int] = []
    dates: list[date] = []

    class Meta(StandardModel.Meta):
        read_only_fields = {
            "correspondents", "tags", "document_types", "storage_paths", "dates"
        }
