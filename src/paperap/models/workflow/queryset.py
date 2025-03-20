"""
----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.workflow.model import Workflow, WorkflowAction, WorkflowTrigger

logger = logging.getLogger(__name__)


class WorkflowQuerySet(StandardQuerySet["Workflow"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    BaseQuerySet provides pagination, filtering, and caching functionality similar to Django's BaseQuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflows by name.

        Args:
            value: The workflow name to filter by
            exact: If True, match the exact name, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowQuerySet

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def order(self, value: int) -> Self:
        """
        Filter workflows by order.

        Args:
            value: The order value to filter by

        Returns:
            Filtered WorkflowQuerySet

        """
        return self.filter(order=value)

    def enabled(self, value: bool = True) -> Self:
        """
        Filter workflows by enabled status.

        Args:
            value: If True, get enabled workflows, otherwise disabled

        Returns:
            Filtered WorkflowQuerySet

        """
        return self.filter(enabled=value)


class WorkflowActionQuerySet(StandardQuerySet["WorkflowAction"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    BaseQuerySet provides pagination, filtering, and caching functionality similar to Django's BaseQuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow actions by type.

        Args:
            value: The action type to filter by
            exact: If True, match the exact type, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter_field_by_str("type", value, exact=exact, case_insensitive=case_insensitive)

    def assign_title(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow actions by assigned title.

        Args:
            value: The title to filter by
            exact: If True, match the exact title, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter_field_by_str("assign_title", value, exact=exact, case_insensitive=case_insensitive)

    def assign_tags(self, value: int | list[int]) -> Self:
        """
        Filter workflow actions by assigned tags.

        Args:
            value: The tag ID or list of tag IDs to filter by

        Returns:
            Filtered WorkflowActionQuerySet

        """
        if isinstance(value, int):
            return self.filter(assign_tags__contains=value)
        return self.filter(assign_tags__overlap=value)

    def assign_correspondent(self, value: int) -> Self:
        """
        Filter workflow actions by assigned correspondent.

        Args:
            value: The correspondent ID to filter by

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter(assign_correspondent=value)

    def assign_document_type(self, value: int) -> Self:
        """
        Filter workflow actions by assigned document type.

        Args:
            value: The document type ID to filter by

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter(assign_document_type=value)

    def assign_storage_path(self, value: int) -> Self:
        """
        Filter workflow actions by assigned storage path.

        Args:
            value: The storage path ID to filter by

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter(assign_storage_path=value)

    def assign_owner(self, value: int) -> Self:
        """
        Filter workflow actions by assigned owner.

        Args:
            value: The owner ID to filter by

        Returns:
            Filtered WorkflowActionQuerySet

        """
        return self.filter(assign_owner=value)


class WorkflowTriggerQuerySet(StandardQuerySet["WorkflowTrigger"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    BaseQuerySet provides pagination, filtering, and caching functionality similar to Django's BaseQuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def type(self, value: int) -> Self:
        """
        Filter workflow triggers by type.

        Args:
            value: The trigger type to filter by

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter(type=value)

    def filter_path(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by path filter.

        Args:
            value: The path filter to match
            exact: If True, match the exact path, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter_field_by_str("filter_path", value, exact=exact, case_insensitive=case_insensitive)

    def filter_filename(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by filename filter.

        Args:
            value: The filename filter to match
            exact: If True, match the exact filename, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter_field_by_str("filter_filename", value, exact=exact, case_insensitive=case_insensitive)

    def filter_mailrule(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by mail rule filter.

        Args:
            value: The mail rule filter to match
            exact: If True, match the exact mail rule, otherwise use contains
            case_insensitive: If True, ignore case when matching

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter_field_by_str("filter_mailrule", value, exact=exact, case_insensitive=case_insensitive)

    def has_tags(self, value: int | list[int]) -> Self:
        """
        Filter workflow triggers by tags filter.

        Args:
            value: The tag ID or list of tag IDs to filter by

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        if isinstance(value, int):
            return self.filter(filter_has_tags__contains=value)
        return self.filter(filter_has_tags__overlap=value)

    def has_correspondent(self, value: int) -> Self:
        """
        Filter workflow triggers by correspondent filter.

        Args:
            value: The correspondent ID to filter by

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter(filter_has_correspondent=value)

    def has_document_type(self, value: int) -> Self:
        """
        Filter workflow triggers by document type filter.

        Args:
            value: The document type ID to filter by

        Returns:
            Filtered WorkflowTriggerQuerySet

        """
        return self.filter(filter_has_document_type=value)
