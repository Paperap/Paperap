"""
Provide queryset functionality for Paperless-ngx correspondents.

This module implements the CorrespondentQuerySet class, which enables
filtering and querying correspondent objects from the Paperless-ngx API.
It extends the standard queryset functionality with correspondent-specific
filtering methods.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, Union

from paperap.models.mixins.queryset import HasDocumentCount, HasOwner
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet, BulkQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent.model import Correspondent

logger = logging.getLogger(__name__)


class CorrespondentQuerySet(BulkQuerySet["Correspondent"], HasOwner, HasDocumentCount):
    """
    QuerySet for Paperless-ngx correspondents with specialized filtering methods.

    Extends StandardQuerySet to provide correspondent-specific filtering
    capabilities, including filtering by name, matching algorithm, and other
    correspondent attributes.

    Inherits document counting capabilities from HasDocumentCount
    and owner-related filtering from HasOwner.

    Examples:
        Get all correspondents:
            >>> correspondents = client.correspondents()

        Filter by name:
            >>> electric = client.correspondents().name("Electric Company")

        Find correspondents with case-insensitive matching:
            >>> insensitive = client.correspondents().case_insensitive(True)

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by name.

        Args:
            value: The correspondent name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, ignore case when matching.

        Returns:
            Filtered CorrespondentQuerySet.

        Examples:
            Find correspondents with exact name:
                >>> exact_match = client.correspondents().name("Electric Company")

            Find correspondents with name containing "electric":
                >>> contains = client.correspondents().name("electric", exact=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter correspondents by their matching algorithm.

        Paperless-ngx supports different algorithms for matching documents to
        correspondents. This method filters correspondents by the algorithm they use.

        Args:
            value: The matching algorithm ID to filter by.
                Common values include:
                1: Any word
                2: All words
                3: Exact match
                4: Regular expression
                5: Fuzzy match
                6: Auto

        Returns:
            Filtered CorrespondentQuerySet.

        """
        return self.filter(matching_algorithm=value)

    def match(self, match: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by their match pattern.

        The match pattern is the text pattern used by Paperless-ngx to automatically
        assign documents to this correspondent.

        Args:
            match: The match pattern to filter by.
            exact: If True, match the exact pattern, otherwise use contains.
            case_insensitive: If True, ignore case when matching.

        Returns:
            Filtered CorrespondentQuerySet.

        Examples:
            Find correspondents with match pattern containing "invoice":
                >>> invoice_matchers = client.correspondents().match("invoice", exact=False)

        """
        return self.filter_field_by_str("match", match, exact=exact, case_insensitive=case_insensitive)

    def case_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter correspondents by case sensitivity setting.

        Paperless-ngx allows correspondents to have case-sensitive or case-insensitive
        matching. This method filters correspondents based on that setting.

        Args:
            insensitive: If True, get correspondents with case-insensitive matching.
                If False, get correspondents with case-sensitive matching.

        Returns:
            Filtered CorrespondentQuerySet.

        """
        return self.filter(is_insensitive=insensitive)

    def user_can_change(self, value: bool = True) -> Self:
        """
        Filter correspondents by user change permission.

        In Paperless-ngx, some correspondents may be restricted from modification
        by certain users based on permissions. This method filters correspondents
        based on whether the current user can change them.

        Args:
            value: If True, get correspondents that can be changed by the current user.
                If False, get correspondents that cannot be changed by the current user.

        Returns:
            Filtered CorrespondentQuerySet.

        """
        return self.filter(user_can_change=value)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by slug.

        Slugs are URL-friendly versions of the correspondent name used in the
        Paperless-ngx web interface and API. This method filters correspondents
        based on their slug value.

        Args:
            value: The slug to filter by.
            exact: If True, match the exact slug, otherwise use contains.
            case_insensitive: If True, ignore case when matching.

        Returns:
            Filtered CorrespondentQuerySet.

        Examples:
            Find correspondent with slug "electric-company":
                >>> electric = client.correspondents().slug("electric-company")

        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)
