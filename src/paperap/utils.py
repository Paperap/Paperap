"""




----------------------------------------------------------------------------

   METADATA:

       File:    utils.py
       Project: paperap
       Created: 2025-03-04
       Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

import json
import os
from datetime import datetime
from typing import Any, BinaryIO, Optional


def datetime_to_str(dt: datetime) -> str:
    """
    Convert a datetime object to an ISO 8601 string for the API.

    Args:
        dt: The datetime object to convert.

    Returns:
        ISO 8601 formatted string.
    """
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def parse_filter_params(**kwargs: Any) -> dict[str, Any]:
    """
    Parse filter parameters for list endpoints.

    Args:
        **kwargs: Filter parameters.

    Returns:
        Dictionary of filter parameters.
    """
    filters = {}
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
