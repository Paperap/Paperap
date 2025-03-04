"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    auth.py                                                                                              *
*        Project: paperwrap                                                                                            *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class AuthBase(BaseModel):
    """Base authentication class."""
    
    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        pass
    
    @abstractmethod
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        pass


class TokenAuth(AuthBase):
    """Authentication using a token."""
    token: str
    
    def get_auth_headers(self) -> dict[str, str]:
        """Get the authorization headers."""
        return {"Authorization": f"Token {self.token}"}
    
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        return {}


class BasicAuth(AuthBase):
    """Authentication using username and password."""
    username: str
    password: str
    
    def get_auth_headers(self) -> dict[str, str]:
        """
        Basic auth is handled by the requests library,
        so no headers are needed here.
        """
        return {}
    
    def get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        return {"auth": (self.username, self.password)}