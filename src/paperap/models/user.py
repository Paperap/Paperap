"""




----------------------------------------------------------------------------

   METADATA:

       File:    user.py
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

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class Group(PaperlessModel):
    """
    Represents a user group in Paperless-NgX.
    """
    name: str
    permissions: list[str] = Field(default_factory=list)


class User(PaperlessModel):
    """
    Represents a user in Paperless-NgX.
    """

    username: str
    email: str
    password : str
    first_name: str
    last_name: str
    date_joined : str
    is_staff: bool = False
    is_active: bool = True
    is_superuser: bool = False
    groups: list[int] = Field(default_factory=list)
    user_permissions: list[int] = Field(default_factory=list)
    inherited_permissions : list[str] = Field(default_factory=list)
