"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
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

from typing import Any, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasDocumentCount

if TYPE_CHECKING:
    from paperap.models.custom_field.model import CustomField

logger = logging.getLogger(__name__)


class CustomFieldQuerySet(StandardQuerySet["CustomField"], HasDocumentCount):
    """
    QuerySet for Paperless-ngx custom fields with specialized filtering methods.
    """

    def name(self, name: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter custom fields by name.

        Args:
            name: The custom field name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered CustomFieldQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def data_type(self, data_type: str) -> Self:
        """
        Filter custom fields by data type.

        Args:
            data_type: The data type to filter by (e.g., "string", "integer", "boolean", "date")

        Returns:
            Filtered CustomFieldQuerySet
        """
        return self.filter(data_type=data_type)
