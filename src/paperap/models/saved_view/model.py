"""
Saved View Model Module.

This module defines the SavedView model class, which represents saved views in Paperless-NgX.
Saved views store filter configurations, display settings, and other view preferences
that users can save and reuse.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from paperap.const import SavedViewDisplayFieldType, SavedViewDisplayModeType, SavedViewFilterRuleType
from paperap.models.abstract.model import StandardModel
from paperap.models.saved_view.queryset import SavedViewQuerySet

# Default display fields for saved views if none are specified
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
    Represents a saved view configuration in Paperless-NgX.

    A saved view stores filter rules, sorting preferences, display settings, and other
    view configuration that can be saved and reused. Saved views can appear on the
    dashboard and/or sidebar for quick access.

    Attributes:
        name: The display name of the saved view.
        show_on_dashboard: Whether this view should be shown on the dashboard.
        show_in_sidebar: Whether this view should be shown in the sidebar.
        sort_field: The field to sort results by (e.g., "created", "title").
        sort_reverse: Whether to sort in reverse/descending order.
        filter_rules: List of filter rules to apply to documents.
        page_size: Number of documents to show per page.
        display_mode: How to display documents (e.g., list, grid).
        display_fields: Which fields to display in the view.
        owner: ID of the user who owns this saved view.
        user_can_change: Whether the current user can modify this saved view.

    Examples:
        >>> # Create a new saved view for tax documents
        >>> tax_view = client.saved_views.create(
        ...     name="Tax Documents",
        ...     show_on_dashboard=True,
        ...     show_in_sidebar=True,
        ...     filter_rules=[
        ...         {"rule_type": "document_type", "value": "5"}
        ...     ]
        ... )
        >>>
        >>> # Update an existing saved view
        >>> view = client.saved_views.get(3)
        >>> view.filter_rules.append({"rule_type": "correspondent", "value": "7"})
        >>> view.save()

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
        """
        Metadata for the SavedView model.

        This class defines metadata for the SavedView model, including read-only fields
        and the associated queryset class.

        Attributes:
            read_only_fields: Set of field names that cannot be modified by the client.
            queryset: The queryset class to use for this model.

        """

        # Fields that should not be modified
        read_only_fields = {"owner", "user_can_change"}
        queryset = SavedViewQuerySet
