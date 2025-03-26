"""
Provide query functionality for document types in Paperless-ngx.

This module contains the DocumentTypeQuerySet class which extends the standard
queryset functionality with document type specific filtering methods. These
methods allow for filtering document types by their attributes such as name,
slug, match pattern, and other properties.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet, BulkQuerySet
from paperap.models.mixins.queryset import HasDocumentCount, HasOwner

if TYPE_CHECKING:
    from paperap.models.document_type.model import DocumentType

logger = logging.getLogger(__name__)


class DocumentTypeQuerySet(BulkQuerySet["DocumentType"], HasOwner, HasDocumentCount):
    """
    Implement specialized filtering methods for Paperless-ngx document types.

    Extends StandardQuerySet to provide document type-specific filtering
    capabilities, including filtering by name, slug, match pattern, and other
    document type attributes.

    Inherits:
        StandardQuerySet: Base queryset functionality for standard models
        HasOwner: Adds owner filtering capabilities
        HasDocumentCount: Adds document count filtering capabilities

    Returns:
        Self: A chainable DocumentTypeQuerySet instance

    Examples:
        Get all document types:
            >>> all_types = client.document_types.all()

        Filter by name:
            >>> invoices = client.document_types.filter(name__contains="invoice")

        Chain multiple filters:
            >>> results = client.document_types.name("Tax").matching_algorithm(1)

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by name.

        Args:
            value: The document type name to filter by
            exact: If True, match the exact name, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching.
                Defaults to True.

        Returns:
            Filtered DocumentTypeQuerySet with name filter applied

        Examples:
            Exact match (default):
                >>> invoice_types = client.document_types.name("Invoice")

            Contains match:
                >>> tax_types = client.document_types.name("tax", exact=False)

            Case sensitive match:
                >>> types = client.document_types.name("TAX", case_insensitive=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by slug.

        The slug is a URL-friendly version of the document type name, typically
        lowercase with hyphens instead of spaces.

        Args:
            value: The slug to filter by
            exact: If True, match the exact slug, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching.
                Defaults to True.

        Returns:
            Filtered DocumentTypeQuerySet with slug filter applied

        Examples:
            Exact match:
                >>> invoice_types = client.document_types.slug("invoice-2023")

            Contains match:
                >>> types = client.document_types.slug("invoice", exact=False)

        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)

    def match(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter document types by match pattern.

        The match pattern is used by Paperless-ngx to automatically assign document types
        to documents based on their content or filename.

        Args:
            value: The pattern to search for in match
            exact: If True, match the exact pattern, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching.
                Defaults to True.

        Returns:
            Filtered DocumentTypeQuerySet with match pattern filter applied

        Examples:
            Find document types that match "invoice":
                >>> invoice_types = client.document_types.match("invoice")

            Find document types with match patterns containing "tax":
                >>> tax_types = client.document_types.match("tax", exact=False)

        """
        return self.filter_field_by_str("match", value, exact=exact, case_insensitive=case_insensitive)

    def matching_algorithm(self, value: int) -> Self:
        """
        Filter document types by matching algorithm.

        Paperless-ngx supports different algorithms for matching document types:
        - 1: Any word (default)
        - 2: All words
        - 3: Exact match
        - 4: Regular expression
        - 5: Fuzzy match
        - 6: Auto

        Args:
            value: The matching algorithm ID (1-6)

        Returns:
            Filtered DocumentTypeQuerySet with matching algorithm filter applied

        Examples:
            Find document types using regex matching:
                >>> regex_types = client.document_types.matching_algorithm(4)

            Find document types using fuzzy matching:
                >>> fuzzy_types = client.document_types.matching_algorithm(5)

        """
        return self.filter(matching_algorithm=value)

    def case_insensitive(self, value: bool = True) -> Self:
        """
        Filter document types by case sensitivity setting.

        Filter document types based on whether their matching is case insensitive
        or case sensitive.

        Args:
            value: If True, get document types with case insensitive matching.
                If False, get document types with case sensitive matching. Defaults to True.

        Returns:
            Filtered DocumentTypeQuerySet with case sensitivity filter applied

        Examples:
            Find document types with case insensitive matching:
                >>> insensitive_types = client.document_types.case_insensitive()

            Find document types with case sensitive matching:
                >>> sensitive_types = client.document_types.case_insensitive(False)

        """
        return self.filter(is_insensitive=value)

    def user_can_change(self, value: bool = True) -> Self:
        """
        Filter document types by user change permission.

        Filter document types based on whether regular users (non-superusers)
        have permission to modify them.

        Args:
            value: If True, get document types where users can change.
                If False, get document types where only superusers can change.
                Defaults to True.

        Returns:
            Filtered DocumentTypeQuerySet with user permission filter applied

        Examples:
            Find document types that regular users can modify:
                >>> user_editable = client.document_types.user_can_change()

            Find document types that only superusers can modify:
                >>> admin_only = client.document_types.user_can_change(False)

        """
        return self.filter(user_can_change=value)
