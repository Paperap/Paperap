"""
----------------------------------------------------------------------------

   METADATA:

       File:    exceptions.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.8
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from string import Template

import pydantic


class PaperlessError(Exception):
    """Base exception for all paperless client errors."""


class ModelValidationError(PaperlessError, ValueError):
    """Raised when a model fails validation."""

    def __init__(self, message: str | None = None, model: pydantic.BaseModel | None = None) -> None:
        if not message:
            message = f"Model failed validation for {model.__class__.__name__}."
        super().__init__(message)

class ReadOnlyFieldError(ModelValidationError):
    """Raised when a read-only field is set."""

class ConfigurationError(PaperlessError):
    """Raised when the configuration is invalid."""


class APIError(PaperlessError):
    """Raised when the API returns an error."""

    status_code: int | None = None

    def __init__(self, message: str | None = None, status_code: int | None = None) -> None:
        self.status_code = status_code
        if not message:
            message = "An error occurred."
        message = f"API Error {status_code}: {message}"
        message = Template(message).safe_substitute(status_code=status_code)
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when authentication fails."""


class InsufficientPermissionError(APIError):
    """Raised when a user does not have permission to perform an action."""


class FeatureNotAvailableError(APIError):
    """Raised when a feature is not available."""


class FilterDisabledError(FeatureNotAvailableError):
    """Raised when a filter is not available."""


class RequestError(APIError):
    """Raised when an error occurs while making a request."""


class BadResponseError(APIError):
    """Raised when a response is returned, but the status code is not 200."""


class ResponseParsingError(APIError):
    """Raised when the response can't be parsed."""


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""

    resource_name: str | None = None

    def __init__(self, message: str | None = None, resource_name: str | None = None) -> None:
        self.resource_name = resource_name
        if not message:
            message = "Resource ${resource} not found."
        message = Template(message).safe_substitute(resource=resource_name)
        super().__init__(message, 404)


class ObjectNotFoundError(ResourceNotFoundError):
    """Raised when a requested object is not found."""

    model_id: int | None = None

    def __init__(
        self, message: str | None = None, resource_name: str | None = None, model_id: int | None = None
    ) -> None:
        self.model_id = model_id
        if not message:
            message = "Resource ${resource} (#${pk}) not found."
        message = Template(message).safe_substitute(resource=resource_name, pk=model_id)
        super().__init__(message, resource_name)


class MultipleObjectsFoundError(APIError):
    """Raised when multiple objects are found when only one was expected."""
