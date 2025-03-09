"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
       Project: paperap
       Created: 2025-03-05
       Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-05     By Jess Mann

"""

from __future__ import annotations
from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from paperap.models.abstract.queryset import QuerySet, StandardQuerySet


class QuerySetProtocol(Protocol):
    def all(self) -> Self: ...
    def filter(self, **kwargs) -> Self: ...
    def filter_field_by_str(
        self, field: str, value: str, *, exact: bool = True, case_insensitive: bool = True
    ) -> Self: ...


class HasDocumentCount(QuerySetProtocol):
    """
    Mixin for querysets that have a document_count field.
    """

    def document_count(self, count: int) -> Self:
        """
        Filter models by document count.

        Args:
            count: The document count to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(document_count=count)

    def document_count_over(self, count: int) -> Self:
        """
        Filter models by document count greater than a value.

        Args:
            count: The document count to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(document_count__gt=count)

    def document_count_under(self, count: int) -> Self:
        """
        Filter models by document count less than a value.

        Args:
            count: The document count to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(document_count__lt=count)

    def document_count_between(self, lower: int, upper: int) -> Self:
        """
        Filter models by document count between two values.

        Args:
            lower: The lower document count to filter by
            upper: The upper document count to filter by

        Returns:
            Filtered QuerySet
        """
        return self.filter(document_count__range=(lower, upper))


class HasOwner(QuerySetProtocol):
    """
    Mixin for querysets that have an owner field.
    """

    def owner(self, owner: int | list[int] | None) -> Self:
        """
        Filter models by owner.

        Args:
            owner: The owner to filter by

        Returns:
            Filtered QuerySet
        """
        if isinstance(owner, list):
            return self.filter(owner__in=owner)
        return self.filter(owner=owner)


class HasStandard(HasOwner, HasDocumentCount):
    """
    Mixin for querysets that have standard fields: owner, document_count, name, slug
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter models where name is value

        Args:
            value (str): The value to compare against
            exact (bool): Whether the comparison should be exact
            case_sensitive (bool): Whether the comparison should be case insensitive

        Returns:
            Filtered QuerySet
        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def slug(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter models where slug is value

        Args:
            value (str): The value to compare against
            exact (bool): Whether the comparison should be exact
            case_sensitive (bool): Whether the comparison should be case insensitive

        Returns:
            Filtered QuerySet
        """
        return self.filter_field_by_str("slug", value, exact=exact, case_insensitive=case_insensitive)
