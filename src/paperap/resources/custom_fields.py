from __future__ import annotations

from paperap.models.custom_field import CustomField
from paperap.resources.base import PaperlessResource


class CustomFieldResource(PaperlessResource[CustomField]):
    """Resource for managing custom fields."""

    model_class = CustomField
