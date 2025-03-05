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

from typing import Any, List, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.custom_field.model import CustomField

logger = logging.getLogger(__name__)


class CustomFieldQuerySet(QuerySet["CustomField"]):
    """
    QuerySet for Paperless-ngx custom fields with specialized filtering methods.
    """

    def with_name(self, name: str, exact: bool = True) -> Self:
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

    def with_data_type(self, data_type: str) -> Self:
        """
        Filter custom fields by data type.

        Args:
            data_type: The data type to filter by (e.g., "string", "integer", "boolean", "date")

        Returns:
            Filtered CustomFieldQuerySet
        """
        return self.filter(data_type=data_type)

    def for_document_type(self, document_type_id: int) -> Self:
        """
        Filter custom fields associated with a specific document type.

        Args:
            document_type_id: The document type ID these fields are associated with

        Returns:
            Filtered CustomFieldQuerySet
        """
        return self.filter(document_type=document_type_id)

    def is_required(self, required: bool = True) -> Self:
        """
        Filter custom fields by required status.

        Args:
            required: If True, get required fields, otherwise optional fields

        Returns:
            Filtered CustomFieldQuerySet
        """
        return self.filter(required=required)
