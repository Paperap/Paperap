"""




----------------------------------------------------------------------------

   METADATA:

       File:    settings.py
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

from abc import ABC, abstractmethod
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Any, Optional, Self, TypedDict
from yarl import URL

from paperap.exceptions import ConfigurationError


class SettingsArgs(TypedDict, total=False):
    base_url: str | URL
    token: str | None
    username: str | None
    password: str | None
    timeout: int
    require_ssl: bool
    save_on_write: bool


class Settings(BaseSettings):
    """
    Settings for the paperap library
    """

    token: str | None = None
    username: str | None = None
    password: str | None = None
    base_url: URL
    timeout: int = 60
    require_ssl: bool = False
    save_on_write: bool = True

    model_config = SettingsConfigDict(env_prefix="PAPERLESS_")

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_url(cls, value: Any) -> URL:
        """Ensure the URL is properly formatted."""
        if not value:
            raise ConfigurationError("Base URL is required")

        if isinstance(value, str):
            try:
                value = URL(value)
            except ValueError as e:
                raise ConfigurationError(f"Invalid URL format: {value}") from e

        # Validate
        if not isinstance(value, URL):
            raise ConfigurationError("Base URL must be a string or a yarl.URL object")

        # Make sure the URL has a scheme
        if not all([value.scheme, value.host]):
            raise ConfigurationError("Base URL must have a scheme and host")

        # Remove trailing slash
        if value.path.endswith("/"):
            value = value.with_path(value.path[:-1])

        return value

    @field_validator("timeout", mode="before")
    @classmethod
    def validate_timeout(cls, value: Any) -> int:
        """Ensure the timeout is a positive integer."""
        try:
            if isinstance(value, str):
                # May raise ValueError
                value = int(value)

            if not isinstance(value, int):
                raise TypeError("Unknown type for timeout")
        except ValueError as ve:
            raise TypeError(f"Timeout must be an integer. Provided {value=} of type {type(value)}") from ve

        if value < 0:
            raise ConfigurationError("Timeout must be a positive integer")
        return value

    def model_post_init(self, __context):
        if self.token is None and (self.username is None or self.password is None):
            raise ConfigurationError("Provide a token, or a username and password")

        if not self.base_url:
            raise ConfigurationError("Base URL is required")

        if self.require_ssl and self.base_url.scheme != "https":
            raise ConfigurationError(f"URL must use HTTPS. Url: {self.base_url}. Scheme: {self.base_url.scheme}")

        return super().model_post_init(__context)
