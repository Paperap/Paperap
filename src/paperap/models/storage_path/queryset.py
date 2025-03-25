"""
Provide query functionality for storage paths in Paperless-ngx.

This module contains the StoragePathQuerySet class, which enables filtering and
querying storage path objects from the Paperless-ngx API. It extends the standard
queryset functionality with storage path-specific filtering methods.
"""

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

    Extends StandardQuerySet to provide storage path-specific filtering
    capabilities, including filtering by path value, match criteria, matching algorithm,
    and permission settings. This queryset enables efficient querying and filtering
    of storage path objects from the Paperless-ngx API.

    Examples:
        Get all storage paths:
            >>> all_paths = client.storage_paths.all()

        Filter by path:
            >>> tax_paths = client.storage_paths.path("/documents/taxes/")

        Filter by matching algorithm:
            >>> auto_paths = client.storage_paths.matching_algorithm(1)  # 1 = Auto

    """

    def path(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter storage paths by their actual path value.

        Args:
            value: The path string to filter by.
            exact: If True, match the exact path string. If False, match paths
                containing the value string. Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered StoragePathQuerySet containing only matching storage paths.

        Examples:
            Find exact path match:
                >>> tax_paths = client.storage_paths.path("/documents/taxes/")

            Find paths containing "invoice" (case insensitive):
                >>> invoice_paths = client.storage_paths.path("invoice", exact=False)

        """
        return self.filter_field_by_str("path", value, exact=exact, case_insensitive=case_insensitive)

    def match(self, value: str, *, exact: bool = True) -> Self:
        """
        Filter storage paths by their match pattern value.

        Filter storage paths based on the match pattern used for automatic
        document routing in Paperless-ngx.

        Args:
            value: The match pattern string to filter by.
            exact: If True, match the exact pattern string. If False, match
                patterns containing the value string. Defaults to True.

        Returns:
            A filtered StoragePathQuerySet containing only matching storage paths.

        Examples:
            Find paths with exact match pattern:
                >>> invoice_paths = client.storage_paths.match("invoice")

            Find paths with match patterns containing "tax":
                >>> tax_paths = client.storage_paths.match("tax", exact=False)

        """
        return self.filter_field_by_str("match", value, exact=exact)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter storage paths by their matching algorithm.

        Filter storage paths based on the algorithm used for matching
        documents to storage paths in Paperless-ngx.

        Args:
            value: The matching algorithm ID to filter by. Common values are:
                1: Auto (let Paperless decide)
                2: Exact (exact string matching)
                3: Regular expression
                4: Fuzzy match

        Returns:
            A filtered StoragePathQuerySet containing only storage paths
            using the specified matching algorithm.

        Examples:
            Find paths using regular expressions:
                >>> regex_paths = client.storage_paths.matching_algorithm(3)

        """
        return self.filter(matching_algorithm=value)

    def case_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter storage paths by their case sensitivity setting.

        Filter storage paths based on whether they use case-insensitive
        matching for document routing.

        Args:
            insensitive: If True, return storage paths configured for
                case-insensitive matching. If False, return paths with
                case-sensitive matching. Defaults to True.

        Returns:
            A filtered StoragePathQuerySet containing only storage paths
            with the specified case sensitivity setting.

        Examples:
            Find case-insensitive paths:
                >>> insensitive_paths = client.storage_paths.case_insensitive()

            Find case-sensitive paths:
                >>> sensitive_paths = client.storage_paths.case_insensitive(False)

        """
        return self.filter(is_insensitive=insensitive)

    def user_can_change(self, can_change: bool = True) -> Self:
        """
        Filter storage paths by user modification permissions.

        Filter storage paths based on whether the current user has
        permission to modify them in the Paperless-ngx system.

        Args:
            can_change: If True, return storage paths that the current user
                can modify. If False, return paths that the user cannot modify.
                Defaults to True.

        Returns:
            A filtered StoragePathQuerySet containing only storage paths
            with the specified permission setting.

        Examples:
            Find paths the current user can modify:
                >>> editable_paths = client.storage_paths.user_can_change()

            Find paths the current user cannot modify:
                >>> readonly_paths = client.storage_paths.user_can_change(False)

        """
        return self.filter(user_can_change=can_change)
