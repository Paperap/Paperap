"""




----------------------------------------------------------------------------

   METADATA:

       File:    profile.py
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

from __future__ import annotations
from typing import Any

from pydantic import Field
from paperap.models.abstract.model import StandardModel
from paperap.models.profile.queryset import ProfileQuerySet


class Profile(StandardModel):
    """
    Represents a user profile in the Paperless NGX system.

    Attributes:
        email: The email address of the user.
        password: The password for the user.
        first_name: The first name of the user.
        last_name: The last name of the user.
        auth_token: The authentication token for the user.
        social_accounts: A list of social accounts associated with the user.
        has_usable_password: Indicates if the user has a usable password.

    Examples:
        >>> profile = Profile(email="example@example.com", password="securepassword", first_name="John", last_name="Doe")
        >>> print(profile.email)
    """

    email: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    auth_token: str | None = None
    social_accounts: list[Any] = Field(default_factory=list)  # TODO unknown subtype
    has_usable_password: bool

    class Meta(StandardModel.Meta):
        queryset = ProfileQuerySet
