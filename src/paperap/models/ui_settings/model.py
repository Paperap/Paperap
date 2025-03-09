"""




----------------------------------------------------------------------------

   METADATA:

       File:    ui_settings.py
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

from typing import Any

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.ui_settings.queryset import UISettingsQuerySet


class UISettings(StandardModel):
    """
    Represents UI settings in Paperless-NgX.
    """

    user: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any]
    permissions: list[str] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        queryset = UISettingsQuerySet
