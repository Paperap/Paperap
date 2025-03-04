
from __future__ import annotations

from typing import Any, Optional

from paperap.models.task import Task
from paperap.resources.base import PaperlessResource


class TaskResource(PaperlessResource[Task]):
    """Resource for managing tasks."""

    model_class = Task

    def acknowledge(self, task_id: int) -> None:
        """
        Acknowledge a task.

        Args:
            task_id: ID of the task to acknowledge.
        """
        self.client.request("PUT", f"tasks/{task_id}/acknowledge/")

    def bulk_acknowledge(self, task_ids: list[int]) -> None:
        """
        Acknowledge multiple tasks.

        Args:
            task_ids: list of task IDs to acknowledge.
        """
        self.client.request("POST", "tasks/bulk_acknowledge/", data={"tasks": task_ids})
