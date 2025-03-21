"""
----------------------------------------------------------------------------

   METADATA:

       File:    saved_view.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from paperap.const import SavedViewDisplayFieldType, SavedViewDisplayModeType, SavedViewFilterRuleType
from paperap.models.abstract.model import StandardModel
from paperap.models.saved_view.queryset import SavedViewQuerySet

DEFAULT_DISPLAY_FIELDS = [
    SavedViewDisplayFieldType.TITLE,
    SavedViewDisplayFieldType.CREATED,
    SavedViewDisplayFieldType.TAGS,
    SavedViewDisplayFieldType.CORRESPONDENT,
    SavedViewDisplayFieldType.DOCUMENT_TYPE,
    SavedViewDisplayFieldType.STORAGE_PATH,
    SavedViewDisplayFieldType.NOTES,
    SavedViewDisplayFieldType.OWNER,
    SavedViewDisplayFieldType.SHARED,
    SavedViewDisplayFieldType.PAGE_COUNT,
]


class SavedView(StandardModel):
    """
    Represents a saved view in Paperless-NgX.
    """

    name: str
    show_on_dashboard: bool | None = None
    show_in_sidebar: bool | None = None
    sort_field: str | None = None
    sort_reverse: bool | None = None
    filter_rules: list[SavedViewFilterRuleType] = Field(default_factory=list)
    page_size: int | None = None
    display_mode: SavedViewDisplayModeType | None = None
    display_fields: list[SavedViewDisplayFieldType] = Field(default_factory=list)
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"owner", "user_can_change"}
        queryset = SavedViewQuerySet
