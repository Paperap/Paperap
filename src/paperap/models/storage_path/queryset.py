

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasStandard

if TYPE_CHECKING:
    from paperap.models.storage_path.model import StoragePath

logger = logging.getLogger(__name__)


class StoragePathQuerySet(StandardQuerySet["StoragePath"], HasStandard):
    """
    QuerySet for Paperless-ngx storage paths with specialized filtering methods.
    """

    def path(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter storage paths by their actual path value.

        Args:
            value: The path to filter by
            exact: If True, match the exact path, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered StoragePathQuerySet

        """
        return self.filter_field_by_str("path", value, exact=exact, case_insensitive=case_insensitive)

    def match(self, value: str, *, exact: bool = True) -> Self:
        """
        Filter storage paths by match value.

        Args:
            value: The match value to filter by
            exact: If True, match the exact match value, otherwise use contains

        Returns:
            Filtered StoragePathQuerySet

        """
        return self.filter_field_by_str("match", value, exact=exact)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter storage paths by matching algorithm.

        Args:
            value: The matching algorithm to filter by

        Returns:
            Filtered StoragePathQuerySet

        """
        return self.filter(matching_algorithm=value)

    def case_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter storage paths by case sensitivity setting.

        Args:
            insensitive: If True, get storage paths with case insensitive matching

        Returns:
            Filtered StoragePathQuerySet

        """
        return self.filter(is_insensitive=insensitive)

    def user_can_change(self, can_change: bool = True) -> Self:
        """
        Filter storage paths by user change permission.

        Args:
            can_change: If True, get storage paths that can be changed by user

        Returns:
            Filtered StoragePathQuerySet

        """
        return self.filter(user_can_change=can_change)
