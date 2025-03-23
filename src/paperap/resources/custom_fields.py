

from __future__ import annotations

from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.resources.base import BaseResource, StandardResource


class CustomFieldResource(StandardResource[CustomField, CustomFieldQuerySet]):
    """Resource for managing custom fields."""

    model_class = CustomField
    queryset_class = CustomFieldQuerySet
    name: str = "custom_fields"
