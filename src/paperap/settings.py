"""
Manage configuration settings for the Paperap library.

This module provides classes for configuring the Paperap client's connection
to a Paperless-NgX server, including authentication, timeouts, and behavior
settings. Settings can be loaded from environment variables or provided directly.
"""

from __future__ import annotations

from typing import Annotated, Any, Self, TypedDict, override

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from paperap.exceptions import ConfigurationError


class SettingsArgs(TypedDict, total=False):
    """
    Define expected arguments for the Settings class constructor.

    All fields are optional in this TypedDict to allow for flexible initialization
    of Settings objects with any combination of configuration parameters.

    Args:
        base_url: Base URL of the Paperless-NgX server.
        token: API token for authentication.
        username: Username for authentication (alternative to token).
        password: Password for authentication (used with username).
        timeout: Request timeout in seconds.
        require_ssl: Whether to require HTTPS connections.
        save_on_write: Whether to automatically save models when attributes are changed.

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
    Configure connection and behavior settings for the Paperap library.

    Manages configuration for connecting to and interacting with a Paperless-NgX server.
    Settings can be loaded from environment variables with the prefix PAPERLESS_
    or provided directly through constructor arguments.

    Authentication requires either a token or a username/password pair.

    Args:
        token: API token for authentication.
        username: Username for authentication (alternative to token).
        password: Password for authentication (used with username).
        base_url: Base URL of the Paperless-NgX server.
        timeout: Request timeout in seconds. Defaults to 60.
        require_ssl: Whether to require HTTPS connections. Defaults to False.
        save_on_write: Whether to automatically save models when attributes are changed.
            Defaults to True.
        openai_key: OpenAI API key for AI-powered features.
        openai_model: OpenAI model name to use.
        openai_url: Custom OpenAI API endpoint URL.

    Raises:
        ConfigurationError: If required settings are missing or invalid.

    Examples:
        Load settings from environment variables:

        ```python
        # With PAPERLESS_BASE_URL and PAPERLESS_TOKEN set in environment
        settings = Settings()
        ```

        Initialize with explicit values:

        ```python
        settings = Settings(
            base_url="https://paperless.example.com",
            token="your_api_token",
            timeout=30,
            require_ssl=True
        )
        ```

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
    template_dir: str | None = Field(default=None, alias="template_directory")

    # Default settings for document enrichment services
    enrichment_batch_size: int = Field(default=10, alias="enrichment_batch_size")
    enrichment_max_images: int = Field(default=2, alias="enrichment_max_images")

    model_config = SettingsConfigDict(env_prefix="PAPERLESS_", extra="ignore")

    @field_validator("base_url", mode="after")
    @classmethod
    def validate_url(cls, value: HttpUrl) -> HttpUrl:
        """
        Validate that the URL has both a scheme and host.

        Args:
            value: URL to validate.

        Returns:
            The validated URL.

        Raises:
            ConfigurationError: If the URL is missing a scheme or host.

        """
        # Make sure the URL has a scheme
        if not all([value.scheme, value.host]):
            raise ConfigurationError("Base URL must have a scheme and host")

        return value

    @field_validator("timeout", mode="before")
    @classmethod
    def validate_timeout(cls, value: Any) -> int:
        """
        Convert and validate the timeout value as a positive integer.

        Handles string values by converting them to integers and ensures
        the final value is a positive number.

        Args:
            value: Timeout value to validate (string or integer).

        Returns:
            Validated timeout as an integer.

        Raises:
            TypeError: If the value cannot be converted to an integer.
            ConfigurationError: If the timeout is negative.

        """
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
        Perform final validation of settings after initialization.

        Executes additional validation checks after individual field validations:
        1. Verifies authentication credentials are provided
        2. Confirms base_url is set
        3. Ensures HTTPS is used when require_ssl is True

        Args:
            __context: Context information from Pydantic initialization.

        Raises:
            ConfigurationError: If any validation checks fail.

        """
        if self.token is None and (self.username is None or self.password is None):
            raise ConfigurationError("Provide a token, or a username and password")

        if not self.base_url:
            raise ConfigurationError("Base URL is required")

        if self.require_ssl and self.base_url.scheme != "https":
            raise ConfigurationError(f"URL must use HTTPS. Url: {self.base_url}. Scheme: {self.base_url.scheme}")

        return super().model_post_init(__context)
