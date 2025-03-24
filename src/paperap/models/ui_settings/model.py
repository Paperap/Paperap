"""
UI Settings model for Paperless-NgX.

This module provides the UISettings model class for interacting with the
Paperless-NgX UI settings API endpoint. UI settings control the appearance
and behavior of the Paperless-NgX web interface.

Typical usage example:
    ```python
    # Get the current user's UI settings
    ui_settings = client.ui_settings.get()

    # Access specific settings
    dark_mode = ui_settings.settings.get("dark_mode", False)

    # Update settings
    ui_settings.settings["dark_mode"] = True
    ui_settings.save()
    ```
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from paperap.models.abstract.model import StandardModel
from paperap.models.ui_settings.queryset import UISettingsQuerySet


class UISettings(StandardModel):
    """
    Represents UI settings in Paperless-NgX.

    This model provides access to user-specific UI settings and permissions
    in Paperless-NgX. Unlike most other models, there is typically only one
    UI settings object per user, and it contains all customizable aspects
    of the user interface.

    Attributes:
        user: Dictionary containing user information such as username and ID.
        settings: Dictionary containing all UI settings like theme preferences,
            display options, and other customizable UI elements.
        permissions: List of permission strings indicating what actions the
            current user is allowed to perform in the Paperless-NgX system.

    Examples:
        Get and modify UI settings:
        ```python
        # Get current UI settings
        ui_settings = client.ui_settings.get()

        # Check if dark mode is enabled
        is_dark_mode = ui_settings.settings.get("dark_mode", False)

        # Enable dark mode
        ui_settings.settings["dark_mode"] = True
        ui_settings.save()

        # Check user permissions
        if "view_document" in ui_settings.permissions:
            print("User can view documents")
        ```

    """

    user: dict[str, Any] = Field(default_factory=dict, description="Dictionary containing user information")
    settings: dict[str, Any] = Field(..., description="Dictionary containing all UI settings")
    permissions: list[str] = Field(default_factory=list, description="List of permission strings for the current user")

    class Meta(StandardModel.Meta):
        """
        Metadata for the UISettings model.

        This class defines metadata for the UISettings model, including the
        associated queryset class.

        Attributes:
            queryset: The UISettingsQuerySet class used for querying UI settings.

        """

        queryset = UISettingsQuerySet
