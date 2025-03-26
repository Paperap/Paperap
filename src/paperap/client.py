"""
Client module for interacting with the Paperless-ngx API.

This module provides the main client class for connecting to and interacting with
a Paperless-ngx server. It handles authentication, request management, and provides
access to all API resources.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Unpack, overload

import requests
from pydantic import HttpUrl

from paperap.auth import AuthBase, BasicAuth, TokenAuth
from paperap.exceptions import (
    APIError,
    AuthenticationError,
    BadResponseError,
    ConfigurationError,
    InsufficientPermissionError,
    RelationshipNotFoundError,
    RequestError,
    ResourceNotFoundError,
    ResponseParsingError,
)
from paperap.resources import (
    CorrespondentResource,
    CustomFieldResource,
    DocumentMetadataResource,
    DocumentNoteResource,
    DocumentResource,
    DocumentSuggestionsResource,
    DocumentTypeResource,
    DownloadedDocumentResource,
    GroupResource,
    ProfileResource,
    SavedViewResource,
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
from paperap.settings import Settings, SettingsArgs
from paperap.signals import registry

if TYPE_CHECKING:
    from paperap.plugins.base import Plugin
    from paperap.plugins.manager import PluginConfig

logger = logging.getLogger(__name__)


class PaperlessClient:
    """
    Client for interacting with the Paperless-NgX API.

    This is the main entry point for all interactions with a Paperless-ngx server.
    It handles authentication, request management, and provides access to all API
    resources through convenient properties.

    Args:
        settings: Settings object containing client configuration. If None, settings
            will be loaded from environment variables and/or kwargs.
        **kwargs: Additional settings that will override those in the settings object
            or environment variables. See Settings class for available options.

    Attributes:
        settings: The configuration settings for this client.
        auth: The authentication handler (TokenAuth or BasicAuth).
        session: The requests Session used for HTTP communication.
        plugins: Dictionary of initialized plugins.
        correspondents: Resource for managing correspondents.
        custom_fields: Resource for managing custom fields.
        document_types: Resource for managing document types.
        documents: Resource for managing documents.
        storage_paths: Resource for managing storage paths.
        tags: Resource for managing tags.
        tasks: Resource for managing tasks.
        saved_views: Resource for managing saved views.

    Raises:
        ValueError: If neither token nor username/password authentication is provided.

    Examples:
        Using token authentication:

        >>> from paperap import PaperlessClient
        >>> from paperap.settings import Settings
        >>> client = PaperlessClient(
        ...     Settings(
        ...         base_url="https://paperless.example.com",
        ...         token="40characterslong40characterslong40charac"
        ...     )
        ... )

        Using basic authentication:

        >>> client = PaperlessClient(
        ...     base_url="https://paperless.example.com",
        ...     username="user",
        ...     password="pass"
        ... )

        Loading settings from environment variables:

        >>> # With PAPERLESS_BASE_URL and PAPERLESS_TOKEN set in environment
        >>> client = PaperlessClient()

        Using as a context manager:

        >>> with PaperlessClient(token="mytoken", base_url="https://paperless.local") as client:
        ...     docs = client.documents.all()

    """

    settings: Settings
    auth: AuthBase
    session: requests.Session
    plugins: dict[str, "Plugin"]

    # Resources
    correspondents: CorrespondentResource
    custom_fields: CustomFieldResource
    document_types: DocumentTypeResource
    document_metadata: DocumentMetadataResource
    document_suggestions: DocumentSuggestionsResource
    downloaded_documents: DownloadedDocumentResource
    documents: DocumentResource
    document_notes: DocumentNoteResource
    groups: GroupResource
    profile: ProfileResource
    saved_views: SavedViewResource
    share_links: ShareLinksResource
    storage_paths: StoragePathResource
    tags: TagResource
    tasks: TaskResource
    ui_settings: UISettingsResource
    users: UserResource
    workflow_actions: WorkflowActionResource
    workflow_triggers: WorkflowTriggerResource
    workflows: WorkflowResource

    def __init__(self, settings: Settings | None = None, **kwargs: Unpack[SettingsArgs]) -> None:
        if not settings:
            # Any params not provided in kwargs will be loaded from env vars
            settings = Settings(**kwargs)

        self.settings = settings
        # Prioritize username/password over token if both are provided
        if self.settings.username and self.settings.password:
            self.auth = BasicAuth(username=self.settings.username, password=self.settings.password)
        elif self.settings.token:
            self.auth = TokenAuth(token=self.settings.token)
        else:
            raise ValueError("Provide a token, or a username and password")

        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {
                "Accept": "application/json; version=7",
                # Don't set Content-Type here as it will be set appropriately per request
                # "Content-Type": "application/json",
            }
        )

        # Initialize resources
        self._init_resources()
        self._initialize_plugins()
        super().__init__()

    @property
    def base_url(self) -> HttpUrl:
        """
        Get the base URL of the Paperless-ngx server.

        Returns:
            The base URL as an HttpUrl object.

        """
        return self.settings.base_url

    def __enter__(self) -> PaperlessClient:
        """
        Enter context manager.

        Returns:
            Self, allowing the client to be used in a with statement.

        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager, ensuring resources are properly released.

        Args:
            exc_type: Exception type if an exception was raised in the context.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.

        """
        self.close()

    def _init_resources(self) -> None:
        """
        Initialize all API resources.

        This method creates instances of all resource classes and assigns them
        to the appropriate attributes of the client.
        """
        # Initialize resources
        self.correspondents = CorrespondentResource(self)
        self.custom_fields = CustomFieldResource(self)
        self.document_types = DocumentTypeResource(self)
        self.document_metadata = DocumentMetadataResource(self)
        self.document_suggestions = DocumentSuggestionsResource(self)
        self.downloaded_documents = DownloadedDocumentResource(self)
        self.documents = DocumentResource(self)
        self.document_notes = DocumentNoteResource(self)
        self.groups = GroupResource(self)
        self.profile = ProfileResource(self)
        self.saved_views = SavedViewResource(self)
        self.share_links = ShareLinksResource(self)
        self.storage_paths = StoragePathResource(self)
        self.tags = TagResource(self)
        self.tasks = TaskResource(self)
        self.ui_settings = UISettingsResource(self)
        self.users = UserResource(self)
        self.workflow_actions = WorkflowActionResource(self)
        self.workflow_triggers = WorkflowTriggerResource(self)
        self.workflows = WorkflowResource(self)

    def _initialize_plugins(self, plugin_config: "PluginConfig | None" = None) -> None:
        """
        Initialize plugins based on configuration.

        This method discovers available plugins, configures them according to the
        provided configuration (or default configuration if none is provided),
        and initializes all enabled plugins.

        Args:
            plugin_config: Optional configuration dictionary for plugins. If None,
                a default configuration will be used.

        """
        from paperap.plugins.manager import PluginManager  # pylint: disable=import-outside-toplevel

        PluginManager.model_rebuild()

        # Create and configure the plugin manager
        self.manager = PluginManager(client=self)

        if os.getenv("PAPERAP_TESTING", False):
            # Discover available plugins
            self.manager.discover_plugins()

            # Configure plugins
            plugin_config = plugin_config or {
                "enabled_plugins": ["SampleDataCollector"],
                "settings": {
                    "SampleDataCollector": {
                        "test_dir": str(Path(__file__).parents[3] / "tests/sample_data"),
                    },
                },
            }
        self.manager.configure(plugin_config)

        # Initialize all enabled plugins
        self.plugins = self.manager.initialize_all_plugins()

    def _get_auth_params(self) -> dict[str, Any]:
        """
        Get authentication parameters for requests.

        Returns:
            Dictionary of authentication parameters to be passed to requests.

        """
        return self.auth.get_auth_params()

    def get_headers(self) -> dict[str, str]:
        """
        Get headers for API requests.

        Returns:
            Dictionary of HTTP headers including authentication headers.

        """
        headers = {}

        headers.update(self.auth.get_auth_headers())

        return headers

    def close(self) -> None:
        """
        Close the client and release resources.

        This method ensures the HTTP session is properly closed to prevent
        resource leaks.
        """
        if hasattr(self, "session"):
            self.session.close()

    def request_raw(
        self,
        method: str,
        endpoint: str | HttpUrl,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> requests.Response | None:
        """
        Make a raw request to the Paperless-NgX API.

        This method handles the low-level HTTP communication with the Paperless-ngx
        server, including URL construction, header management, and error handling.
        It returns the raw response object without parsing the content.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint relative to base URL or absolute URL.
            params: Query parameters for the request.
            data: Request body data.
            files: Files to upload.

        Returns:
            Response object or None if the server returned a 204 No Content response.

        Raises:
            AuthenticationError: If authentication fails (401).
            ResourceNotFoundError: If the requested resource doesn't exist (404).
            InsufficientPermissionError: If the user lacks permission (403).
            RequestError: For connection or request failures.
            BadResponseError: For other HTTP error responses.

        Examples:
            >>> response = client.request_raw("GET", "api/documents/")
            >>> print(response.status_code)
            200

        """
        if isinstance(endpoint, HttpUrl):
            # Use URL object directly
            url = str(endpoint)
        elif isinstance(endpoint, str):
            if endpoint.startswith("http"):
                url = endpoint
            else:
                url = f"{self.base_url}{endpoint.lstrip('/')}"
        else:
            url = f"{self.base_url}{str(endpoint).lstrip('/')}"

        logger.debug("Requesting %s %s", method, url)

        # Add headers from authentication and session defaults
        headers = {**self.session.headers, **self.get_headers()}

        # Set the appropriate Content-Type header based on the request type
        if files:
            # For file uploads, let requests set the multipart/form-data Content-Type with boundary
            headers.pop("Content-Type", None)
        elif "Content-Type" not in headers:
            # For JSON requests, explicitly set the Content-Type
            headers["Content-Type"] = "application/json"

        try:
            # TODO: Temporary hack
            params = params.get("params", params) if params else params

            logger.debug(
                "Request (%s) url %s, params %s, data %s, files %s, headers %s",
                method,
                url,
                params,
                data,
                files,
                headers,
            )
            # When uploading files, we need to pass data as form data, not JSON
            # The key difference is that with files, we MUST use data parameter, not json
            if files:
                # For file uploads, use data parameter (not json) to ensure proper multipart/form-data encoding
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,  # Use data for form fields with files
                    files=files,
                    timeout=self.settings.timeout,
                    **self._get_auth_params(),
                )
            else:
                # For regular JSON requests
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,  # Use json for regular requests
                    timeout=self.settings.timeout,
                    **self._get_auth_params(),
                )

            # Handle HTTP errors
            if response.status_code >= 400:
                return self._handle_request_errors(response, url, params=params, data=data, files=files)

            # No content
            if response.status_code == 204:
                return None

        except requests.exceptions.ConnectionError as ce:
            logger.error(
                "Unable to connect to Paperless server: %s url %s, params %s, data %s, files %s",
                method,
                url,
                params,
                data,
                files,
            )
            raise RequestError(f"Connection error: {str(ce)}") from ce
        except requests.exceptions.RequestException as re:
            raise RequestError(f"Request failed: {str(re)}") from re

        return response

    def _handle_request_errors(
        self,
        response: requests.Response,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> None:
        """
        Handle HTTP error responses from the API.

        This method analyzes error responses from the Paperless-ngx API and raises
        appropriate exceptions based on the status code and error message.

        Args:
            response: The HTTP response object.
            url: The URL that was requested.
            params: The query parameters that were sent.
            data: The request body data that was sent.
            files: The files that were uploaded.

        Raises:
            ValueError: For 400 errors with missing required fields.
            RelationshipNotFoundError: For 400 errors with invalid relationships.
            AuthenticationError: For 401 authentication failures.
            ConfigurationError: For CSRF token issues.
            InsufficientPermissionError: For 403 permission errors.
            ResourceNotFoundError: For 404 not found errors.
            BadResponseError: For all other error responses.

        """
        error_message = self._extract_error_message(response)

        if response.status_code == 400:
            if "This field is required" in error_message:
                raise ValueError(f"Required field missing: {error_message}")
            if matches := re.match(r"([a-zA-Z_-]+): Invalid pk", error_message):
                raise RelationshipNotFoundError(f"Invalid relationship {matches.group(1)}: {error_message}")
        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}")
        if response.status_code == 403:
            if "this site requires a CSRF" in error_message:
                raise ConfigurationError(f"Response claims CSRF token required. Is the url correct? {url}")
            raise InsufficientPermissionError(f"Permission denied: {error_message}")
        if response.status_code == 404:
            raise ResourceNotFoundError(f"Paperless returned 404 for {url}")

        # All else...
        raise BadResponseError(error_message, response.status_code)

    @overload
    def _handle_response(self, response: requests.Response, *, json_response: Literal[True] = True) -> dict[str, Any]: ...

    @overload
    def _handle_response(self, response: None, *, json_response: bool = True) -> None: ...

    @overload
    def _handle_response(self, response: requests.Response | None, *, json_response: Literal[False]) -> bytes | None: ...

    @overload
    def _handle_response(self, response: requests.Response | None, *, json_response: bool = True) -> dict[str, Any] | bytes | None: ...

    def _handle_response(self, response: requests.Response | None, *, json_response: bool = True) -> dict[str, Any] | bytes | None:
        """Handle the response based on the content type."""
        if response is None:
            return None

        # Try to parse as JSON if requested
        if json_response:
            try:
                return response.json()  # type: ignore # mypy can't infer the return type correctly
            except ValueError as e:
                url = getattr(response, "url", "unknown URL")
                logger.error("Failed to parse JSON response: %s -> url %s -> content: %s", e, url, response.content)
                raise ResponseParsingError(f"Failed to parse JSON response: {str(e)} -> url {url}") from e

        return response.content

    @overload
    def request(
        self,
        method: str,
        endpoint: str | HttpUrl,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...

    @overload
    def request(
        self,
        method: str,
        endpoint: str | HttpUrl,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: Literal[False],
    ) -> bytes | None: ...

    @overload
    def request(
        self,
        method: str,
        endpoint: str | HttpUrl,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: bool = True,
    ) -> dict[str, Any] | bytes | None: ...

    def request(
        self,
        method: str,
        endpoint: str | HttpUrl,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json_response: bool = True,
    ) -> dict[str, Any] | bytes | None:
        """
        Make a request to the Paperless-NgX API and parse the response.

        This method extends request_raw by handling the parsing of the response
        and emitting signals before and after the request. It's the primary method
        used by resources to communicate with the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint relative to base URL or absolute URL.
            params: Query parameters for the request.
            data: Request body data.
            files: Files to upload.
            json_response: Whether to parse the response as JSON (True) or return raw bytes (False).

        Returns:
            If json_response is True, returns a dictionary parsed from the JSON response.
            If json_response is False, returns the raw response bytes.
            Returns None if the server returned a 204 No Content response.

        Raises:
            AuthenticationError: If authentication fails.
            ResourceNotFoundError: If the requested resource doesn't exist.
            ResponseParsingError: If the response cannot be parsed as JSON.
            RequestError: For connection or request failures.
            APIError: For other API errors.

        Note:
            Generally, this should be done using resources, not by calling this method directly.

        Examples:
            >>> data = client.request("GET", "api/documents/123/")
            >>> print(data["title"])
            Invoice March 2023

            >>> # Get binary content
            >>> pdf_bytes = client.request("GET", "api/documents/123/download/", json_response=False)

        """
        kwargs = {
            "client": self,
            "method": method,
            "endpoint": endpoint,
            "params": params,
            "data": data,
            "files": files,
            "json_response": json_response,
        }

        registry.emit("client.request:before", "Before a request is sent to the Paperless server", args=[self], kwargs=kwargs)

        # Get the response from request_raw
        response = self.request_raw(method, endpoint, params=params, data=data, files=files)

        # Only return None if response is exactly None (not just falsey)
        if response is None:
            return None

        registry.emit(
            "client.request__response",
            "After a response is received, before it is parsed",
            args=[response],
            kwargs=kwargs,
        )

        parsed_response = self._handle_response(response, json_response=json_response)
        parsed_response = registry.emit(
            "client.request:after",
            "After a request is parsed.",
            args=parsed_response,
            kwargs=kwargs,
        )

        return parsed_response

    def _extract_error_message(self, response: requests.Response) -> str:
        """
        Extract a human-readable error message from an error response.

        This method attempts to parse the error response in various formats
        to extract the most useful error message for the user.

        Args:
            response: The HTTP error response.

        Returns:
            A string containing the extracted error message.

        """
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                # Try different possible error formats
                if "detail" in error_data:
                    return str(error_data["detail"])
                if "error" in error_data:
                    return str(error_data["error"])
                if "non_field_errors" in error_data:
                    return ", ".join(error_data["non_field_errors"])

                # Handle nested error messages
                messages = []
                for key, value in error_data.items():
                    if isinstance(value, list):
                        values = [str(i) for i in value]
                        messages.append(f"{key}: {', '.join(values)}")
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

        This method allows obtaining a token that can be used for subsequent
        authentication instead of repeatedly sending username and password.

        Args:
            base_url: The base URL of the Paperless-NgX instance.
            username: Username for authentication.
            password: Password for authentication.
            timeout: Request timeout in seconds. If None, uses the client's default timeout.

        Returns:
            Generated API token as a string.

        Raises:
            AuthenticationError: If authentication fails due to invalid credentials.
            RequestError: For connection or request failures.
            ResponseParsingError: If the response cannot be parsed or doesn't contain a token.

        Examples:
            >>> token = client.generate_token(
            ...     "https://paperless.example.com",
            ...     "admin",
            ...     "securepassword"
            ... )
            >>> print(token)
            40characterslong40characterslong40charac

        """
        if timeout is None:
            timeout = self.settings.timeout

        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        url = f"{base_url.rstrip('/')}/api/token/"

        registry.emit(
            "client.generate_token__before",
            "Before a new token is generated",
            kwargs={"url": url, "username": username},
        )

        try:
            response = requests.post(
                url,
                json={"username": username, "password": password},
                headers={"Accept": "application/json"},
                timeout=timeout,
            )

            response.raise_for_status()
            data = response.json()

            registry.emit(
                "client.generate_token__after",
                "After a new token is generated",
                kwargs={"url": url, "username": username, "response": data},
            )

            if "token" not in data:
                raise ResponseParsingError("Token not found in response")

            return str(data["token"])
        except requests.exceptions.HTTPError as he:
            if he.response.status_code == 401:
                raise AuthenticationError("Invalid username or password") from he
            try:
                error_data = he.response.json()
                error_message = error_data.get("detail", str(he))
            except (ValueError, KeyError):
                error_message = str(he)

            raise RequestError(f"Failed to generate token: {error_message}") from he
        except requests.exceptions.RequestException as re:
            raise RequestError(f"Error while requesting a new token: {str(re)}") from re
        except (ValueError, KeyError) as ve:
            raise ResponseParsingError(f"Failed to parse response when generating token: {str(ve)}") from ve

    def get_statistics(self) -> dict[str, Any]:
        """
        Get system statistics from the Paperless-ngx server.

        This method retrieves statistics about the Paperless-ngx system,
        including document counts, storage usage, and other metrics.

        Returns:
            Dictionary containing system statistics.

        Raises:
            APIError: If the statistics cannot be retrieved.

        Examples:
            >>> stats = client.get_statistics()
            >>> print(f"Total documents: {stats['documents_total']}")
            Total documents: 1250

        """
        if result := self.request("GET", "api/statistics/"):
            return result
        raise APIError("Failed to get statistics")

    def get_system_status(self) -> dict[str, Any]:
        """
        Get system status from the Paperless-ngx server.

        This method retrieves information about the current status of the
        Paperless-ngx system, including version information, task queue status,
        and other operational metrics.

        Returns:
            Dictionary containing system status information.

        Raises:
            APIError: If the status information cannot be retrieved.

        Examples:
            >>> status = client.get_system_status()
            >>> print(f"Paperless version: {status['version']}")
            Paperless version: 1.14.5

        """
        if result := self.request("GET", "api/status/"):
            return result
        raise APIError("Failed to get system status")

    def get_config(self) -> dict[str, Any]:
        """
        Get system configuration from the Paperless-ngx server.

        This method retrieves the current configuration settings of the
        Paperless-ngx server, including feature flags, settings, and
        other configuration parameters.

        Returns:
            Dictionary containing system configuration.

        Raises:
            APIError: If the configuration cannot be retrieved.

        Examples:
            >>> config = client.get_config()
            >>> print(f"OCR language: {config['ocr_language']}")
            OCR language: eng

        """
        if result := self.request("GET", "api/config/"):
            return result
        raise APIError("Failed to get system configuration")
