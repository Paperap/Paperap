"""
Provide queryset mixin classes for extending queryset functionality.

This module contains Protocol classes that define interfaces and mixins that
implement common filtering patterns for different types of querysets. These
mixins can be combined with concrete queryset classes to add specialized
filtering methods for different resource types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Self

if TYPE_CHECKING:
    from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet


class QuerySetProtocol(Protocol):
    """
    Define the basic interface for querysets.

    This protocol establishes the minimum interface that all queryset mixins
    can depend on. It's used primarily for type hinting and to ensure
    consistent behavior across different queryset implementations.

    All queryset classes should implement these methods to be compatible
    with the mixin classes in this module.
    """

    def all(self) -> Self:
        """
        Return a new queryset with all objects.

        Returns:
            Self: A new queryset containing all objects.

        """
        ...

    def filter(self, **kwargs: Any) -> Self:
        """
        Filter the queryset by the given keyword arguments.

        Args:
            **kwargs: Field lookups to filter by.

        Returns:
            Self: A new filtered queryset.

        Example:
            >>> queryset.filter(name="example", created__gt="2023-01-01")

        """
        ...

    def filter_field_by_str(self, field: str, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter the queryset by comparing a field to a string value.

        Args:
            field: The name of the field to filter on.
            value: The string value to compare against.
            exact: Whether to perform an exact match (True) or a contains match (False).
            case_insensitive: Whether to perform case-insensitive comparison.

        Returns:
            Self: A new filtered queryset.

        Example:
            >>> queryset.filter_field_by_str("name", "invoice", exact=False)

        """
        ...


class HasDocumentCount(QuerySetProtocol, Protocol):
    """
    Provide filtering methods for querysets with a document_count field.

    This mixin provides convenience methods for filtering models based on their
    document count. It's intended for resources like tags, correspondents, and
    document types that have an associated count of documents.

    Examples:
        >>> # Find tags with exactly 5 documents
        >>> client.tags().document_count(5)
        >>>
        >>> # Find document types with more than 10 documents
        >>> client.document_types().document_count_over(10)
        >>>
        >>> # Find correspondents with between 5 and 20 documents
        >>> client.correspondents().document_count_between(5, 20)

    """

    def document_count(self, count: int) -> Self:
        """
        Filter models by exact document count.

        Args:
            count: The exact document count to filter by.

        Returns:
            Self: A new filtered queryset containing only models with exactly
                the specified document count.

        Example:
            >>> client.tags().document_count(5)  # Tags with exactly 5 documents

        """
        return self.filter(document_count=count)

    def document_count_over(self, count: int) -> Self:
        """
        Filter models by document count greater than a value.

        Args:
            count: The minimum document count (exclusive).

        Returns:
            Self: A new filtered queryset containing only models with more
                documents than the specified count.

        Example:
            >>> client.tags().document_count_over(10)  # Tags with more than 10 documents

        """
        return self.filter(document_count__gt=count)

    def document_count_under(self, count: int) -> Self:
        """
        Filter models by document count less than a value.

        Args:
            count: The maximum document count (exclusive).

        Returns:
            Self: A new filtered queryset containing only models with fewer
                documents than the specified count.

        Example:
            >>> client.tags().document_count_under(3)  # Tags with fewer than 3 documents

        """
        return self.filter(document_count__lt=count)

    def document_count_between(self, lower: int, upper: int) -> Self:
        """
        Filter models by document count between two values (inclusive).

        Args:
            lower: The lower document count bound (inclusive).
            upper: The upper document count bound (inclusive).

        Returns:
            Self: A new filtered queryset containing only models with document
                count within the specified range.

        Example:
            >>> client.tags().document_count_between(5, 20)  # Tags with 5 to 20 documents

        """
        return self.filter(document_count__range=(lower, upper))


class HasOwner(QuerySetProtocol, Protocol):
    """
    Provide filtering methods for querysets with an owner field.

    This mixin provides convenience methods for filtering models based on their
    owner. It's intended for resources like documents, saved views, and other
    user-owned resources in Paperless-NgX.

    Examples:
        >>> # Find documents owned by user with ID 1
        >>> client.documents().owner(1)
        >>>
        >>> # Find documents owned by any of several users
        >>> client.documents().owner([1, 2, 3])
        >>>
        >>> # Find documents with no owner
        >>> client.documents().owner(None)

    """

    def owner(self, owner: int | list[int] | None) -> Self:
        """
        Filter models by owner.

        Args:
            owner: The owner ID, list of owner IDs, or None to filter for
                unowned items. When a list is provided, models owned by any
                of the specified owners will be included.

        Returns:
            Self: A new filtered queryset containing only models with the
                specified owner(s).

        Examples:
            >>> client.documents().owner(1)  # Documents owned by user 1
            >>> client.documents().owner([1, 2, 3])  # Documents owned by users 1, 2, or 3
            >>> client.documents().owner(None)  # Documents with no owner

        """
        if isinstance(owner, list):
            return self.filter(owner__in=owner)
        return self.filter(owner=owner)


class HasStandard(HasOwner, HasDocumentCount, Protocol):
    """
    Combine standard filtering methods for common Paperless-NgX resources.

    This mixin combines the HasOwner and HasDocumentCount mixins and adds
    additional filtering methods for the name and slug fields. It's intended
    for resources like tags, correspondents, and document types that have
    these standard fields.

    The standard fields are:
        - owner: The user who owns the resource
        - document_count: The number of documents associated with the resource
        - name: The display name of the resource
        - slug: The URL-friendly identifier for the resource

    Examples:
        >>> # Find tags with a specific name
        >>> client.tags().name("Invoices")
        >>>
        >>> # Find document types with names containing "tax" (case insensitive)
        >>> client.document_types().name("tax", exact=False)
        >>>
        >>> # Find correspondents with a specific slug
        >>> client.correspondents().slug("acme-corp")

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter models by name field.

        Args:
            value: The name value to filter by.
            exact: If True, performs exact matching. If False, performs contains matching.
            case_insensitive: If True, performs case-insensitive comparison.

        Returns:
            Self: A new filtered queryset containing only models with matching names.

        Examples:
            >>> client.tags().name("Invoices")  # Tags named exactly "Invoices"
            >>> client.tags().name("tax", exact=False)  # Tags with "tax" in their name
            >>> client.tags().name("TAX", case_insensitive=True)  # Case-insensitive match

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter models by slug field.

        Args:
            value: The slug value to filter by.
            exact: If True, performs exact matching. If False, performs contains matching.
            case_insensitive: If True, performs case-insensitive comparison.

        Returns:
            Self: A new filtered queryset containing only models with matching slugs.

        Examples:
            >>> client.tags().slug("invoices")  # Tags with slug exactly "invoices"
            >>> client.tags().slug("tax", exact=False)  # Tags with "tax" in their slug

        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)
