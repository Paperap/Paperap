

from __future__ import annotations

from typing import Any

from pydantic import Field

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
