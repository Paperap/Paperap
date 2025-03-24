

from __future__ import annotations

from typing import Annotated, Any, Self, TypedDict, override

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from paperap.exceptions import ConfigurationError


class SettingsArgs(TypedDict, total=False):
    """
    Arguments for the Settings class.

    This TypedDict defines the expected arguments that can be passed to the
    Settings class constructor. All fields are optional.

    Attributes:
        base_url: The base URL of the Paperless-NgX server.
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
    Settings for the Paperap library.

    This class manages configuration for connecting to and interacting with
    a Paperless-NgX server. Settings can be provided via environment variables
    with the prefix PAPERLESS_ or directly through constructor arguments.

    Authentication requires either a token or a username/password pair.

    Attributes:
        token: API token for authentication.
        username: Username for authentication (alternative to token).
        password: Password for authentication (used with username).
        base_url: The base URL of the Paperless-NgX server.
        timeout: Request timeout in seconds.
        require_ssl: Whether to require HTTPS connections.
        save_on_write: Whether to automatically save models when attributes are changed.
        openai_key: OpenAI API key for AI-powered features.
        openai_model: OpenAI model name to use.
        openai_url: Custom OpenAI API endpoint URL.

    Examples:
        From environment variables:
        ```python
        # With PAPERLESS_BASE_URL and PAPERLESS_TOKEN set in environment
        settings = Settings()
        ```

        Direct initialization:
        ```python
        settings = Settings(
            base_url="https://paperless.example.com",
            token="your_api_token",
            timeout=30,
            require_ssl=True
        )
        ```

    Raises:
        ConfigurationError: If required settings are missing or invalid.

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
        """
        Ensure the URL is properly formatted.

        Validates that the provided URL has both a scheme (http/https) and a host.

        Args:
            value: The URL to validate.

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
        Ensure the timeout is a positive integer.

        Converts string values to integers and validates that the timeout
        is a positive number.

        Args:
            value: The timeout value to validate, can be a string or integer.

        Returns:
            The validated timeout as an integer.

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
        Validate the settings after they have been initialized.

        Performs final validation checks after all individual field validations:
        1. Ensures authentication credentials are provided
        2. Confirms base_url is set
        3. Verifies HTTPS is used when require_ssl is True

        Args:
            __context: Context information from Pydantic initialization.

        Returns:
            None

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
