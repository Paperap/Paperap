"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    exceptions.py                                                                                        *
*        Project: paperap                                                                                            *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from string import Template


class PaperlessException(Exception):
    """Base exception for all paperless client errors."""

    pass


class APIError(PaperlessException):
    """Raised when the API returns an error."""

    status_code: int | None = None

    def __init__(self, message: str | None = None, status_code: int | None = None):
        self.status_code = status_code
        if not message:
            message = "An error occurred."
        message = f"API Error {status_code}: {message}"
        message = Template(message).safe_substitute(status_code=status_code)
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""

    resource_type: str | None = None

    def __init__(self, message: str | None = None, resource_type: str | None = None):
        self.resource_type = resource_type
        if not message:
            message = "Resource ${resource} not found."
        message = Template(message).safe_substitute(resource=resource_type)
        super().__init__(message, 404)


class ObjectNotFoundError(ResourceNotFoundError):
    """Raised when a requested object is not found."""

    resource_id: int | None = None

    def __init__(self, message: str | None = None, resource_type: str | None = None, resource_id: int | None = None):
        self.resource_id = resource_id
        if not message:
            message = "Resource ${resource} (#${id}) not found."
        message = Template(message).safe_substitute(resource=resource_type, id=resource_id)
        super().__init__(message, resource_type)


class MultipleObjectsFoundError(APIError):
    """Raised when multiple objects are found when only one was expected."""

    pass
