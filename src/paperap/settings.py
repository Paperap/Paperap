

from __future__ import annotations

from typing import Annotated, Any, Self, TypedDict, override

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from paperap.exceptions import ConfigurationError


class SettingsArgs(TypedDict, total=False):
    """
    Arguments for the settings class
    """

    base_url: HttpUrl
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
    base_url: HttpUrl
    timeout: int = 60
    require_ssl: bool = False
    save_on_write: bool = True
    openai_key: str | None = Field(default=None, alias="openai_api_key")
    openai_model: str | None = Field(default=None, alias="openai_model_name")
    openai_url: str | None = Field(default=None, alias="openai_base_url")

    model_config = SettingsConfigDict(env_prefix="PAPERLESS_", extra="ignore")

    @field_validator("base_url", mode="after")
    @classmethod
    def validate_url(cls, value: HttpUrl) -> HttpUrl:
        """Ensure the URL is properly formatted."""
        # Make sure the URL has a scheme
        if not all([value.scheme, value.host]):
            raise ConfigurationError("Base URL must have a scheme and host")

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

    @override
    def model_post_init(self, __context: Any) -> None:
        """
        Validate the settings after they have been initialized.
        """
        if self.token is None and (self.username is None or self.password is None):
            raise ConfigurationError("Provide a token, or a username and password")

        if not self.base_url:
            raise ConfigurationError("Base URL is required")

        if self.require_ssl and self.base_url.scheme != "https":
            raise ConfigurationError(f"URL must use HTTPS. Url: {self.base_url}. Scheme: {self.base_url.scheme}")

        return super().model_post_init(__context)
