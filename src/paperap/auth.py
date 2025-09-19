"""
Authentication classes for Paperless-ngx API.

This module provides authentication classes for interacting with the Paperless-ngx API.
It supports token-based authentication and basic username/password authentication.

Classes:
    AuthBase: Abstract base class for authentication methods.
    TokenAuth: Authentication using a Paperless-ngx API token.
    BasicAuth: Authentication using username and password.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Annotated, Any, override
import pydantic
from pydantic import ConfigDict, Field


class AuthBase(pydantic.BaseModel, ABC):
    """
    Base authentication class for Paperless-ngx API.

    This abstract base class defines the interface for all authentication methods.
    Subclasses must implement methods to provide authentication headers and parameters.

    Attributes:
        model_config (ConfigDict): Pydantic configuration for validation behavior.

    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            dict[str, str]: A dictionary of HTTP headers needed for authentication.

        Raises:
            NotImplementedError: If not implemented by subclasses.

        """
        raise NotImplementedError("get_auth_headers must be implemented by subclasses")

    @abstractmethod
    def get_auth_params(self) -> dict[str, Any]:
        """
        Get authentication parameters for API requests.

        Returns:
            dict[str, Any]: A dictionary of parameters to include in the request.

        Raises:
            NotImplementedError: If not implemented by subclasses.

        """
        raise NotImplementedError("get_auth_params must be implemented by subclasses")


class TokenAuth(AuthBase):
    """
    Authentication using a Paperless-ngx API token.

    This class implements token-based authentication for the Paperless-ngx API.
    The token is included in the Authorization header of each request.

    Attributes:
        token (str): The API token from Paperless-ngx.

    Examples:
        >>> auth = TokenAuth(token="abcdef1234567890abcdef1234567890abcdef12")
        >>> headers = auth.get_auth_headers()
        >>> print(headers)
        {'Authorization': 'Token abcdef1234567890abcdef1234567890abcdef12'}

    """

    # token length appears to be 40. Set to 30 just in case (will still catch egregious errors)
    token: Annotated[str, Field(min_length=30, max_length=75, pattern=r"^[a-zA-Z0-9]+$")]

    @override
    def get_auth_headers(self) -> dict[str, str]:
        """
        Get the authorization headers with the token.

        Returns:
            dict[str, str]: A dictionary containing the Authorization header with the token.

        """
        return {"Authorization": f"Token {self.token}"}

    @override
    def get_auth_params(self) -> dict[str, Any]:
        """
        Get authentication parameters for requests.

        For token authentication, no additional parameters are needed.

        Returns:
            dict[str, Any]: An empty dictionary as token auth uses headers, not parameters.

        """
        return {}


class BasicAuth(AuthBase):
    """
    Authentication using username and password.

    This class implements HTTP Basic Authentication for the Paperless-ngx API.
    The username and password are passed to the requests library's auth parameter.

    Attributes:
        username (str): The Paperless-ngx username.
        password (str): The Paperless-ngx password.

    Examples:
        >>> auth = BasicAuth(username="admin", password="password123")
        >>> params = auth.get_auth_params()
        >>> print(params)
        {'auth': ('admin', 'password123')}

    """

    username: str = Field(min_length=0, max_length=255)
    password: str = Field(min_length=0, max_length=255)

    @override
    def get_auth_headers(self) -> dict[str, str]:
        """
        Get headers for basic auth.

        Basic auth is handled by the requests library's auth parameter,
        so no headers are needed here.

        Returns:
            dict[str, str]: An empty dictionary as basic auth uses parameters, not headers.

        """
        return {}

    @override
    def get_auth_params(self) -> dict[str, Any]:
        """
        Get authentication parameters for requests.

        Returns:
            dict[str, Any]: A dictionary containing the auth parameter with username and password.

        """
        return {"auth": (self.username, self.password)}
