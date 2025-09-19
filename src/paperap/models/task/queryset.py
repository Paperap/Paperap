"""
Provide query interface for Paperless-NGX tasks.

This module implements the TaskQuerySet class, which extends StandardQuerySet
to provide specialized filtering methods for Paperless-NGX tasks. It enables
efficient querying of the task API endpoint with task-specific filters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.task.model import Task

logger = logging.getLogger(__name__)


class TaskQuerySet(StandardQuerySet["Task"]):
    """
    Provide a lazy-loaded, chainable query interface for Paperless-NGX tasks.

    Extends StandardQuerySet to provide specialized filtering methods for task-specific
    attributes like task_id, status, and result. Enables efficient querying of the
    Paperless-NGX task API endpoint.

    The queryset is lazy-loaded, meaning API requests are only made when data
    is actually needed (when iterating, slicing, or calling terminal methods
    like count() or get()).

    Examples:
        Get all tasks:
            >>> all_tasks = client.tasks.all()

        Get a specific task by ID:
            >>> task = client.tasks.get(123)

        Filter tasks by status:
            >>> pending = client.tasks.all().status("PENDING")

        Chain filters:
            >>> document_tasks = client.tasks.all().type("document").status("SUCCESS")

    """

    def task_id(self, value: int) -> Self:
        """
        Filter tasks by task_id.

        Args:
            value: The task_id to filter by.

        Returns:
            A filtered queryset containing only tasks with the specified task_id.

        Examples:
            Get task with specific task_id:
                >>> task = client.tasks.all().task_id(12345).first()

        """
        return self.filter(task_id=value)

    def task_file_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by task_file_name.

        Args:
            value: The task_file_name to filter by.
            exact: If True, match the exact task_file_name, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered queryset containing only tasks with the matching task_file_name.

        Examples:
            Exact match, case insensitive (default):
                >>> pdf_tasks = client.tasks.all().task_file_name("document.pdf")

            Contains match, case sensitive:
                >>> pdf_tasks = client.tasks.all().task_file_name("pdf", exact=False, case_insensitive=False)

        """
        return self.filter_field_by_str("task_file_name", value, exact=exact, case_insensitive=case_insensitive)

    def date_done(self, value: str | None) -> Self:
        """
        Filter tasks by completion date.

        Args:
            value: The date_done to filter by, in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ).
                Pass None to find tasks that haven't completed.

        Returns:
            A filtered queryset containing only tasks with the matching completion date.

        Examples:
            Tasks completed on a specific date:
                >>> completed = client.tasks.all().date_done("2023-04-15T00:00:00Z")

            Tasks that haven't completed yet:
                >>> pending = client.tasks.all().date_done(None)

        """
        return self.filter(date_done=value)

    def type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by type.

        Task types typically include 'document', 'mail', 'consumption', etc.

        Args:
            value: The task type to filter by.
            exact: If True, match the exact type, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered queryset containing only tasks with the matching type.

        Examples:
            Get all document processing tasks:
                >>> doc_tasks = client.tasks.all().type("document")

            Get all mail-related tasks (contains match):
                >>> mail_tasks = client.tasks.all().type("mail", exact=False)

        """
        return self.filter_field_by_str("type", value, exact=exact, case_insensitive=case_insensitive)

    def status(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by status.

        Common status values include 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', etc.

        Args:
            value: The status to filter by.
            exact: If True, match the exact status, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered queryset containing only tasks with the matching status.

        Examples:
            Get all successful tasks:
                >>> successful = client.tasks.all().status("SUCCESS")

            Get all failed tasks:
                >>> failed = client.tasks.all().status("FAILURE")

            Get all in-progress tasks:
                >>> in_progress = client.tasks.all().status("STARTED")

        """
        return self.filter_field_by_str("status", value, exact=exact, case_insensitive=case_insensitive)

    def result(self, value: str | None, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter tasks by result.

        The result field typically contains the output of the task, which may be
        a document ID, error message, or other task-specific data.

        Args:
            value: The result to filter by. Pass None to find tasks with no result.
            exact: If True, match the exact result, otherwise use contains.
                Defaults to True.
            case_insensitive: If True, ignore case when matching. Defaults to True.

        Returns:
            A filtered queryset containing only tasks with the matching result.

        Examples:
            Find tasks with a specific document ID in the result:
                >>> doc_tasks = client.tasks.all().result("42")

            Find tasks with no result yet:
                >>> no_result = client.tasks.all().result(None)

            Find tasks with error messages:
                >>> error_tasks = client.tasks.all().result("error", exact=False)

        """
        if value is None:
            return self.filter(result__isnull=True)
        return self.filter_field_by_str("result", value, exact=exact, case_insensitive=case_insensitive)

    def acknowledged(self, value: bool) -> Self:
        """
        Filter tasks by acknowledged status.

        Acknowledged tasks are those that have been marked as seen/reviewed by a user.
        This is particularly useful for filtering out tasks that need attention.

        Args:
            value: True to get only acknowledged tasks, False to get only unacknowledged tasks.

        Returns:
            A filtered queryset containing only tasks with the matching acknowledged status.

        Examples:
            Get all unacknowledged tasks that need attention:
                >>> needs_attention = client.tasks.all().acknowledged(False)

            Get all acknowledged tasks:
                >>> reviewed = client.tasks.all().acknowledged(True)

        """
        return self.filter(acknowledged=value)

    def related_document(self, value: int | list[int]) -> Self:
        """
        Filter tasks by related document ID.

        Many tasks in Paperless-NGX are associated with specific documents.
        This method allows filtering tasks by their related document ID(s).

        Args:
            value: Either a single document ID or a list of document IDs to filter by.

        Returns:
            A filtered queryset containing only tasks related to the specified document(s).

        Examples:
            Get all tasks related to document #42:
                >>> doc_tasks = client.tasks.all().related_document(42)

            Get all tasks related to a set of documents:
                >>> batch_tasks = client.tasks.all().related_document([42, 43, 44])

        """
        if isinstance(value, int):
            return self.filter(related_document=value)
        return self.filter(related_document__in=value)
