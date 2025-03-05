"""




----------------------------------------------------------------------------

   METADATA:

       File:    custom_fields.py
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

from __future__ import annotations

from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class CustomFieldResource(StandardResource[CustomField, CustomFieldQuerySet]):
    """Resource for managing custom fields."""

    model_class = CustomField
    name = "custom_fields"
