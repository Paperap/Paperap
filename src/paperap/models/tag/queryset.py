"""
Provide specialized query capabilities for Paperless-ngx tag resources.

This module implements the TagQuerySet class, which extends the standard
queryset functionality with tag-specific filtering methods. These methods
enable efficient and intuitive querying of tag resources based on their
unique attributes such as color, matching algorithm, and inbox status.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, Union

from paperap.models.abstract.queryset import BulkQuerySet
from paperap.models.mixins.queryset import HasStandard

if TYPE_CHECKING:
    from paperap.models.tag.model import Tag

logger = logging.getLogger(__name__)


class TagQuerySet(BulkQuerySet["Tag"], HasStandard):
    """
    Implement specialized filtering methods for Paperless-ngx tags.

    Extends StandardQuerySet to provide tag-specific filtering capabilities,
    including filtering by color, matching algorithm, inbox status, and other
    tag-specific attributes.

    The TagQuerySet provides a fluent interface for building complex queries
    against tag resources in the Paperless-ngx API.

    Examples:
        Get all inbox tags:
            >>> inbox_tags = client.tags.all().is_inbox_tag()

        Find tags with a specific color:
            >>> red_tags = client.tags.all().colour("#ff0000")

        Find tags that can be changed by the user:
            >>> editable_tags = client.tags.all().user_can_change()

    """

    def colour(self, value: str | int, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tags by color.

        Allows filtering tags based on their color attribute. The color can be specified
        as either a string (e.g., "#ff0000" for red) or an integer representation.

        Args:
            value: The color to filter by (string or integer).
            exact: If True, match the exact color, otherwise use contains matching.
                Defaults to True.
            case_insensitive: If True, ignore case when matching (for string values).
                Defaults to True.

        Returns:
            A filtered TagQuerySet containing only tags with matching colors.

        Examples:
            Find tags with red color:
                >>> red_tags = client.tags.all().colour("#ff0000")

            Find tags with colors containing "blue" (case insensitive):
                >>> blue_tags = client.tags.all().colour("blue", exact=False)

        """
        if isinstance(value, int):
            return self.filter(colour=value)
        return self.filter_field_by_str("colour", value, exact=exact, case_insensitive=case_insensitive)

    def match(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tags by match value.

        Filters tags based on their match pattern, which is used by Paperless-ngx
        for automatic tag assignment.

        Args:
            value: The match pattern value to filter by.
            exact: If True, match the exact value, otherwise use contains matching.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered TagQuerySet containing only tags with matching patterns.

        Examples:
            Find tags that match "invoice":
                >>> invoice_tags = client.tags.all().match("invoice")

            Find tags with match patterns containing "tax":
                >>> tax_tags = client.tags.all().match("tax", exact=False)

        """
        return self.filter_field_by_str("match", value, exact=exact, case_insensitive=case_insensitive)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter tags by matching algorithm.

        Filters tags based on the algorithm used for automatic tag assignment.
        Paperless-ngx supports different matching algorithms like exact, regex,
        fuzzy matching, etc., each represented by an integer value.

        Args:
            value: The matching algorithm ID to filter by. Common values include:
                1 (any), 2 (all), 3 (literal), 4 (regex), 5 (fuzzy match).

        Returns:
            A filtered TagQuerySet containing only tags using the specified
            matching algorithm.

        Examples:
            Find tags using regex matching:
                >>> regex_tags = client.tags.all().matching_algorithm(4)

        """
        return self.filter(matching_algorithm=value)

    def case_insensitive(self, value: bool = True) -> Self:
        """
        Filter tags by case insensitivity setting.

        Filters tags based on whether their matching is case insensitive or not.
        This affects how Paperless-ngx performs automatic tag assignment.

        Args:
            value: If True, returns tags configured for case-insensitive matching.
                If False, returns tags configured for case-sensitive matching.
                Defaults to True.

        Returns:
            A filtered TagQuerySet containing only tags with the specified
            case sensitivity setting.

        Examples:
            Find case-insensitive tags:
                >>> insensitive_tags = client.tags.all().case_insensitive()

            Find case-sensitive tags:
                >>> sensitive_tags = client.tags.all().case_insensitive(False)

        """
        return self.filter(is_insensitive=value)

    def is_inbox_tag(self, value: bool = True) -> Self:
        """
        Filter tags by inbox status.

        In Paperless-ngx, inbox tags are special tags that mark documents as needing
        attention or processing. This method filters tags based on whether they are
        designated as inbox tags.

        Args:
            value: If True, returns only inbox tags. If False, returns only non-inbox tags.
                Defaults to True.

        Returns:
            A filtered TagQuerySet containing only tags with the specified
            inbox status.

        Examples:
            Get all inbox tags:
                >>> inbox_tags = client.tags.all().is_inbox_tag()

            Get all non-inbox tags:
                >>> regular_tags = client.tags.all().is_inbox_tag(False)

        """
        return self.filter(is_inbox_tag=value)

    def user_can_change(self, value: bool = True) -> Self:
        """
        Filter tags by user change permission.

        Filters tags based on whether the current authenticated user has permission
        to modify them. This is useful for identifying which tags can be edited
        in user interfaces.

        Args:
            value: If True, returns tags that can be changed by the current user.
                If False, returns tags that cannot be changed by the current user.
                Defaults to True.

        Returns:
            A filtered TagQuerySet containing only tags with the specified
            change permission.

        Examples:
            Get tags the current user can modify:
                >>> editable_tags = client.tags.all().user_can_change()

            Get tags the current user cannot modify:
                >>> readonly_tags = client.tags.all().user_can_change(False)

        """
        return self.filter(user_can_change=value)
