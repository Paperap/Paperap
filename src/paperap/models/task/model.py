"""
Task model module for interacting with Paperless-NgX tasks.

This module provides the Task model class for representing and interacting
with background tasks in the Paperless-NgX system.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paperap.const import TaskNameType, TaskStatusType, TaskTypeType
from paperap.models.abstract.model import StandardModel
from paperap.models.task.queryset import TaskQuerySet


class Task(StandardModel):
    """
    Represents a background task in Paperless-NgX.

    Tasks are used for tracking long-running operations in Paperless-NgX,
    such as document processing, OCR, classification, and bulk operations.
    This model provides access to task status, progress, and results.

    Attributes:
        task_id: Unique identifier for the task in the task queue system.
        task_file_name: Name of the file being processed, if applicable.
        task_name: Human-readable name of the task type.
        date_created: When the task was created.
        date_started: When the task started execution.
        date_done: When the task completed (successfully or with error).
        type: The type of task being performed.
        status: Current status of the task (pending, running, success, failure).
        result: Result data from the task, often a JSON string.
        acknowledged: Whether the task has been acknowledged by a user.
        related_document: ID of the document related to this task, if any.

    Examples:
        >>> # Get a specific task
        >>> task = client.tasks.get(5)
        >>> print(f"Task status: {task.status}")
        >>>
        >>> # Wait for a task to complete
        >>> document = client.tasks.wait_for_task(task.task_id)
        >>> print(f"Document {document.id} ready")

    """

    task_id: str
    task_file_name: str | None = None
    task_name: TaskNameType | None = None
    date_created: datetime | None = None
    date_started: datetime | None = None
    date_done: datetime | None = None
    type: TaskTypeType | None = None
    status: TaskStatusType | None = None
    result: str | None = None
    acknowledged: bool
    related_document: int | None = None

    class Meta(StandardModel.Meta):
        """
        Metadata for the Task model.

        Defines the queryset class to use for task queries.
        """

        queryset = TaskQuerySet
