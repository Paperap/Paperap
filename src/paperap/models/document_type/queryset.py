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
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet
from paperap.models.mixins.queryset import HasOwner, HasDocumentCount

if TYPE_CHECKING:
    from paperap.models.document_type.model import DocumentType

logger = logging.getLogger(__name__)


class DocumentTypeQuerySet(StandardQuerySet["DocumentType"], HasOwner, HasDocumentCount):
    """
    QuerySet for Paperless-ngx document types with specialized filtering methods.

    Returns:
        A new instance of DocumentTypeQuerySet.

    Examples:
        # Create a DocumentTypeQuerySet instance
        queryset = DocumentTypeQuerySet()
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by user change permission.

        Args:
            value: If True, get document types where users can change.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by user change permission
            filtered = queryset.user_can_change(True)
        Filter document types by case sensitivity setting.

        Args:
            value: If True, get document types with case insensitive matching.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by case sensitivity
            filtered = queryset.case_insensitive(True)
        Filter document types by matching algorithm.

        Args:
            value: The matching algorithm ID.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by matching algorithm
            filtered = queryset.matching_algorithm(1)
        Filter document types by match pattern.

        Args:
            value: The pattern to search for in match.
            exact: If True, match the exact pattern, otherwise use contains.
            case_insensitive: If True, perform a case insensitive match.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by match pattern
            filtered = queryset.match("INV-*")
        Filter document types by slug.

        Args:
            value: The slug to filter by.
            exact: If True, match the exact slug, otherwise use contains.
            case_insensitive: If True, perform a case insensitive match.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by slug
            filtered = queryset.slug("invoice")
        Filter document types by name.

        Args:
            value: The document type name to filter by.
            exact: If True, match the exact name, otherwise use contains.
            case_insensitive: If True, perform a case insensitive match.

        Returns:
            Filtered DocumentTypeQuerySet.

        Examples:
            # Filter document types by name
            filtered = queryset.name("Invoice")
        Filter document types by name.

        Args:
            value: The document type name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by slug.

        Args:
            value: The slug to filter by
            exact: If True, match the exact slug, otherwise use contains

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)

    def match(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by match pattern.

        Args:
            value: The pattern to search for in match
            exact: If True, match the exact pattern, otherwise use contains

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter_field_by_str("match", value, exact=exact, case_insensitive=case_insensitive)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter document types by matching algorithm.

        Args:
            value: The matching algorithm ID

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter(matching_algorithm=value)

    def case_insensitive(self, value: bool = True) -> Self:
        """
        Filter document types by case sensitivity setting.

        Args:
            insensitive: If True, get document types with case insensitive matching

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter(is_insensitive=value)

    def user_can_change(self, value: bool = True) -> Self:
        """
        Filter document types by user change permission.

        Args:
            value: If True, get document types where users can change

        Returns:
            Filtered DocumentTypeQuerySet
        """
        return self.filter(user_can_change=value)
