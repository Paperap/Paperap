"""




----------------------------------------------------------------------------

   METADATA:

       File:    custom_field.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel

if TYPE_CHECKING:
    from paperap.models.document import DocumentQuerySet


class CustomField(StandardModel):
    """
    Represents a custom field in Paperless-NgX.
    """

    name: str
    data_type: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)
    document_count: int = 0

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
        "extra": "allow",
    }

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug"}

    @property
    def documents(self) -> "DocumentQuerySet":
        return self._client.documents().all().has_custom_field_id(self.id)
