"""
----------------------------------------------------------------------------

   METADATA:

       File:    users.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from typing import Any, Optional

from paperap.exceptions import ObjectNotFoundError
from paperap.models.user import Group, GroupQuerySet, User, UserQuerySet
from paperap.resources.base import BaseResource, StandardResource


class UserResource(StandardResource[User, UserQuerySet]):
    """Resource for managing users."""

    model_class = User

    def get_current(self) -> User:
        """
        Get the current authenticated user.

        Returns:
            The current user.

        """
        if not (response := self.client.request("GET", "users/me/")):
            raise ObjectNotFoundError("Failed to get current user")
        return User.from_dict(response)


class GroupResource(StandardResource[Group, GroupQuerySet]):
    """Resource for managing groups."""

    model_class = Group
