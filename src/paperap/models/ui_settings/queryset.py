"""
Provide query functionality for UI settings in Paperless-NGX.

This module contains the specialized queryset implementation for interacting
with the UI settings endpoint of Paperless-NGX. Unlike most resources that
can return multiple objects, UI settings is a singleton resource that always
returns exactly one object containing all UI configuration settings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, Self, override

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.ui_settings.model import UISettings

logger = logging.getLogger(__name__)


class UISettingsQuerySet(StandardQuerySet["UISettings"]):
    """
    Manage queries for UI settings in Paperless-NGX.

    Extends StandardQuerySet to handle the singleton nature of UI settings,
    which always returns exactly one object containing all UI configuration.
    Unlike typical querysets that can return multiple objects, this queryset
    is specialized for the unique characteristics of the UI settings endpoint.

    Attributes:
        _result_cache (list[UISettings] | None): Cache of fetched UI settings objects.
        _last_response (ClientResponse | None): The last response received from the API.
        resource (Resource): The resource instance associated with the queryset.
        filters (dict[str, Any]): Dictionary of filters to apply to the API request.

    """

    @override
    def count(self) -> Literal[1]:
        """
        Return the count of UI settings objects.

        Overrides the standard count method to always return 1 because the UI settings
        endpoint in Paperless-NGX always returns exactly one object containing
        all UI configuration settings.

        Returns:
            Literal[1]: Always returns 1, as there is only one UI settings object.

        Example:
            ```python
            settings_count = client.ui_settings().count()
            print(settings_count)  # Output: 1
            ```

        """
        return 1

    def has_permission(self, value: str) -> Self:
        """
        Filter UI settings by checking if a specific permission exists.

        Creates a filtered queryset that checks whether a specific permission
        is included in the permissions list. This method is useful for determining
        if the current user has a particular permission in the Paperless-NGX system.

        Args:
            value (str): The permission string to check for in the permissions list.
                Common permissions include "view_document", "change_document", etc.

        Returns:
            Self: A new queryset filtered to include only settings with the specified permission.

        Example:
            ```python
            # Check if the current user has permission to add documents
            if client.ui_settings().has_permission("add_document").exists():
                print("User can add documents")
            else:
                print("User cannot add documents")
            ```

        """
        return self.filter(permissions__contains=value)
