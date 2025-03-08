"""




----------------------------------------------------------------------------

   METADATA:

       File:    saved_view.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.saved_view.queryset import SavedViewQuerySet

DEFAULT_DISPLAY_FIELDS = [
    "title",
    "created",
    "tag",
    "correspondent",
    "documenttype",
    "storagepath",
    "note",
    "owner",
    "shared",
    "pagecount",
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
    filter_rules: list[dict[str, Any]] = Field(default_factory=list)
    page_size: int | None = None
    display_mode: str | None = None
    display_fields: list[str] = Field(default_factory=list)
    owner: int | None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"owner", "user_can_change"}
        queryset = SavedViewQuerySet
