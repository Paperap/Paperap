

"""
Module for managing custom field resources in the Paperless-NgX API.

This module provides the CustomFieldResource class which encapsulates all interactions
with custom fields in a Paperless-NgX system. It leverages the underlying StandardResource
functionality to provide CRUD operations, filtering, and other specialized behaviors for
custom field management.

Example:
    >>> from paperap.resources.custom_fields import CustomFieldResource
    >>> resource = CustomFieldResource(client)
    >>> custom_field = resource.create(name="Priority", data_type="string")

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

    Attributes:
        model_class (Type[CustomField]): The model class representing a custom field.
        queryset_class (Type[CustomFieldQuerySet]): The queryset class for handling lists of custom field models.
        name (str): The base endpoint name for custom fields in the API.

    Example:
        >>> from paperap.resources.custom_fields import CustomFieldResource
        >>> resource = CustomFieldResource(client)
        >>> new_field = resource.create(name="Priority", data_type="string")

    """

    model_class = CustomField
    queryset_class = CustomFieldQuerySet
    name: str = "custom_fields"
