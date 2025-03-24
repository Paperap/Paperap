"""
User profile module for Paperless-NGX.

This module defines the Profile model which represents user profiles in the
Paperless-NGX system, including personal information and authentication details.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from paperap.models.abstract.model import StandardModel
from paperap.models.profile.queryset import ProfileQuerySet


class Profile(StandardModel):
    """
    Represents a user profile in the Paperless-NGX system.

    This model corresponds to the user profile endpoint in the Paperless-NGX API
    and contains information about users, including their personal details and
    authentication information.

    Attributes:
        email (str, optional): The email address of the user.
        password (str, optional): The password for the user. This is write-only
            and will not be returned in API responses.
        first_name (str, optional): The first name of the user.
        last_name (str, optional): The last name of the user.
        auth_token (str, optional): The authentication token for the user.
            This can be used for API authentication.
        social_accounts (list): A list of social accounts associated with the user
            for third-party authentication.
        has_usable_password (bool): Indicates if the user has a usable password.
            False if the user can only log in via social authentication or tokens.

    Examples:
        >>> # Create a new profile
        >>> profile = Profile(
        ...     email="user@example.com",
        ...     first_name="John",
        ...     last_name="Doe",
        ...     has_usable_password=True
        ... )
        >>>
        >>> # Access profile information
        >>> print(f"{profile.first_name} {profile.last_name} <{profile.email}>")
        John Doe <user@example.com>

    """

    email: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    auth_token: str | None = None
    social_accounts: list[Any] = Field(default_factory=list)  # TODO unknown subtype
    has_usable_password: bool

    class Meta(StandardModel.Meta):
        """
        Metadata for the Profile model.

        This class defines metadata for the Profile model, including the
        associated queryset class for performing queries on profiles.

        Attributes:
            queryset (type[ProfileQuerySet]): The queryset class to use for
                profile queries.

        """

        queryset = ProfileQuerySet
