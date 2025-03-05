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
from typing import Any, TYPE_CHECKING, Self
import logging
import datetime

from paperap.models.abstract.queryset import QuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.share_links.model import ShareLinks

logger = logging.getLogger(__name__)


class ShareLinksQuerySet(StandardQuerySet["ShareLinks"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def expiration_before(self, value: datetime.datetime | str) -> Self:
        """
        Filter ShareLinks where expiration is before value

        Args:
            value (datetime.datetime | str): The value to compare against

        Returns:
            ShareLinksQuerySet: The filtered queryset
        """
        return self.filter(expiration__lt=value)

    def expiration_after(self, value: datetime.datetime | str) -> Self:
        """
        Filter ShareLinks where expiration is after value

        Args:
            value (datetime.datetime | str): The value to compare against

        Returns:
            ShareLinksQuerySet: The filtered queryset
        """
        return self.filter(expiration__gt=value)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter ShareLinks where slug is value

        Args:
            value (str): The value to compare against
            exact (bool): Whether the comparison should be exact
            case_sensitive (bool): Whether the comparison should be case insensitive

        Returns:
            ShareLinksQuerySet: The filtered queryset
        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)

    def document(self, value: int | list[int]) -> Self:
        """
        Filter ShareLinks where document is value

        Args:
            value (int | list[int]): The value to compare against

        Returns:
            ShareLinksQuerySet: The filtered queryset
        """
        if isinstance(value, int):
            return self.filter(document=value)
        return self.filter(document__in=value)

    def file_version(self, value: str) -> Self:
        """
        Filter ShareLinks where file_version is value

        Args:
            value (str): The value to compare against

        Returns:
            ShareLinksQuerySet: The filtered queryset
        """
        return self.filter(file_version=value)

    def created_before(self, date: datetime.datetime) -> Self:
        """
        Filter models created before a given date.

        Args:
            date: The date to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(created__lt=date)

    def created_after(self, date: datetime.datetime) -> Self:
        """
        Filter models created after a given date.

        Args:
            date: The date to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(created__gt=date)

    def created_between(self, start: datetime.datetime, end: datetime.datetime) -> Self:
        """
        Filter models created between two dates.

        Args:
            start: The start date to filter by
            end: The end date to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(created__range=(start, end))
