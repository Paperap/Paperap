"""
Module for managing custom field resources in the Paperless-NgX API.

This module provides the CustomFieldResource class which encapsulates all interactions
with custom fields in a Paperless-NgX system. It leverages the underlying StandardResource
functionality to provide CRUD operations, filtering, and other specialized behaviors for
custom field management.

Custom fields allow users to define additional metadata fields for documents beyond
the standard fields provided by Paperless-NgX. These fields can be of various data types
including string, integer, boolean, date, etc.

Example:
    >>> custom_field = client.custom_fields.create(name="Priority", data_type="string")
    >>> print(f"Created field ID: {custom_field.id}")

"""

from __future__ import annotations

from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.resources.base import BaseResource, StandardResource


class CustomFieldResource(StandardResource[CustomField, CustomFieldQuerySet]):
    """
    CustomFieldResource handles operations related to custom fields in the Paperless-NgX API.

    This resource class extends the StandardResource to provide CRUD operations,
    robust filtering, and other specialized methods for managing custom fields,
    allowing users to define, update, and remove custom metadata on documents.

    Custom fields can be of various data types including:
        - string: Text values
        - integer: Numeric values
        - boolean: True/False values
        - date: Date values (ISO format)
        - monetary: Currency values
        - url: Web addresses

    Attributes:
        model_class (Type[CustomField]): The model class representing a custom field.
        queryset_class (Type[CustomFieldQuerySet]): The queryset class for handling
            lists of custom field models.
        name (str): The base endpoint name for custom fields in the API.

    Example:
        >>> # Create a new custom field
        >>> date_field = client.custom_fields.create(
        ...     name="Due Date",
        ...     data_type="date"
        ... )
        >>> # Get all custom fields
        >>> all_fields = client.custom_fields.all()
        >>> # Get a specific custom field
        >>> field = client.custom_fields.get(1)
        >>> # Update a custom field
        >>> field.name = "Updated Name"
        >>> field.save()

    """

    model_class = CustomField
    queryset_class = CustomFieldQuerySet
    name: str = "custom_fields"
