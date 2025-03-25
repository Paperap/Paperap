"""
Resources for managing users and groups in Paperless-NgX.

This module provides resource classes for interacting with the users and groups
endpoints of the Paperless-NgX API. It enables operations such as retrieving user
information, managing user accounts, and working with permission groups.

Classes:
    UserResource: Resource for managing user accounts.
    GroupResource: Resource for managing permission groups.
"""

from __future__ import annotations

from typing import Any

from paperap.exceptions import ObjectNotFoundError
from paperap.models.user import Group, GroupQuerySet, User, UserQuerySet
from paperap.resources.base import BaseResource, StandardResource


class UserResource(StandardResource[User, UserQuerySet]):
    """
    Resource for managing user accounts in Paperless-NgX.

    This class provides methods to interact with the user-related endpoints of the
    Paperless-NgX API, allowing for operations such as retrieving user information,
    creating users, and managing user accounts.

    Attributes:
        model_class: The User model class associated with this resource.
        queryset_class: The UserQuerySet class used for querying users.

    Example:
        >>> client = PaperlessClient()
        >>> users = client.users.all()
        >>> for user in users:
        ...     print(f"{user.username}: {user.email}")

    """

    model_class = User
    queryset_class = UserQuerySet

    def get_current(self) -> User:
        """
        Retrieve the current authenticated user.

        Sends a request to the Paperless-NgX API to fetch the details of the currently
        authenticated user (the user associated with the API token or credentials
        used to initialize the client).

        Returns:
            User: The current authenticated user object.

        Raises:
            ObjectNotFoundError: If the current user cannot be retrieved or the
                authentication credentials are invalid.

        Example:
            >>> client = PaperlessClient()
            >>> current_user = client.users.get_current()
            >>> print(f"Logged in as: {current_user.username}")
            >>> print(f"User ID: {current_user.id}")
            >>> print(f"Is superuser: {current_user.is_superuser}")

        """
        if not (response := self.client.request("GET", "users/me/")):
            raise ObjectNotFoundError("Failed to get current user")
        return User.from_dict(response)


class GroupResource(StandardResource[Group, GroupQuerySet]):
    """
    Resource for managing permission groups in Paperless-NgX.

    This class provides methods to interact with the group-related endpoints of the
    Paperless-NgX API, allowing for operations such as retrieving group information,
    creating groups, and managing group permissions.

    Groups in Paperless-NgX are used to organize users and control their access
    permissions to various features and resources within the system.

    Attributes:
        model_class: The Group model class associated with this resource.
        queryset_class: The GroupQuerySet class used for querying groups.

    Example:
        >>> client = PaperlessClient()
        >>> # Get all groups
        >>> all_groups = client.groups.all()
        >>> for group in all_groups:
        ...     print(f"Group: {group.name}")
        ...     print(f"Permissions: {group.permissions}")
        >>>
        >>> # Create a new group
        >>> new_group = client.groups.create(
        ...     name="Document Managers",
        ...     permissions=[1, 4, 7]  # Permission IDs
        ... )

    """

    model_class = Group
    queryset_class = GroupQuerySet
