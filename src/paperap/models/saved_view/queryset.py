"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
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

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Self, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner

if TYPE_CHECKING:
    from paperap.models.saved_view.model import SavedView

logger = logging.getLogger(__name__)


class SavedViewQuerySet(StandardQuerySet["SavedView"], HasOwner):
    """
    QuerySet for Paperless-ngx saved views with specialized filtering methods.
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter saved views by name.

        Args:
            name: The saved view name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def show_in_sidebar(self, show: bool = True) -> Self:
        """
        Filter saved views by sidebar visibility.

        Args:
            show: If True, get views shown in sidebar, otherwise those hidden

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(show_in_sidebar=show)

    def show_on_dashboard(self, show: bool = True) -> Self:
        """
        Filter saved views by dashboard visibility.

        Args:
            show: If True, get views shown on dashboard, otherwise those hidden

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(show_on_dashboard=show)

    def sort_field(self, field: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter saved views by sort field.

        Args:
            field: The field to sort by
            exact: If True, match the exact field, otherwise use contains

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter_field_by_str("sort_field", field, exact=exact, case_insensitive=case_insensitive)

    def sort_reverse(self, reverse: bool = True) -> Self:
        """
        Filter saved views by sort direction.

        Args:
            reverse: If True, get views sorted in reverse order

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(sort_reverse=reverse)

    def page_size(self, size: int) -> Self:
        """
        Filter saved views by page size.

        Args:
            size: The number of items per page

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(page_size=size)

    def page_size_under(self, size: int) -> Self:
        """
        Filter saved views by page size under a limit.

        Args:
            size: The maximum number of items per page

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(page_size__lt=size)

    def page_size_over(self, size: int) -> Self:
        """
        Filter saved views by page size over a limit.

        Args:
            size: The minimum number of items per page

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(page_size__gt=size)

    def page_size_between(self, min_size: int, max_size: int) -> Self:
        """
        Filter saved views by page size within a range.

        Args:
            min_size: The minimum number of items per page
            max_size: The maximum number of items per page

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(page_size__gte=min_size, page_size__lte=max_size)

    def display_mode(self, mode: str) -> Self:
        """
        Filter saved views by display mode.

        Args:
            mode: The display mode to filter by

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(display_mode=mode)

    def user_can_change(self, can_change: bool = True) -> Self:
        """
        Filter saved views by user change permissions.

        Args:
            can_change: If True, get views that can be changed by the user

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(user_can_change=can_change)
