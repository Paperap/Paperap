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

from paperap.models.custom_field import CustomField
from paperap.resources.base import PaperlessResource


class CustomFieldResource(PaperlessResource[CustomField]):
    """Resource for managing custom fields."""

    model_class = CustomField
    name = "custom_fields"
