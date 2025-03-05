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

from typing import Any, TYPE_CHECKING, Self
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.task.model import Task

logger = logging.getLogger(__name__)


class TaskQuerySet(StandardQuerySet["Task"]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """

    def task_id(self, value: int) -> Self:
        """
        Filter tasks by task_id.

        Args:
            value (int): The task_id to filter by

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter(task_id=value)

    def task_file_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by task_file_name.

        Args:
            value (str): The task_file_name to filter by
            exact (bool): If True, match the exact task_file_name, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter_field_by_str("task_file_name", value, exact=exact, case_insensitive=case_insensitive)

    def date_done(self, value: str | None) -> Self:
        """
        Filter tasks by date_done.

        Args:
            value (str | None): The date_done to filter by

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter(date_done=value)

    def type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by type.

        Args:
            value (str): The type to filter by
            exact (bool): If True, match the exact type, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter_field_by_str("type", value, exact=exact, case_insensitive=case_insensitive)

    def status(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by status.

        Args:
            value (str): The status to filter by
            exact (bool): If True, match the exact status, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter_field_by_str("status", value, exact=exact, case_insensitive=case_insensitive)

    def result(self, value: str | None, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by result.

        Args:
            value (str | None): The result to filter by
            exact (bool): If True, match the exact result, otherwise use contains
            case_insensitive (bool): If True, ignore case when matching

        Returns:
            TaskQuerySet: The filtered queryset
        """
        if value is None:
            return self.filter(result__isnull=True)
        return self.filter_field_by_str("result", value, exact=exact, case_insensitive=case_insensitive)

    def acknowledged(self, value: bool) -> Self:
        """
        Filter tasks by acknowledged.

        Args:
            value (bool): The acknowledged to filter by

        Returns:
            TaskQuerySet: The filtered queryset
        """
        return self.filter(acknowledged=value)

    def related_document(self, value: int | list[int]) -> Self:
        """
        Filter tasks by related_document.

        Args:
            value (int | list[int]): The related_document to filter by

        Returns:
            TaskQuerySet: The filtered queryset
        """
        if isinstance(value, int):
            return self.filter(related_document=value)
        return self.filter(related_document__in=value)
