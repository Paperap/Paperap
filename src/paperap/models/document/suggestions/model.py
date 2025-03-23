

from __future__ import annotations

from datetime import date
from typing import List

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
        read_only_fields = {"correspondents", "tags", "document_types", "storage_paths", "dates"}
