"""




----------------------------------------------------------------------------

METADATA:

File:    ui_settings.py
Project: paperap
Created: 2025-03-21
Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-21     By Jess Mann

"""

from __future__ import annotations

from typing import Any, Iterator, override

from paperap.models.ui_settings import UISettings, UISettingsQuerySet
from paperap.resources.base import BaseResource, StandardResource


class UISettingsResource(StandardResource[UISettings, UISettingsQuerySet]):
    """Resource for managing UI settings."""

    model_class = UISettings
    queryset_class = UISettingsQuerySet
    name = "ui_settings"

    def get_current(self) -> UISettings | None:
        """
        Get the current user's UI settings.

        Returns:
            The current user's UI settings.

        """
        if not (response := self.client.request("GET", "ui_settings/")):
            return None

        if response:
            return self.parse_to_model(response)
        return None

    def update_current(self, settings: dict[str, Any]) -> UISettings:
        """
        Update the current user's UI settings.

        Args:
            settings: The settings to update.

        Returns:
            The updated UI settings.

        """
        ui_settings = self.get_current()
        if ui_settings:
            ui_settings.settings.update(settings)
            return self.update(ui_settings)

        # Create new settings
        return self.create(**{"settings": settings})

    @override
    def delete(self, model_id: int | UISettings) -> None:
        raise NotImplementedError("Cannot delete UI settings, per Paperless NGX REST Api")
