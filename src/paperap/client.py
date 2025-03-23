

from __future__ import annotations

import logging
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

    Args:
        settings: Settings object containing client configuration.

    Examples:
        ```python
        # Using token authentication
        client = PaperlessClient(
            Settings(
                base_url="https://paperless.example.com",
                token="40characterslong40characterslong40charac"
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
                "Accept": "application/json; version=2",
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
        """Get the base URL."""
        return self.settings.base_url

    def __enter__(self) -> PaperlessClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _init_resources(self) -> None:
        """Initialize all API resources."""
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

        Args:
            plugin_config: Optional configuration dictionary for plugins.

        """
        from paperap.plugins.manager import PluginManager  # pylint: disable=import-outside-toplevel

        PluginManager.model_rebuild()

        # Create and configure the plugin manager
        self.manager = PluginManager(client=self)

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
        """Get authentication parameters for requests."""
        return self.auth.get_auth_params()

    def get_headers(self) -> dict[str, str]:
        """Get headers for requests."""
        headers = {}

        headers.update(self.auth.get_auth_headers())

        return headers

    def close(self) -> None:
        """Close the client and release resources."""
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
            PaperapError: For other errors.

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
        Make a request to the Paperless-NgX API.

        Generally, this should be done using resources, not by calling this method directly.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint relative to base URL.
            params: Query parameters for the request.
            data: Request body data.
            files: Files to upload.
            json_response: Whether to parse the response as JSON.

        Returns:
            Parsed response data.

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

        if not (response := self.request_raw(method, endpoint, params=params, data=data, files=files)):
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
        """Extract error message from response."""
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

        Args:
            base_url: The base URL of the Paperless-NgX instance.
            username: Username for authentication.
            password: Password for authentication.
            timeout: Request timeout in seconds.

        Returns:
            Generated API token.

        Raises:
            AuthenticationError: If authentication fails.
            PaperapError: For other errors.

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
