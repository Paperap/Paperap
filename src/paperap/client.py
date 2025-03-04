"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    client.py                                                                                            *
*        Project: paperap                                                                                            *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

import logging
from pathlib import Path
from typing import Any, Iterator, Literal, Unpack, overload
import requests
from yarl import URL
from string import Template
from paperap.auth import BasicAuth, TokenAuth, AuthBase
from paperap.exceptions import APIError, AuthenticationError, PaperlessException, ResourceNotFoundError
from paperap.plugin_manager import PluginConfig
from paperap.plugins.base import Plugin
from paperap.settings import Settings, SettingsArgs
from paperap.resources import (
    CorrespondentResource,
    CustomFieldResource,
    DocumentResource,
    DocumentTypeResource,
    GroupResource,
    LogResource,
    MailAccountsResource,
    MailRulesResource,
    ProfileResource,
    SavedViewResource,
    SearchResource,
    ShareLinksResource,
    StoragePathResource,
    TagResource,
    TaskResource,
    UISettingsResource,
    UserResource,
    WorkflowActionResource,
    WorkflowResource,
    WorkflowTriggerResource,
)

logger = logging.getLogger(__name__)


class PaperlessClient:
    """
    Client for interacting with the Paperless-NgX API.

    Args:
        settings: Settings object containing client configuration.

    Examples:
        ```python
        # Using token authentication
        client = PaperlessClient(
            Settings(
                base_url="https://paperless.example.com",
                token="your-token"
            )
        )

        # Using basic authentication
        client = PaperlessClient(
            Settings(
                base_url="https://paperless.example.com",
                username="user",
                password="pass"
            )
        )

        # Loading all settings from environment variables (e.g. PAPERLESS_TOKEN)
        client = PaperlessClient()

        # With context manager
        with PaperlessClient(...) as client:
            docs = client.documents.list()
        ```
    """

    settings: Settings
    auth: AuthBase
    session: requests.Session
    plugins: dict[str, Plugin]

    # Resources
    correspondents: CorrespondentResource
    custom_fields: CustomFieldResource
    document_types: DocumentTypeResource
    documents: DocumentResource
    groups: GroupResource
    logs: LogResource
    mail_accounts: MailAccountsResource
    mail_rules: MailRulesResource
    profile: ProfileResource
    saved_views: SavedViewResource
    search: SearchResource
    share_links: ShareLinksResource
    storage_paths: StoragePathResource
    tags: TagResource
    tasks: TaskResource
    ui_settings: UISettingsResource
    users: UserResource
    workflow_actions: WorkflowActionResource
    workflow_triggers: WorkflowTriggerResource
    workflows: WorkflowResource

    def __init__(self, settings: Settings | None = None, **kwargs: Unpack[SettingsArgs]):
        if not settings:
            # Any params not provided in kwargs will be loaded from env vars
            settings = Settings(**kwargs)  # type: ignore # base_url is a URL, but accepts str | URL

        self.settings = settings
        if self.settings.token:
            self.auth = TokenAuth(token=self.settings.token)
        elif self.settings.username and self.settings.password:
            self.auth = BasicAuth(username=self.settings.username, password=self.settings.password)
        else:
            raise ValueError("Provide a token, or a username and password")

        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {
                "Accept": "application/json; version=2",
                "Content-Type": "application/json",
            }
        )

        # Initialize resources
        self._init_resources()
        self._initialize_plugins()

    @property
    def base_url(self) -> URL:
        """Get the base URL."""
        return self.settings.base_url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_resources(self) -> None:
        """Initialize all API resources."""
        # Initialize resources
        self.documents = DocumentResource(self)
        self.correspondents = CorrespondentResource(self)
        self.tags = TagResource(self)
        self.document_types = DocumentTypeResource(self)
        self.storage_paths = StoragePathResource(self)
        self.custom_fields = CustomFieldResource(self)
        self.logs = LogResource(self)
        self.users = UserResource(self)
        self.groups = GroupResource(self)
        self.tasks = TaskResource(self)
        self.saved_views = SavedViewResource(self)
        self.ui_settings = UISettingsResource(self)
        self.workflows = WorkflowResource(self)
        self.workflow_triggers = WorkflowTriggerResource(self)
        self.workflow_actions = WorkflowActionResource(self)

    def _initialize_plugins(self, plugin_config: PluginConfig | None = None) -> None:
        """
        Initialize plugins based on configuration.

        Args:
            plugin_config: Optional configuration dictionary for plugins.
        """
        from paperap.plugin_manager import PluginManager

        # Create and configure the plugin manager
        self.plugin_manager = PluginManager()

        # Discover available plugins
        self.plugin_manager.discover_plugins()

        # Configure plugins
        default_config: PluginConfig = {
            "enabled_plugins": ["TestDataCollector"],
            "settings": {
                "TestDataCollector": {
                    "test_dir": str(Path(__file__).parent.parent.parent / "tests/sample_data"),
                },
            },
        }
        config = plugin_config or default_config
        self.plugin_manager.configure(config)

        # Initialize all enabled plugins
        self.plugins = self.plugin_manager.initialize_all_plugins(self)

    def _get_auth_params(self) -> dict[str, Any]:
        """Get authentication parameters for requests."""
        return self.auth.get_auth_params() if self.auth else {}

    def _get_headers(self) -> dict[str, str]:
        """Get headers for requests."""
        headers = {}

        if self.auth:
            headers.update(self.auth.get_auth_headers())

        return headers

    def close(self) -> None:
        """Close the client and release resources."""
        if hasattr(self, "session") and self.session:
            self.session.close()

    def _request(
        self,
        method: str,
        endpoint: str | URL | Template,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> requests.Response | None:
        """
        Make a request to the Paperless-NgX API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint relative to base URL.
            params: Query parameters for the request.
            data: Request body data.
            files: Files to upload.
            json_response: Whether to parse the response as JSON.

        Returns:
            Response object or None if no content.

        Raises:
            AuthenticationError: If authentication fails.
            ResourceNotFoundError: If the requested resource doesn't exist.
            APIError: If the API returns an error.
            PaperlessException: For other errors.
        """
        endpoint = str(endpoint)

        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.critical("Requesting %s %s", method, url)

        # Add headers from authentication and session defaults
        headers = {**self.session.headers, **self._get_headers()}

        # If we're uploading files, don't set Content-Type
        if files:
            headers.pop("Content-Type", None)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data if not files and data else None,
                data=data if files else None,
                files=files,
                timeout=self.settings.timeout,
                **self._get_auth_params(),
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                error_message = self._extract_error_message(response)

                if response.status_code == 401:
                    raise AuthenticationError(f"Authentication failed: {error_message}")
                elif response.status_code == 404:
                    raise ResourceNotFoundError(f"Paperless returned 404 for {endpoint}")
                else:
                    raise APIError(error_message, response.status_code)

            # No content
            if response.status_code == 204:
                return None

            return response

        except requests.exceptions.RequestException as e:
            raise PaperlessException(f"Request failed: {str(e)}") from e

    @overload
    def _handle_response(
        self, response: requests.Response, *, json_response: Literal[True] = True
    ) -> dict[str, Any]: ...

    @overload
    def _handle_response(self, response: None, *, json_response: bool = True) -> None: ...

    @overload
    def _handle_response(
        self, response: requests.Response | None, *, json_response: Literal[False]
    ) -> bytes | None: ...

    @overload
    def _handle_response(
        self, response: requests.Response | None, *, json_response: bool = True
    ) -> dict[str, Any] | bytes | None: ...

    def _handle_response(
        self, response: requests.Response | None, *, json_response: bool = True
    ) -> dict[str, Any] | bytes | None:
        """Handle the response based on the content type."""
        if not response:
            return None

        # Try to parse as JSON if requested
        if json_response:
            try:
                return response.json()
            except ValueError as e:
                raise PaperlessException(f"Failed to parse JSON response: {str(e)} -> {response}") from e

        return response.content

    @overload
    def request(
        self,
        method: str,
        endpoint: str | URL | Template,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: Literal[True] = True,
    ) -> dict[str, Any] | None: ...

    @overload
    def request(
        self,
        method: str,
        endpoint: str | URL | Template,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: Literal[False] = False,
    ) -> bytes | None: ...

    @overload
    def request(
        self,
        method: str,
        endpoint: str | URL | Template,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: bool = True,
    ) -> dict[str, Any] | bytes | None: ...

    def request(
        self,
        method: str,
        endpoint: str | URL | Template,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: bool = True,
    ) -> dict[str, Any] | bytes | None:
        if not (response := self._request(method, endpoint, params=params, data=data, files=files)):
            return None

        return self._handle_response(response, json_response=json_response)

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response."""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                # Try different possible error formats
                if "detail" in error_data:
                    return error_data["detail"]
                elif "error" in error_data:
                    return error_data["error"]
                elif "non_field_errors" in error_data:
                    return ", ".join(error_data["non_field_errors"])
                else:
                    # Handle nested error messages
                    messages = []
                    for key, value in error_data.items():
                        if isinstance(value, list):
                            messages.append(f"{key}: {', '.join(value)}")
                        else:
                            messages.append(f"{key}: {value}")
                    return "; ".join(messages)
            return str(error_data)
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    def generate_token(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int | None = None,
    ) -> str:
        """
        Generate an API token using username and password.

        Args:
            base_url: The base URL of the Paperless-NgX instance.
            username: Username for authentication.
            password: Password for authentication.
            timeout: Request timeout in seconds.

        Returns:
            Generated API token.

        Raises:
            AuthenticationError: If authentication fails.
            PaperlessException: For other errors.
        """
        if timeout is None:
            timeout = self.settings.timeout

        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        url = f"{base_url.rstrip('/')}/api/token/"

        try:
            response = requests.post(
                url,
                json={"username": username, "password": password},
                headers={"Accept": "application/json"},
                timeout=timeout,
            )

            response.raise_for_status()
            data = response.json()

            if "token" not in data:
                raise PaperlessException("Token not found in response")

            return data["token"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid username or password") from e
            else:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("detail", str(e))
                except (ValueError, KeyError):
                    error_message = str(e)

                raise PaperlessException(f"Failed to generate token: {error_message}") from e
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            raise PaperlessException(f"Failed to generate token: {str(e)}") from e

    def get_statistics(self) -> dict[str, Any]:
        """
        Get system statistics.

        Returns:
            Dictionary containing system statistics.
        """
        if result := self.request("GET", "api/statistics/"):
            return result
        raise APIError("Failed to get statistics")

    def get_system_status(self) -> dict[str, Any]:
        """
        Get system status.

        Returns:
            Dictionary containing system status information.
        """
        if result := self.request("GET", "api/status/"):
            return result
        raise APIError("Failed to get system status")

    def get_config(self) -> dict[str, Any]:
        """
        Get system configuration.

        Returns:
            Dictionary containing system configuration.
        """
        if result := self.request("GET", "api/config/"):
            return result
        raise APIError("Failed to get system configuration")
