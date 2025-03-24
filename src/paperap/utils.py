"""
Utility functions for the Paperap library.

This module provides common utility functions used throughout the Paperap library,
including data conversion, parameter parsing, and other helper functions.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, BinaryIO


def datetime_to_str(dt: datetime | None) -> str | None:
    """
    Convert a datetime object to an ISO 8601 string for the API.

    This function converts a datetime object to an ISO 8601 formatted string
    that is compatible with the Paperless-NgX API. It handles timezone information
    and ensures proper formatting of the output string.

    Args:
        dt: The datetime object to convert.
            If None is provided, None will be returned.

    Returns:
        str or None: ISO 8601 formatted string (e.g., "2023-04-15T14:30:45Z")
            or None if the input is None.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2023, 4, 15, 14, 30, 45, tzinfo=timezone.utc)
        >>> datetime_to_str(dt)
        '2023-04-15T14:30:45Z'

    """
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def parse_filter_params(**kwargs: Any) -> dict[str, Any]:
    """
    Parse filter parameters for list endpoints.

    This function processes filter parameters for API requests, handling special
    cases like datetime objects and lists. It ensures that parameters are properly
    formatted for the Paperless-NgX API.

    Args:
        **kwargs: Filter parameters as keyword arguments. These can include:
            - Simple filters (e.g., title="Invoice")
            - Field lookups (e.g., created__gt=datetime_obj)
            - List filters (e.g., tags__id__in=[1, 2, 3])

    Returns:
        dict[str, Any]: Dictionary of processed filter parameters ready for API use.

    Examples:
        >>> from datetime import datetime
        >>> params = parse_filter_params(
        ...     title__contains="invoice",
        ...     created__gt=datetime(2023, 1, 1),
        ...     tags__id__in=[1, 2, 3]
        ... )
        >>> params
        {'title__contains': 'invoice', 'created__gt': '2023-01-01T00:00:00', 'tags__id__in': '1,2,3'}

    """
    filters: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, datetime):
                filters[key] = datetime_to_str(value)
            elif isinstance(value, list):
                # Handle list parameters like tags__id__in
                filters[key] = ",".join([str(v) for v in value])
            else:
                filters[key] = value
    return filters
