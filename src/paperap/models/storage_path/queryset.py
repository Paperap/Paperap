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

from typing import Any, Self, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.storage_path.model import StoragePath

logger = logging.getLogger(__name__)


class StoragePathQuerySet(QuerySet["StoragePath"]):
    """
    QuerySet for Paperless-ngx storage paths with specialized filtering methods.
    """

    def with_name(self, name: str, *, exact: bool = True) -> Self:
        """
        Filter storage paths by name.

        Args:
            name: The storage path name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered StoragePathQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def with_path(self, path: str, *, exact: bool = True) -> Self:
        """
        Filter storage paths by their actual path value.

        Args:
            path: The path to filter by
            exact: If True, match the exact path, otherwise use contains

        Returns:
            Filtered StoragePathQuerySet
        """
        if exact:
            return self.filter(path=path)
        return self.filter(path__contains=path)

    def with_slug(self, slug: str, *, exact: bool = True) -> Self:
        """
        Filter storage paths by their slug.

        Args:
            slug: The slug to filter by
            exact: If True, match the exact slug, otherwise use contains

        Returns:
            Filtered StoragePathQuery
        """
        if exact:
            return self.filter(slug=slug)
        return self.filter(slug__contains=slug)

    def with_matching_rule(self, rule_pattern: str) -> Self:
        """
        Filter storage paths by their matching rule pattern.

        Args:
            rule_pattern: The pattern to search for in matching rules

        Returns:
            Filtered StoragePathQuerySet
        """
        return self.filter(matching_algorithm__contains=rule_pattern)

    def is_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter storage paths by case sensitivity setting.

        Args:
            insensitive: If True, get storage paths with case insensitive matching

        Returns:
            Filtered StoragePathQuerySet
        """
        return self.filter(is_insensitive=insensitive)
