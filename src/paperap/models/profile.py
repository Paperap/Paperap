"""




----------------------------------------------------------------------------

   METADATA:

       File:    profile.py
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
from typing import Any

from pydantic import Field
from paperap.models.base import PaperlessModel


class Profile(PaperlessModel):
    email : str
    password : str
    first_name : str
    last_name : str
    auth_token : str
    social_accounts : list[Any] = Field(default_factory=list) # TODO unknown subtype
    has_usable_password : bool = True