"""
Provide query functionality for Paperless-ngx saved views.

This module contains the SavedViewQuerySet class which extends StandardQuerySet
to provide specialized filtering methods for saved views. It enables efficient
querying of saved views based on their attributes such as name, visibility settings,
sort options, and display preferences.
"""

from __future__ import annotations

import datetime
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner

if TYPE_CHECKING:
    from paperap.models.saved_view.model import SavedView

logger = logging.getLogger(__name__)


class SavedViewQuerySet(StandardQuerySet["SavedView"], HasOwner):
    """
    QuerySet for Paperless-ngx saved views with specialized filtering methods.

    Extends StandardQuerySet to provide saved view-specific filtering methods,
    including filtering by name, visibility settings, sort options, and display
    preferences. Allows for precise querying of saved views based on their
    attributes and configuration.

    Examples:
        >>> # Get all saved views shown in the sidebar
        >>> sidebar_views = client.saved_views.filter().show_in_sidebar()
        >>>
        >>> # Get dashboard views with large page sizes
        >>> large_views = client.saved_views.filter().show_on_dashboard().page_size_over(50)

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter saved views by name.

        Args:
            value: The saved view name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views with exact name match
            >>> tax_views = client.saved_views.filter().name("Tax Documents")
            >>>
            >>> # Find views containing "invoice" (case-insensitive)
            >>> invoice_views = client.saved_views.filter().name("invoice", exact=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def show_in_sidebar(self, show: bool = True) -> Self:
        """
        Filter saved views by sidebar visibility.

        Args:
            show: If True, get views shown in sidebar, otherwise those hidden.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Get views shown in sidebar
            >>> sidebar_views = client.saved_views.filter().show_in_sidebar()
            >>>
            >>> # Get views not shown in sidebar
            >>> hidden_views = client.saved_views.filter().show_in_sidebar(False)

        """
        return self.filter(show_in_sidebar=show)

    def show_on_dashboard(self, show: bool = True) -> Self:
        """
        Filter saved views by dashboard visibility.

        Args:
            show: If True, get views shown on dashboard, otherwise those hidden.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Get views shown on dashboard
            >>> dashboard_views = client.saved_views.filter().show_on_dashboard()
            >>>
            >>> # Get views not shown on dashboard
            >>> non_dashboard_views = client.saved_views.filter().show_on_dashboard(False)

        """
        return self.filter(show_on_dashboard=show)

    def sort_field(self, field: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter saved views by sort field.

        Args:
            field: The field to sort by (e.g., "created", "title").
            exact: If True, match the exact field name, otherwise use contains.
            case_insensitive: If True, perform case-insensitive matching.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views sorted by created date
            >>> date_sorted = client.saved_views.filter().sort_field("created")
            >>>
            >>> # Find views with sort fields containing "date"
            >>> date_fields = client.saved_views.filter().sort_field("date", exact=False)

        """
        return self.filter_field_by_str("sort_field", field, exact=exact, case_insensitive=case_insensitive)

    def sort_reverse(self, reverse: bool = True) -> Self:
        """
        Filter saved views by sort direction.

        Args:
            reverse: If True, get views sorted in reverse (descending) order,
                if False, get views sorted in normal (ascending) order.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Get views with descending sort
            >>> desc_views = client.saved_views.filter().sort_reverse()
            >>>
            >>> # Get views with ascending sort
            >>> asc_views = client.saved_views.filter().sort_reverse(False)

        """
        return self.filter(sort_reverse=reverse)

    def page_size(self, size: int) -> Self:
        """
        Filter saved views by exact page size.

        Args:
            size: The exact number of items per page to filter by.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views with 25 items per page
            >>> standard_views = client.saved_views.filter().page_size(25)

        """
        return self.filter(page_size=size)

    def page_size_under(self, size: int) -> Self:
        """
        Filter saved views by page size under a specified limit.

        Args:
            size: The maximum number of items per page (exclusive).

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views with fewer than 20 items per page
            >>> small_views = client.saved_views.filter().page_size_under(20)

        """
        return self.filter(page_size__lt=size)

    def page_size_over(self, size: int) -> Self:
        """
        Filter saved views by page size over a specified limit.

        Args:
            size: The minimum number of items per page (exclusive).

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views with more than 50 items per page
            >>> large_views = client.saved_views.filter().page_size_over(50)

        """
        return self.filter(page_size__gt=size)

    def page_size_between(self, min_size: int, max_size: int) -> Self:
        """
        Filter saved views by page size within a specified range.

        Args:
            min_size: The minimum number of items per page (inclusive).
            max_size: The maximum number of items per page (inclusive).

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views with between 20 and 50 items per page
            >>> medium_views = client.saved_views.filter().page_size_between(20, 50)

        """
        return self.filter(page_size__gte=min_size, page_size__lte=max_size)

    def display_mode(self, mode: str) -> Self:
        """
        Filter saved views by display mode.

        Args:
            mode: The display mode to filter by (e.g., "list", "grid", "details").

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views using list display mode
            >>> list_views = client.saved_views.filter().display_mode("list")
            >>>
            >>> # Find views using grid display mode
            >>> grid_views = client.saved_views.filter().display_mode("grid")

        """
        return self.filter(display_mode=mode)

    def user_can_change(self, can_change: bool = True) -> Self:
        """
        Filter saved views by user change permissions.

        Args:
            can_change: If True, get views that can be changed by the current user,
                if False, get views that cannot be changed by the current user.

        Returns:
            Self: Filtered SavedViewQuerySet.

        Examples:
            >>> # Find views the current user can modify
            >>> editable_views = client.saved_views.filter().user_can_change()
            >>>
            >>> # Find views the current user cannot modify
            >>> readonly_views = client.saved_views.filter().user_can_change(False)

        """
        return self.filter(user_can_change=can_change)
