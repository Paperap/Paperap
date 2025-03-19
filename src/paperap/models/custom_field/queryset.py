"""
----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional, Self, Union

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasDocumentCount

if TYPE_CHECKING:
    from paperap.models.custom_field.model import CustomField

logger = logging.getLogger(__name__)


class CustomFieldQuerySet(StandardQuerySet["CustomField"], HasDocumentCount):
    """
    QuerySet for Paperless-ngx custom fields with specialized filtering methods.
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter custom fields by name.

        Args:
            value: The custom field name to filter by
            exact: If True, match the exact name, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered CustomFieldQuerySet

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def data_type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter custom fields by data type.

        Args:
            value: The data type to filter by (e.g., "string", "integer", "boolean", "date")
            exact: If True, match the exact data type, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered CustomFieldQuerySet

        """
        return self.filter_field_by_str("data_type", value, exact=exact, case_insensitive=case_insensitive)

    def extra_data(self, key: str, value: Any) -> Self:
        """
        Filter custom fields by a key-value pair in extra_data.

        Args:
            key: The key in extra_data to filter by
            value: The value to filter by

        Returns:
            Filtered CustomFieldQuerySet

        """
        filter_key = f"extra_data__{key}"
        return self.filter(**{filter_key: value})
