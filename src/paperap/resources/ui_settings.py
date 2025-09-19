"""
Provide access to Paperless-NgX UI settings.

This module contains the resource class for interacting with the UI settings
endpoint of the Paperless-NgX API. It allows retrieving and updating the
current user's UI settings.
"""

from __future__ import annotations

from typing import Any, Iterator, override

from paperap.models.ui_settings import UISettings, UISettingsQuerySet
from paperap.resources.base import BaseResource, StandardResource


class UISettingsResource(StandardResource[UISettings, UISettingsQuerySet]):
    """
    Resource for managing UI settings in Paperless-NgX.

    This class provides methods to interact with the UI settings endpoint
    of the Paperless-NgX API, allowing for operations such as retrieving
    and updating the current user's UI settings.

    Attributes:
        model_class: The UISettings model class associated with this resource.
        queryset_class: The UISettingsQuerySet class used for querying UI settings.
        name: The name of the resource used in API endpoints.

    """

    model_class = UISettings
    queryset_class = UISettingsQuerySet
    name = "ui_settings"

    def get_current(self) -> UISettings | None:
        """
        Get the current user's UI settings.

        Makes a GET request to the UI settings endpoint to retrieve the
        current user's UI settings configuration.

        Returns:
            UISettings: The current user's UI settings object, or None if
                no settings exist or the request failed.

        Example:
            ```python
            client = PaperlessClient()
            ui_settings = client.ui_settings.get_current()
            if ui_settings:
                print(f"Dark mode enabled: {ui_settings.settings.get('dark_mode', False)}")
            ```

        """
        if not (response := self.client.request("GET", "ui_settings/")):
            return None

        if response:
            return self.parse_to_model(response)
        return None

    def update_current(self, settings: dict[str, Any]) -> UISettings:
        """
        Update the current user's UI settings.

        Retrieves the current UI settings, updates them with the provided
        settings dictionary, and saves the changes back to the server.
        If no settings exist for the current user, creates new settings.

        Args:
            settings: Dictionary of UI settings to update. Keys should match
                the expected UI settings keys in Paperless-NgX.

        Returns:
            UISettings: The updated UI settings object.

        Example:
            ```python
            client = PaperlessClient()
            # Update dark mode and sidebar settings
            updated_settings = client.ui_settings.update_current({
                "dark_mode": True,
                "sidebar_show_inbox": True
            })
            ```

        """
        ui_settings = self.get_current()
        if ui_settings:
            ui_settings.settings.update(settings)
            return self.update(ui_settings)

        # Create new settings
        return self.create(**{"settings": settings})

    @override
    def delete(self, model: int | UISettings | list[int | UISettings]) -> None:
        """
        Delete UI settings (not supported).

        Raises:
            NotImplementedError: Always raised as deletion is not supported.

        """
        raise NotImplementedError("Cannot delete UI settings, per Paperless NGX REST Api")
