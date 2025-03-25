"""
Define models for interacting with Paperless-NgX users and groups.

Provides the User and Group models that represent users and groups
in a Paperless-NgX instance. These models allow for querying, creating, and
managing users and their permissions within the system.

The models in this module follow the same pattern as other Paperless-NgX
resources, with standard CRUD operations and relationship management.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from paperap.models.abstract.model import StandardModel
from paperap.models.user.queryset import GroupQuerySet, UserQuerySet


class Group(StandardModel):
    """
    Represent a user group in Paperless-NgX.

    A group is a collection of users that share the same permissions. Groups are used
    to simplify permission management by assigning permissions to groups rather than
    individual users.

    Attributes:
        name (str, optional): The name of the group.
        permissions (list[str]): A list of permission strings assigned to this group.

    Examples:
        Get all admin groups::

            admin_groups = client.groups().filter(name__icontains="admin")

        Create a new group::

            new_group = client.groups().create(
                name="Finance",
                permissions=["view_document"]
            )

    """

    name: str | None = None
    permissions: list[str] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        queryset = GroupQuerySet

    @property
    def users(self) -> "UserQuerySet":
        """
        Get all users that are members of this group.

        Returns a queryset of all users that belong to this group,
        allowing for further filtering and operations on those users.

        Returns:
            UserQuerySet: A queryset containing all users that are members of this group.

        Examples:
            Get active users in a group::

                group = client.groups().get(1)  # Get group with ID 1
                active_users = group.users.filter(is_active=True)
                print(f"Group {group.name} has {active_users.count()} active users")

        """
        return self._client.users().all().in_group(self.id)


class User(StandardModel):
    """
    Represent a user in Paperless-NgX.

    Models a user account in the Paperless-NgX system, including
    authentication details, personal information, and permission settings.
    Users can belong to groups and have both direct and inherited permissions.

    Attributes:
        username (str, optional): The user's login username.
        email (str, optional): The user's email address.
        password (str, optional): The user's password (only used when creating new users).
        first_name (str, optional): The user's first name.
        last_name (str, optional): The user's last name.
        date_joined (str, optional): ISO 8601 formatted date when the user joined.
        is_staff (bool, optional): Whether the user has staff privileges.
        is_active (bool, optional): Whether the user account is active.
        is_superuser (bool, optional): Whether the user has superuser privileges.
        groups (list[int]): List of group IDs the user belongs to.
        user_permissions (list[str]): List of permission strings directly assigned to the user.
        inherited_permissions (list[str]): List of permission strings inherited from groups.

    Examples:
        Get all active users::

            active_users = client.users().filter(is_active=True)

        Create a new user::

            new_user = client.users().create(
                username="jsmith",
                email="jsmith@example.com",
                password="secure_password",
                first_name="John",
                last_name="Smith",
                is_active=True
            )

    """

    username: str | None = None
    email: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_joined: str | None = None
    is_staff: bool | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    groups: list[int] = Field(default_factory=list)
    user_permissions: list[str] = Field(default_factory=list)
    inherited_permissions: list[str] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        queryset = UserQuerySet

    def get_groups(self) -> "GroupQuerySet":
        """
        Get all groups this user is a member of.

        Returns a queryset containing all the groups that this user belongs to,
        allowing for further filtering and operations on those groups.

        Returns:
            GroupQuerySet: A queryset containing all groups this user is a member of.

        Examples:
            Find admin groups a user belongs to::

                user = client.users().get(1)  # Get user with ID 1
                admin_groups = user.get_groups().filter(name__icontains="admin")
                print(f"User {user.username} belongs to {user.get_groups().count()} groups")

        """
        return self._client.groups().all().id(self.groups)
