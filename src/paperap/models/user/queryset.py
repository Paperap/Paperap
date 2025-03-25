"""
Provide query interfaces for Paperless-NGX user and group resources.

This module contains specialized querysets for interacting with users and groups
in a Paperless-NGX instance. It extends the base queryset functionality with
user and group-specific filtering methods to enable efficient and expressive
queries against the Paperless-NGX API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.user.model import Group, User

logger = logging.getLogger(__name__)


class UserQuerySet(StandardQuerySet["User"]):
    """
    Provide a lazy-loaded, chainable query interface for Paperless-NGX users.

    Extends StandardQuerySet to provide user-specific filtering methods,
    allowing for efficient querying of user resources from the Paperless-NGX API.
    Supports filtering by username, email, name, permissions, and various
    user status flags.

    All query methods return a new queryset instance, allowing for method chaining
    to build complex queries that are only executed when the results are accessed.

    Examples:
        Find active staff users:
            >>> staff_users = client.users.filter().staff().active()

        Find users with a specific permission:
            >>> admin_users = client.users.filter().has_permission("admin")

        Find users by email domain:
            >>> company_users = client.users.filter().email("@company.com", exact=False)

    """

    def username(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by username.

        Args:
            value: The username to filter by.
            exact: If True, match the exact username; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered UserQuerySet containing only users matching the username criteria.

        Examples:
            Find user with exact username:
                >>> user = client.users.filter().username("admin")

            Find users with 'admin' in their username:
                >>> admin_users = client.users.filter().username("admin", exact=False)

        """
        return self.filter_field_by_str("username", value, exact=exact, case_insensitive=case_insensitive)

    def email(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by email address.

        Args:
            value: The email address to filter by.
            exact: If True, match the exact email; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered UserQuerySet containing only users matching the email criteria.

        Examples:
            Find users with a specific domain:
                >>> gmail_users = client.users.filter().email("@gmail.com", exact=False)

        """
        return self.filter_field_by_str("email", value, exact=exact, case_insensitive=case_insensitive)

    def first_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by first name.

        Args:
            value: The first name to filter by.
            exact: If True, match the exact first name; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered UserQuerySet containing only users matching the first name criteria.

        """
        return self.filter_field_by_str("first_name", value, exact=exact, case_insensitive=case_insensitive)

    def last_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter users by last name.

        Args:
            value: The last name to filter by.
            exact: If True, match the exact last name; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered UserQuerySet containing only users matching the last name criteria.

        """
        return self.filter_field_by_str("last_name", value, exact=exact, case_insensitive=case_insensitive)

    def staff(self, value: bool = True) -> Self:
        """
        Filter users by staff status.

        Staff users typically have additional permissions in Paperless-NGX.

        Args:
            value: If True, return users that are staff members; if False, return non-staff users.

        Returns:
            A filtered UserQuerySet containing only users matching the staff status.

        Examples:
            Get all staff users:
                >>> staff = client.users.filter().staff()

            Get all non-staff users:
                >>> regular_users = client.users.filter().staff(False)

        """
        return self.filter(is_staff=value)

    def active(self, value: bool = True) -> Self:
        """
        Filter users by active status.

        Inactive users cannot log in to Paperless-NGX.

        Args:
            value: If True, return active users; if False, return inactive users.

        Returns:
            A filtered UserQuerySet containing only users matching the active status.

        Examples:
            Get only active users:
                >>> active_users = client.users.filter().active()

            Get inactive users:
                >>> inactive_users = client.users.filter().active(False)

        """
        return self.filter(is_active=value)

    def superuser(self, value: bool = True) -> Self:
        """
        Filter users by superuser status.

        Superusers have all permissions in Paperless-NGX regardless of their
        assigned permissions or groups.

        Args:
            value: If True, return superusers; if False, return non-superusers.

        Returns:
            A filtered UserQuerySet containing only users matching the superuser status.

        Examples:
            Get only superusers:
                >>> admins = client.users.filter().superuser()

            Get non-superusers:
                >>> regular_users = client.users.filter().superuser(False)

        """
        return self.filter(is_superuser=value)

    def in_group(self, value: int) -> Self:
        """
        Filter users by group membership.

        Args:
            value: The group ID to filter by.

        Returns:
            A filtered UserQuerySet containing only users who are members of the specified group.

        Examples:
            Find all users in the 'Accounting' group (ID: 5):
                >>> accounting_users = client.users.filter().in_group(5)

        """
        return self.filter(groups_contains=value)

    def has_permission(self, value: str) -> Self:
        """
        Filter users by direct permission assignment.

        Filter users who have been directly assigned the specified permission
        through their groups. Does not include permissions inherited from other sources.

        Args:
            value: The permission string to filter by (e.g., "documents.view_document").

        Returns:
            A filtered UserQuerySet containing only users with the specified permission.

        Examples:
            Find users who can view documents:
                >>> viewers = client.users.filter().has_permission("documents.view_document")

        """
        return self.filter(groups_permissions_contains=value)

    def has_inherited_permission(self, value: str) -> Self:
        """
        Filter users by inherited permission.

        Filter users who have the specified permission through any means,
        including direct assignment, group membership, or superuser status.

        Args:
            value: The permission string to filter by (e.g., "documents.view_document").

        Returns:
            A filtered UserQuerySet containing only users with the specified inherited permission.

        Examples:
            Find users who can add documents:
                >>> can_add = client.users.filter().has_inherited_permission("documents.add_document")

        """
        return self.filter(inherited_permissions_contains=value)


class GroupQuerySet(StandardQuerySet["Group"]):
    """
    Provide a lazy-loaded, chainable query interface for Paperless-NGX user groups.

    Extends StandardQuerySet to provide group-specific filtering methods,
    allowing for efficient querying of group resources from the Paperless-NGX API.
    Supports filtering by name and permissions.

    All query methods return a new queryset instance, allowing for method chaining
    to build complex queries that are only executed when the results are accessed.

    Examples:
        Find groups with a specific permission:
            >>> admin_groups = client.groups.filter().has_permission("admin.add_user")

        Find groups by name:
            >>> finance_groups = client.groups.filter().name("finance", exact=False)

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter groups by name.

        Args:
            value: The name to filter by.
            exact: If True, match the exact name; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered GroupQuerySet containing only groups matching the name criteria.

        Examples:
            Find the 'Administrators' group:
                >>> admin_group = client.groups.filter().name("Administrators")

            Find all groups with 'admin' in their name:
                >>> admin_groups = client.groups.filter().name("admin", exact=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def has_permission(self, value: str) -> Self:
        """
        Filter groups by assigned permission.

        Args:
            value: The permission string to filter by (e.g., "documents.view_document").

        Returns:
            A filtered GroupQuerySet containing only groups with the specified permission.

        Examples:
            Find groups that can delete documents:
                >>> delete_groups = client.groups.filter().has_permission("documents.delete_document")

        """
        return self.filter(permissions__contains=value)
