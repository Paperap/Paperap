"""
----------------------------------------------------------------------------

   METADATA:

       File:    auth.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, override

import pydantic


class AuthBase(pydantic.BaseModel):
    """Base authentication class."""

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        raise NotImplementedError("get_auth_headers must be implemented by subclasses")

    @abstractmethod
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        raise NotImplementedError("get_auth_params must be implemented by subclasses")

class TokenAuth(AuthBase):
    """Authentication using a token."""

    token: str

    @override
    def get_auth_headers(self) -> dict[str, str]:
        """Get the authorization headers."""
        return {"Authorization": f"Token {self.token}"}

    @override
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        return {}


class BasicAuth(AuthBase):
    """Authentication using username and password."""

    username: str
    password: str

    @override
    def get_auth_headers(self) -> dict[str, str]:
        """
        Get headers for basic auth.
        
        Basic auth is handled by the requests library, so no headers are needed here.
        """
        return {}

    @override
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        return {"auth": (self.username, self.password)}
