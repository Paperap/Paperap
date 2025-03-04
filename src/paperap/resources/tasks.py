"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    tasks.py                                                                                             *
*        Project: resources                                                                                            *
*        Created: 2025-03-03                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-03     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from typing import Any, Dict, List, Optional

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
