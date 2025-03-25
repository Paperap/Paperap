"""
Provide specialized queryset for custom fields in Paperless-ngx.

This module implements the CustomFieldQuerySet class, which extends the standard
queryset functionality with methods specific to custom fields. It enables
filtering by name, data type, and extra data properties.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, Union

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasDocumentCount

if TYPE_CHECKING:
    from paperap.models.custom_field.model import CustomField

logger = logging.getLogger(__name__)


class CustomFieldQuerySet(StandardQuerySet["CustomField"], HasDocumentCount):
    """
    Manage and filter custom fields from Paperless-ngx.

    Extends StandardQuerySet to provide specialized filtering methods for custom
    fields. Allows filtering by name, data type, and extra data, making it easier
    to find and manage custom fields.

    The QuerySet is lazy-loaded, meaning API requests are only made when the
    results are actually needed (when iterating, counting, etc.).

    Attributes:
        Inherits all attributes from StandardQuerySet and HasDocumentCount.

    Examples:
        Get all string-type custom fields:
            >>> string_fields = client.custom_fields().data_type("string")

        Find custom fields with a specific name pattern:
            >>> invoice_fields = client.custom_fields().name("invoice", exact=False)

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter custom fields by name.

        Filter the queryset to include only custom fields whose names match the
        specified value, with options for exact matching and case sensitivity.

        Args:
            value: The custom field name to filter by.
            exact: If True, match the exact name; if False, use contains matching.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered CustomFieldQuerySet containing only matching custom fields.

        Examples:
            Find fields with exact name "Invoice Number":
                >>> invoice_fields = client.custom_fields().name("Invoice Number")

            Find fields containing "date" (case-insensitive):
                >>> date_fields = client.custom_fields().name("date", exact=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def data_type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter custom fields by data type.

        Filter the queryset to include only custom fields with the specified data type.
        Paperless-ngx supports several data types for custom fields, including string,
        integer, boolean, date, etc.

        Args:
            value: The data type to filter by (e.g., "string", "integer", "boolean", "date").
            exact: If True, match the exact data type; if False, use contains matching.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered CustomFieldQuerySet containing only custom fields with matching data types.

        Examples:
            Get all date-type custom fields:
                >>> date_fields = client.custom_fields().data_type("date")

            Get all numeric fields (integer or float):
                >>> numeric_fields = client.custom_fields().data_type("int", exact=False)

        """
        return self.filter_field_by_str("data_type", value, exact=exact, case_insensitive=case_insensitive)

    def extra_data(self, key: str, value: Any) -> Self:
        """
        Filter custom fields by a key-value pair in extra_data.

        Filter custom fields based on specific values within the extra_data JSON structure.
        Custom fields in Paperless-ngx can have additional configuration stored
        in this extra_data field.

        Args:
            key: The key in extra_data to filter by. This can be a nested key
                using Django's double-underscore syntax for JSON fields.
            value: The value to filter by. Can be any JSON-compatible value
                (string, number, boolean, etc.).

        Returns:
            A filtered CustomFieldQuerySet containing only custom fields with matching extra_data values.

        Examples:
            Find custom fields with specific configuration:
                >>> fields = client.custom_fields().extra_data("format", "currency")

            Find fields with nested configuration:
                >>> fields = client.custom_fields().extra_data("options__default", True)

        """
        filter_key = f"extra_data__{key}"
        return self.filter(**{filter_key: value})
