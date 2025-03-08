"""




----------------------------------------------------------------------------

   METADATA:

       File:    user.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.user.queryset import UserQuerySet, GroupQuerySet


class Group(StandardModel):
    """
    Represents a user group in Paperless-NgX.
    """

    name: str | None = None
    permissions: list[str] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        queryset = GroupQuerySet

    @property
    def users(self) -> "UserQuerySet":
        """
        Get the users in this group.

        Returns:
            UserQuerySet: The users in this group
        """
        return self._client.users().all().in_group(self.id)


class User(StandardModel):
    """
    Represents a user in Paperless-NgX.
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
        Get the groups this user is a member of.

        Returns:
            GroupQuerySet: The groups this user is a member
        """
        return self._client.groups().all().id(self.groups)
