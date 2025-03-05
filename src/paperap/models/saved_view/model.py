"""




----------------------------------------------------------------------------

   METADATA:

       File:    saved_view.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import PaperlessModel
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


class SavedView(PaperlessModel):
    """
    Represents a saved view in Paperless-NgX.
    """

    name: str
    show_on_dashboard: bool
    show_in_sidebar: bool
    sort_field: str
    sort_reverse: bool
    filter_rules: list[dict[str, Any]]
    page_size: int | None = None
    display_mode: str = "smallCards"
    display_fields: list[str] = Field(default_factory=lambda: DEFAULT_DISPLAY_FIELDS)
    owner: int | None = None
    user_can_change: bool = True

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"owner", "user_can_change"}
        queryset = SavedViewQuerySet
