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

from typing import Any, List, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent.model import Correspondent

logger = logging.getLogger(__name__)


class CorrespondentQuerySet(QuerySet["Correspondent"]):
    """
    QuerySet for Paperless-ngx correspondents with specialized filtering methods.
    """

    def with_name(self, name: str, exact: bool = True) -> Self:
        """
        Filter correspondents by name.

        Args:
            name: The correspondent name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered CorrespondentQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def with_ids(self, ids: List[int]) -> Self:
        """
        Filter correspondents by multiple IDs.

        Args:
            ids: List of correspondent IDs to filter by

        Returns:
            Filtered CorrespondentQuerySet
        """
        ids_param = ",".join(str(id) for id in ids)
        return self.filter(id__in=ids_param)

    def with_matching_rule(self, rule_pattern: str) -> Self:
        """
        Filter correspondents by their matching rule pattern.

        Args:
            rule_pattern: The pattern to search for in matching rules

        Returns:
            Filtered CorrespondentQuerySet
        """
        return self.filter(matching_algorithm__contains=rule_pattern)

    def is_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter correspondents by case sensitivity setting.

        Args:
            insensitive: If True, get correspondents with case insensitive matching

        Returns:
            Filtered CorrespondentQuerySet
        """
        return self.filter(is_insensitive=insensitive)
