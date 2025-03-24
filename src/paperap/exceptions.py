

from __future__ import annotations

from string import Template

import pydantic


class PaperapError(Exception):
    """
    Base exception for all paperless client errors.

    This is the parent class for all exceptions raised by the Paperap library.
    All custom exceptions inherit from this class, allowing users to catch any
    Paperap-related exception with a single except clause.

    Examples:
        >>> try:
        ...     client.documents.get(99999)
        ... except PaperapError as e:
        ...     print(f"Paperap error occurred: {e}")

    """


class ModelValidationError(PaperapError, ValueError):
    """
    Raised when a model fails validation.

    This exception is raised when a Pydantic model fails validation, typically
    when creating or updating a model with invalid data.

    Args:
        message: Custom error message. If None, a default message is generated.
        model: The Pydantic model that failed validation.

    """

    def __init__(self, message: str | None = None, model: pydantic.BaseModel | None = None) -> None:
        if not message:
            message = f"Model failed validation for {model.__class__.__name__}."
        super().__init__(message)


class ReadOnlyFieldError(ModelValidationError):
    """
    Raised when a read-only field is set.

    This exception is raised when an attempt is made to modify a field that
    is marked as read-only in the model's Meta configuration.

    Examples:
        >>> try:
        ...     document.id = 456  # id is typically read-only
        ... except ReadOnlyFieldError as e:
        ...     print(f"Cannot modify read-only field: {e}")

    """


class ConfigurationError(PaperapError):
    """
    Raised when the configuration is invalid.

    This exception is raised when there's an issue with the client configuration,
    such as missing required settings or invalid connection parameters.

    Examples:
        >>> try:
        ...     client = PaperlessClient(base_url="invalid://url")
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")

    """


class PaperlessError(PaperapError):
    """
    Raised due to a feature or error of Paperless-NgX.

    This exception is raised when an error occurs that is specific to the
    Paperless-NgX server or its API, rather than the Paperap client.
    """


class APIError(PaperlessError):
    """
    Raised when the API returns an error.

    This exception is raised when the Paperless-NgX API returns an error response.
    It includes the HTTP status code and error message from the API.

    Args:
        message: Error message from the API. If None, a default message is used.
        status_code: HTTP status code returned by the API.

    Attributes:
        status_code: HTTP status code returned by the API.

    Examples:
        >>> try:
        ...     client.documents.create(title="Test")  # Missing required file
        ... except APIError as e:
        ...     print(f"API Error {e.status_code}: {e}")

    """

    status_code: int | None = None

    def __init__(self, message: str | None = None, status_code: int | None = None) -> None:
        self.status_code = status_code
        if not message:
            message = "An error occurred."
        message = f"API Error {status_code}: {message}"
        message = Template(message).safe_substitute(status_code=status_code)
        super().__init__(message)


class AuthenticationError(APIError):
    """
    Raised when authentication fails.

    This exception is raised when the client fails to authenticate with the
    Paperless-NgX server, typically due to invalid credentials or an expired token.

    Examples:
        >>> try:
        ...     client = PaperlessClient(token="invalid_token")
        ...     client.documents.all()
        ... except AuthenticationError as e:
        ...     print(f"Authentication failed: {e}")

    """


class InsufficientPermissionError(APIError):
    """
    Raised when a user does not have permission to perform an action.

    This exception is raised when the authenticated user lacks the necessary
    permissions to perform the requested operation on the Paperless-NgX server.
    """


class FeatureNotAvailableError(APIError):
    """
    Raised when a feature is not available.

    This exception is raised when attempting to use a feature that is not
    available in the current version of Paperless-NgX or has been disabled
    in the server configuration.
    """


class FilterDisabledError(FeatureNotAvailableError):
    """
    Raised when a filter is not available.

    This exception is raised when attempting to use a filter that has been
    disabled in the model's Meta configuration or is not supported by the API.

    Examples:
        >>> try:
        ...     client.documents.filter(unsupported_field="value")
        ... except FilterDisabledError as e:
        ...     print(f"Filter not available: {e}")

    """


class RequestError(APIError):
    """
    Raised when an error occurs while making a request.

    This exception is raised when there's an error in the HTTP request itself,
    such as a connection error, timeout, or invalid URL.

    Examples:
        >>> try:
        ...     client.request("GET", "invalid/endpoint")
        ... except RequestError as e:
        ...     print(f"Request failed: {e}")

    """


class BadResponseError(APIError):
    """
    Raised when a response is returned, but the status code is not 200.

    This exception is raised when the API returns a non-success status code,
    indicating that the request was received but could not be processed successfully.

    Examples:
        >>> try:
        ...     client.request("POST", "documents/", data={"invalid": "data"})
        ... except BadResponseError as e:
        ...     print(f"Bad response: {e.status_code} - {e}")

    """


class ResponseParsingError(APIError):
    """
    Raised when the response can't be parsed.

    This exception is raised when the API returns a response that cannot be
    parsed as expected, typically due to an unexpected format or content type.

    Examples:
        >>> try:
        ...     client.request("GET", "documents/", json_response=True)
        ...     # Assuming the response is not valid JSON
        ... except ResponseParsingError as e:
        ...     print(f"Failed to parse response: {e}")

    """


class ResourceNotFoundError(APIError):
    """
    Raised when a requested resource is not found.

    This exception is raised when the requested API resource (endpoint) does not exist
    or is not available.

    Args:
        message: Custom error message. If None, a default message is generated.
        resource_name: Name of the resource that was not found.

    Attributes:
        resource_name: Name of the resource that was not found.

    Examples:
        >>> try:
        ...     client.request("GET", "nonexistent_resource/")
        ... except ResourceNotFoundError as e:
        ...     print(f"Resource not found: {e.resource_name}")

    """

    resource_name: str | None = None

    def __init__(self, message: str | None = None, resource_name: str | None = None) -> None:
        self.resource_name = resource_name
        if not message:
            message = "Resource ${resource} not found."
        message = Template(message).safe_substitute(resource=resource_name)
        super().__init__(message, 404)


class RelationshipNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested relationship is not found.

    This exception is raised when attempting to access a relationship that
    does not exist on a model, such as a foreign key or many-to-many relationship.

    Examples:
        >>> try:
        ...     document.nonexistent_relationship
        ... except RelationshipNotFoundError as e:
        ...     print(f"Relationship not found: {e}")

    """


class ObjectNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested object is not found.

    This exception is raised when attempting to retrieve a specific object by ID
    that does not exist in the Paperless-NgX database.

    Args:
        message: Custom error message. If None, a default message is generated.
        resource_name: Name of the resource type (e.g., "document", "tag").
        model_id: ID of the object that was not found.

    Attributes:
        model_id: ID of the object that was not found.

    Examples:
        >>> try:
        ...     client.documents.get(99999)  # Non-existent document ID
        ... except ObjectNotFoundError as e:
        ...     print(f"{e.resource_name} with ID {e.model_id} not found")

    """

    model_id: int | None = None

    def __init__(self, message: str | None = None, resource_name: str | None = None, model_id: int | None = None) -> None:
        self.model_id = model_id
        if not message:
            message = "Resource ${resource} (#${pk}) not found."
        message = Template(message).safe_substitute(resource=resource_name, pk=model_id)
        super().__init__(message, resource_name)


class MultipleObjectsFoundError(APIError):
    """
    Raised when multiple objects are found when only one was expected.

    This exception is raised when a query that should return a single object
    returns multiple objects, typically in a get() operation with non-unique filters.

    Examples:
        >>> try:
        ...     # If multiple documents have this exact title
        ...     client.documents.filter(title="Invoice").get()
        ... except MultipleObjectsFoundError as e:
        ...     print(f"Multiple objects found: {e}")

    """


class DocumentError(PaperapError):
    """
    Raised when an error occurs with a local document.

    This exception is raised when there's an issue with a local document file,
    such as when uploading or processing a document.
    """


class NoImagesError(DocumentError):
    """
    Raised when no images are found in a PDF.

    This exception is raised when attempting to process a PDF document that
    contains no images or pages that can be processed.

    Examples:
        >>> try:
        ...     client.documents.upload("empty.pdf")
        ... except NoImagesError as e:
        ...     print(f"Cannot process PDF: {e}")

    """


class DocumentParsingError(DocumentError):
    """
    Raised when a document cannot be parsed.

    This exception is raised when the system fails to parse or extract content
    from a document, typically due to an unsupported format or corrupted file.

    Examples:
        >>> try:
        ...     client.documents.upload("corrupted.pdf")
        ... except DocumentParsingError as e:
        ...     print(f"Failed to parse document: {e}")

    """
