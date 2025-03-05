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
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.user.model import User, Group

logger = logging.getLogger(__name__)


class UserQuerySet(StandardQuerySet["User"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def username(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by username.

        Args:
            value (str): The username to filter by
            exact (bool): If True, match the exact username, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            Filtered UserQuerySet
        """
        return self.filter_field_by_str("username", value, exact=exact, case_insensitive=case_insensitive)

    def email(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by email.

        Args:
            value (str): The email to filter by
            exact (bool): If True, match the exact email, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            Filtered UserQuerySet
        """
        return self.filter_field_by_str("email", value, exact=exact, case_insensitive=case_insensitive)

    def first_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by first name.

        Args:
            value (str): The first name to filter by
            exact (bool): If True, match the exact first name, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            Filtered UserQuerySet
        """
        return self.filter_field_by_str("first_name", value, exact=exact, case_insensitive=case_insensitive)

    def last_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by last name.

        Args:
            value (str): The last name to filter by
            exact (bool): If True, match the exact last name, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            Filtered UserQuerySet
        """
        return self.filter_field_by_str("last_name", value, exact=exact, case_insensitive=case_insensitive)

    def staff(self, value: bool = True) -> Self:
        """
        Filter users by staff status.

        Args:
            value: If True, filter users that are staff

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(is_staff=value)

    def active(self, value: bool = True) -> Self:
        """
        Filter users by active status.

        Args:
            value: If True, filter users that are active

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(is_active=value)

    def superuser(self, value: bool = True) -> Self:
        """
        Filter users by superuser status.

        Args:
            value: If True, filter users that are superusers

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(is_superuser=value)

    def in_group(self, value: int) -> Self:
        """
        Filter users by group.

        Args:
            value: The group to filter by

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(groups_contains=value)

    def has_permission(self, value: str) -> Self:
        """
        Filter users by permission.

        Args:
            value: The permission to filter by

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(groups_permissions_contains=value)

    def has_inherited_permission(self, value: str) -> Self:
        """
        Filter users by inherited permission.

        Args:
            value: The inherited permission to filter by

        Returns:
            Filtered UserQuerySet
        """
        return self.filter(inherited_permissions_contains=value)


class GroupQuerySet(StandardQuerySet["Group"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter groups by name.

        Args:
            value (str): The name to filter by
            exact (bool): If True, match the exact name, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            Filtered GroupQuerySet
        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def has_permission(self, value: str) -> Self:
        """
        Filter groups by permission.

        Args:
            value: The permission to filter by

        Returns:
            Filtered GroupQuerySet
        """
        return self.filter(permissions__contains=value)
