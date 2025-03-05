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

from typing import Any, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.saved_view.model import SavedView

logger = logging.getLogger(__name__)


class SavedViewQuerySet(QuerySet["SavedView"]):
    """
    QuerySet for Paperless-ngx saved views with specialized filtering methods.
    """

    def with_name(self, name: str, *, exact: bool = True) -> Self:
        """
        Filter saved views by name.

        Args:
            name: The saved view name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered SavedViewQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def is_show_in_sidebar(self, show: bool = True) -> Self:
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

    def is_public(self, public: bool = True) -> Self:
        """
        Filter saved views by public status.

        Args:
            public: If True, get public views, otherwise private views

        Returns:
            Filtered SavedViewQuerySet
        """
        return self.filter(public=public)
