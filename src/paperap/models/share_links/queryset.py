"""
Provide query functionality for ShareLinks resources in Paperless-NgX.

Contains the ShareLinksQuerySet class, which extends StandardQuerySet
to provide specialized filtering methods for ShareLinks resources. Enables
efficient querying of share links by various attributes such as expiration date,
document association, and creation time.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.share_links.model import ShareLinks

logger = logging.getLogger(__name__)


class ShareLinksQuerySet(StandardQuerySet["ShareLinks"]):
    """
    Implement a lazy-loaded, chainable query interface for ShareLinks resources.

    Extends StandardQuerySet to provide ShareLinks-specific filtering methods,
    including filtering by expiration date, slug, document, and file version.
    Only fetches data when it's actually needed, providing pagination, filtering,
    and caching functionality similar to Django's QuerySet.

    Examples:
        Get all share links:
            >>> all_links = client.share_links.all()

        Filter by document ID:
            >>> doc_links = client.share_links.filter(document=123)

        Find links that expire soon:
            >>> import datetime
            >>> tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            >>> expiring_soon = client.share_links.expiration_before(tomorrow)

    """

    def expiration_before(self, value: datetime.datetime | str) -> Self:
        """
        Filter ShareLinks where expiration date is before the specified value.

        Args:
            value: The datetime or ISO-formatted string to compare against.
                If a string is provided, it should be in ISO format (YYYY-MM-DDTHH:MM:SSZ).

        Returns:
            Self: A filtered queryset containing only ShareLinks that expire before the given date.

        Examples:
            Find links expiring in the next week:
                >>> next_week = datetime.datetime.now() + datetime.timedelta(days=7)
                >>> expiring_soon = client.share_links.expiration_before(next_week)

            Using string format:
                >>> expiring_soon = client.share_links.expiration_before("2023-12-31T23:59:59Z")

        """
        return self.filter(expiration__lt=value)

    def expiration_after(self, value: datetime.datetime | str) -> Self:
        """
        Filter ShareLinks where expiration date is after the specified value.

        Args:
            value: The datetime or ISO-formatted string to compare against.
                If a string is provided, it should be in ISO format (YYYY-MM-DDTHH:MM:SSZ).

        Returns:
            Self: A filtered queryset containing only ShareLinks that expire after the given date.

        Examples:
            Find links that haven't expired yet:
                >>> now = datetime.datetime.now()
                >>> valid_links = client.share_links.expiration_after(now)

        """
        return self.filter(expiration__gt=value)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter ShareLinks by their slug value.

        The slug is a unique identifier for the share link that appears in the URL.

        Args:
            value: The slug value to filter by.
            exact: If True, matches the exact slug. If False, performs a contains search.
            case_insensitive: If True, performs case-insensitive matching.
                If False, matching is case-sensitive.

        Returns:
            Self: A filtered queryset containing ShareLinks matching the slug criteria.

        Examples:
            Find a specific share link by its exact slug:
                >>> link = client.share_links.slug("abc123def")

            Find links containing a substring in their slug:
                >>> links = client.share_links.slug("invoice", exact=False)

        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)

    def document(self, value: int | list[int]) -> Self:
        """
        Filter ShareLinks by associated document ID(s).

        Args:
            value: Either a single document ID or a list of document IDs to filter by.
                When a list is provided, links associated with any of the documents will be returned.

        Returns:
            Self: A filtered queryset containing ShareLinks associated with the specified document(s).

        Examples:
            Find all share links for a specific document:
                >>> doc_links = client.share_links.document(123)

            Find links for multiple documents:
                >>> multi_doc_links = client.share_links.document([123, 456, 789])

        """
        if isinstance(value, int):
            return self.filter(document=value)
        return self.filter(document__in=value)

    def file_version(self, value: str) -> Self:
        """
        Filter ShareLinks by file version.

        In Paperless-NgX, share links can be created for specific versions of a document.
        This method filters links by their associated file version.

        Args:
            value: The file version string to filter by (e.g., "archive", "original").

        Returns:
            Self: A filtered queryset containing ShareLinks with the specified file version.

        Examples:
            Find all share links for original document versions:
                >>> original_links = client.share_links.file_version("original")

            Find all share links for archived versions:
                >>> archive_links = client.share_links.file_version("archive")

        """
        return self.filter(file_version=value)

    def created_before(self, date: datetime.datetime) -> Self:
        """
        Filter ShareLinks created before a given date.

        Args:
            date: The datetime to compare against. ShareLinks created before this
                datetime will be included in the results.

        Returns:
            Self: A filtered queryset containing ShareLinks created before the specified date.

        Examples:
            Find links created before last month:
                >>> last_month = datetime.datetime.now() - datetime.timedelta(days=30)
                >>> old_links = client.share_links.created_before(last_month)

        """
        return self.filter(created__lt=date)

    def created_after(self, date: datetime.datetime) -> Self:
        """
        Filter ShareLinks created after a given date.

        Args:
            date: The datetime to compare against. ShareLinks created after this
                datetime will be included in the results.

        Returns:
            Self: A filtered queryset containing ShareLinks created after the specified date.

        Examples:
            Find links created in the last week:
                >>> last_week = datetime.datetime.now() - datetime.timedelta(days=7)
                >>> recent_links = client.share_links.created_after(last_week)

        """
        return self.filter(created__gt=date)

    def created_between(self, start: datetime.datetime, end: datetime.datetime) -> Self:
        """
        Filter ShareLinks created between two dates.

        Args:
            start: The start datetime. ShareLinks created at or after this datetime
                will be included in the results.
            end: The end datetime. ShareLinks created at or before this datetime
                will be included in the results.

        Returns:
            Self: A filtered queryset containing ShareLinks created within the specified date range.

        Examples:
            Find links created in January 2023:
                >>> start = datetime.datetime(2023, 1, 1)
                >>> end = datetime.datetime(2023, 1, 31, 23, 59, 59)
                >>> jan_links = client.share_links.created_between(start, end)

        """
        return self.filter(created__range=(start, end))
