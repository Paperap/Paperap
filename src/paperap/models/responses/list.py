"""
Response models for list-based API responses from Paperless-ngx.

This module contains models that represent paginated list responses from the
Paperless-ngx API. These models handle the standard response format for
collections of resources, including pagination metadata.
"""

from __future__ import annotations

from paperap.models.abstract import StandardModel


class ListResponse(StandardModel):
    """
    Model representing a paginated list response from the Paperless-ngx API.

    This class models the standard structure of list responses returned by the
    Paperless-ngx API, which include pagination metadata and the actual results.
    While not currently used in the main codebase, it's maintained for documentation
    and potential future implementation.

    Attributes:
        count (int): Total number of items across all pages.
        next (str | None): URL to fetch the next page of results, or None if this is the last page.
        previous (str | None): URL to fetch the previous page of results, or None if this is the first page.
        all (list[int]): List of IDs for all items matching the query, across all pages.
        results (list[StandardModel]): List of model instances for the current page.

    Example:
        ```python
        # Example of what a ListResponse might look like when implemented
        response = ListResponse(
            count=150,
            next="https://paperless.example.com/api/documents/?page=2",
            previous=None,
            all=[1, 2, 3, 4, ...],
            results=[Document(...), Document(...), ...]
        )

        # Access total count
        total = response.count

        # Iterate through current page results
        for document in response.results:
            print(document.title)
        ```

    """

    count: int
    next: str | None
    previous: str | None
    all: list[int]
    results: list[StandardModel]
