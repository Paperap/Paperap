"""
Define exception hierarchy for the Paperap library.

This module contains all exceptions that may be raised by the Paperap library
during its operation. The exceptions form a hierarchy with PaperapError as the
base class, allowing applications to catch specific or general error types as needed.
"""

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
    Raise when a model fails validation.

    This exception occurs when a Pydantic model fails validation, typically
    when creating or updating a model with invalid data.

    Args:
        message: Custom error message. If None, a default message is generated.
        model: The Pydantic model that failed validation.

    Examples:
        >>> try:
        ...     client.documents.create(invalid_field="value")
        ... except ModelValidationError as e:
        ...     print(f"Validation error: {e}")

    """

    def __init__(self, message: str | None = None, model: pydantic.BaseModel | None = None) -> None:
        if not message:
            message = f"Model failed validation for {model.__class__.__name__}."
        super().__init__(message)


class ReadOnlyFieldError(ModelValidationError):
    """
    Raise when a read-only field is modified.

    This exception occurs when an attempt is made to modify a field that
    is marked as read-only in the model's Meta configuration.

    Examples:
        >>> try:
        ...     document.id = 456  # id is typically read-only
        ... except ReadOnlyFieldError as e:
        ...     print(f"Cannot modify read-only field: {e}")

    """


class ConfigurationError(PaperapError):
    """
    Raise when the client configuration is invalid.

    This exception occurs when there's an issue with the client configuration,
    such as missing required settings or invalid connection parameters.

    Examples:
        >>> try:
        ...     client = PaperlessClient(base_url="invalid://url")
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")

    """


class PaperlessError(PaperapError):
    """
    Raise when an error is specific to the Paperless-NgX server.

    This exception occurs when an error is specific to the Paperless-NgX server
    or its API, rather than the Paperap client itself.

    Examples:
        >>> try:
        ...     # An operation that depends on a Paperless-NgX feature
        ...     client.documents.merge([1, 2, 3])
        ... except PaperlessError as e:
        ...     print(f"Paperless server error: {e}")

    """


class APIError(PaperlessError):
    """
    Raise when the Paperless-NgX API returns an error.

    This exception occurs when the Paperless-NgX API returns an error response.
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
    Raise when authentication with the Paperless-NgX server fails.

    This exception occurs when the client fails to authenticate with the
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
    Raise when a user lacks permission for an operation.

    This exception occurs when the authenticated user lacks the necessary
    permissions to perform the requested operation on the Paperless-NgX server.

    Examples:
        >>> try:
        ...     # Attempting an admin-only operation with a regular user account
        ...     client.users.create(username="new_user")
        ... except InsufficientPermissionError as e:
        ...     print(f"Permission denied: {e}")

    """


class FeatureNotAvailableError(APIError):
    """
    Raise when attempting to use an unavailable feature.

    This exception occurs when attempting to use a feature that is not
    available in the current version of Paperless-NgX or has been disabled
    in the server configuration.

    Examples:
        >>> try:
        ...     # Using a feature only available in newer versions
        ...     client.documents.bulk_edit(...)
        ... except FeatureNotAvailableError as e:
        ...     print(f"Feature not available: {e}")

    """


class FilterDisabledError(FeatureNotAvailableError):
    """
    Raise when attempting to use an unavailable filter.

    This exception occurs when attempting to use a filter that has been
    disabled in the model's Meta configuration or is not supported by the API.

    Examples:
        >>> try:
        ...     client.documents.filter(unsupported_field="value")
        ... except FilterDisabledError as e:
        ...     print(f"Filter not available: {e}")

    """


class RequestError(APIError):
    """
    Raise when an HTTP request fails.

    This exception occurs when there's an error in the HTTP request itself,
    such as a connection error, timeout, or invalid URL.

    Examples:
        >>> try:
        ...     client.request("GET", "invalid/endpoint")
        ... except RequestError as e:
        ...     print(f"Request failed: {e}")

    """


class BadResponseError(APIError):
    """
    Raise when the API returns a non-success status code.

    This exception occurs when the API returns a non-success status code,
    indicating that the request was received but could not be processed successfully.

    Examples:
        >>> try:
        ...     client.request("POST", "documents/", data={"invalid": "data"})
        ... except BadResponseError as e:
        ...     print(f"Bad response: {e.status_code} - {e}")

    """


class ResponseParsingError(APIError):
    """
    Raise when the API response cannot be parsed.

    This exception occurs when the API returns a response that cannot be
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
    Raise when a requested API resource is not found.

    This exception occurs when the requested API resource (endpoint) does not exist
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
    Raise when a requested model relationship is not found.

    This exception occurs when attempting to access a relationship that
    does not exist on a model, such as a foreign key or many-to-many relationship.

    Examples:
        >>> try:
        ...     document.nonexistent_relationship
        ... except RelationshipNotFoundError as e:
        ...     print(f"Relationship not found: {e}")

    """


class ObjectNotFoundError(ResourceNotFoundError):
    """
    Raise when a requested object is not found by ID.

    This exception occurs when attempting to retrieve a specific object by ID
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
    Raise when multiple objects are found when only one was expected.

    This exception occurs when a query that should return a single object
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
    Raise when an error occurs with a local document file.

    This exception occurs when there's an issue with a local document file,
    such as when uploading or processing a document.

    Examples:
        >>> try:
        ...     client.documents.upload("nonexistent_file.pdf")
        ... except DocumentError as e:
        ...     print(f"Document error: {e}")

    """


class NoImagesError(DocumentError):
    """
    Raise when no images or pages are found in a document.

    This exception occurs when attempting to process a document that
    contains no images or pages that can be processed.

    Examples:
        >>> try:
        ...     client.documents.upload("empty.pdf")
        ... except NoImagesError as e:
        ...     print(f"Cannot process PDF: {e}")

    """


class DocumentParsingError(DocumentError):
    """
    Raise when a document cannot be parsed or content extracted.

    This exception occurs when the system fails to parse or extract content
    from a document, typically due to an unsupported format or corrupted file.

    Examples:
        >>> try:
        ...     client.documents.upload("corrupted.pdf")
        ... except DocumentParsingError as e:
        ...     print(f"Failed to parse document: {e}")

    """
