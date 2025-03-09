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
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner, HasDocumentCount

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

    def matching_algorithm(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter correspondents by their matching rule pattern.

        Args:
            rule_pattern: The pattern to search for in matching rules

        Returns:
            Filtered CorrespondentQuerySet
        """
        return self.filter_field_by_str("matching_algorithm", value, exact=exact, case_insensitive=case_insensitive)

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

    def user_can_change(self, value: bool) -> Self:
        """
        Filter correspondents by user_can_change.

        Args:
            value: The value to filter by

        Returns:
            Filtered CorrespondentQuerySet
        """
        return self.filter(user_can_change=value)
