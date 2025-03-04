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

from paperap.models.base import PaperlessModel


class SavedView(PaperlessModel):
    """
    Represents a saved view in Paperless-NgX.
    """

    name: str
    sort_field: str
    sort_reverse: bool
    show_on_dashboard: bool
    show_in_sidebar: bool
    filter_rules: list[dict[str, Any]]
    owner: int | None = Field(default=None)
    user_can_change: bool = Field(default=False)

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"owner", "user_can_change"}
