
from __future__ import annotations

from typing import Any, Optional

from paperap.exceptions import ObjectNotFoundError
from paperap.models.user import Group, User
from paperap.resources.base import PaperlessResource


class UserResource(PaperlessResource[User]):
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
        return User.from_dict(response, self)


class GroupResource(PaperlessResource[Group]):
    """Resource for managing groups."""

    model_class = Group
