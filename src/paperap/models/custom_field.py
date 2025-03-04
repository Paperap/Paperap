"""




----------------------------------------------------------------------------

   METADATA:

       File:    custom_field.py
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

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class CustomField(PaperlessModel):
    """
    Represents a custom field in Paperless-NgX.
    """

    name: str
    slug: str
    data_type: int  # 0=text, 1=integer, 2=float, 3=boolean, 4=monetary, 5=date
    required: bool
    document_types: list[int] = Field(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
        "extra": "allow",
        "json_encoders": {},
    }

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug"}
