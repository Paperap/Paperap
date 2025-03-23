

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, Union

from paperap.models.mixins.queryset import HasDocumentCount, HasOwner
from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent.model import Correspondent

logger = logging.getLogger(__name__)


class CorrespondentQuerySet(StandardQuerySet["Correspondent"], HasOwner, HasDocumentCount):
    """
    QuerySet for Paperless-ngx correspondents with specialized filtering methods.
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by name.

        Args:
            name: The correspondent name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter correspondents by their matching algorithm.

        Args:
            value: The matching algorithm ID to filter by

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter(matching_algorithm=value)

    def match(self, match: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by match.

        Args:
            match: The match to filter by
            exact: If True, match the exact match, otherwise use contains

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter_field_by_str("match", match, exact=exact, case_insensitive=case_insensitive)

    def case_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter correspondents by case sensitivity setting.

        Args:
            insensitive: If True, get correspondents with case insensitive matching

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter(is_insensitive=insensitive)

    def user_can_change(self, value: bool = True) -> Self:
        """
        Filter correspondents by user change permission.

        Args:
            value: If True, get correspondents that can be changed by user

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter(user_can_change=value)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by slug.

        Args:
            value: The slug to filter by
            exact: If True, match the exact slug, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered CorrespondentQuerySet

        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)
