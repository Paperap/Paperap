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

from typing import Any, Self, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.document_type.model import DocumentType

logger = logging.getLogger(__name__)


class DocumentTypeQuerySet(QuerySet["DocumentType"]):
    """
    QuerySet for Paperless-ngx document types with specialized filtering methods.
    """

    def with_name(self, name: str, *, exact: bool = True) -> Self:
        """
        Filter document types by name.

        Args:
            name: The document type name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentTypeQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def with_ids(self, ids: list[int]) -> Self:
        """
        Filter document types by multiple IDs.

        Args:
            ids: list of document type IDs to filter by

        Returns:
            Filtered DocumentTypeQuerySet
        """
        ids_param = ",".join(str(id) for id in ids)
        return self.filter(id__in=ids_param)

    def with_matching_rule(self, rule_pattern: str) -> Self:
        """
        Filter document types by their matching rule pattern.

        Args:
            rule_pattern: The pattern to search for in matching rules

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter(matching_algorithm__contains=rule_pattern)

    def is_insensitive(self, insensitive: bool = True) -> Self:
        """
        Filter document types by case sensitivity setting.

        Args:
            insensitive: If True, get document types with case insensitive matching

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter(is_insensitive=insensitive)
