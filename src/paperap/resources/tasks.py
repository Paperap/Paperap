

from __future__ import annotations

import enum
import logging
import time
from typing import Any, Callable, Generic, TypeVar, cast

from paperap.exceptions import APIError, BadResponseError, ResourceNotFoundError
from paperap.models.task import Task, TaskQuerySet
from paperap.resources.base import BaseResource, StandardResource

logger = logging.getLogger(__name__)


class TaskStatus(enum.Enum):
    """Status of a task."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY = "RETRY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"


T = TypeVar("T")


class TaskResource(StandardResource[Task, TaskQuerySet]):
    """Resource for managing tasks."""

    model_class = Task
    queryset_class = TaskQuerySet

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

    def wait_for_task(
        self,
        task_id: str,
        max_wait: int = 300,
        poll_interval: float = 1.0,
        success_callback: Callable[[Task], None] | None = None,
        failure_callback: Callable[[Task], None] | None = None,
    ) -> Task:
        """
        Wait for a task to complete.

        Args:
            task_id: The task ID to wait for.
            max_wait: Maximum time (in seconds) to wait for completion.
            poll_interval: Seconds between polling attempts.
            success_callback: Optional callback to execute when task succeeds.
            failure_callback: Optional callback to execute when task fails.

        Returns:
            The completed Task instance.

        Raises:
            APIError: If the task fails or times out.
            ResourceNotFoundError: If the task cannot be found.

        """
        logger.debug("Waiting for task %s to complete", task_id)
        end_time = time.monotonic() + max_wait

        while time.monotonic() < end_time:
            try:
                task = self(task_id=task_id).first()
                if task is None:
                    logger.debug("Task %s not found, retrying...", task_id)
                    time.sleep(poll_interval)
                    continue

                # Check if task is complete
                if task.status == TaskStatus.SUCCESS.value:
                    logger.debug("Task %s completed successfully", task_id)
                    if success_callback:
                        success_callback(task)
                    return task

                if task.status == TaskStatus.FAILURE.value:
                    logger.error("Task %s failed: %s", task_id, task.result)
                    if failure_callback:
                        failure_callback(task)
                    raise APIError(f"Task {task_id} failed: {task.result}")

                if task.status == TaskStatus.REVOKED.value:
                    logger.warning("Task %s was revoked", task_id)
                    raise APIError(f"Task {task_id} was revoked")

                logger.debug("Task %s status: %s, waiting...", task_id, task.status)

            except ResourceNotFoundError:
                logger.debug("Task %s not found yet, retrying...", task_id)

            time.sleep(poll_interval)

        raise APIError(f"Timed out waiting for task {task_id} to complete")

    def wait_for_tasks(self, task_ids: list[str], max_wait: int = 300, poll_interval: float = 1.0) -> dict[str, Task]:
        """
        Wait for multiple tasks to complete.

        Args:
            task_ids: List of task IDs to wait for.
            max_wait: Maximum time (in seconds) to wait for all tasks.
            poll_interval: Seconds between polling attempts.

        Returns:
            Dictionary mapping task IDs to completed Task instances.

        Raises:
            APIError: If any task fails or times out.

        """
        logger.debug("Waiting for %d tasks to complete", len(task_ids))
        end_time = time.monotonic() + max_wait
        completed_tasks: dict[str, Task] = {}
        pending_tasks = list(task_ids)

        while pending_tasks and time.monotonic() < end_time:
            for task_id in list(pending_tasks):  # Create a copy to safely modify during iteration
                try:
                    task = self(task_id=task_id).first()
                    if task is None:
                        continue

                    if task.status == TaskStatus.SUCCESS.value:
                        logger.debug("Task %s completed successfully", task_id)
                        completed_tasks[task_id] = task
                        pending_tasks.remove(task_id)

                    elif task.status == TaskStatus.FAILURE.value:
                        logger.error("Task %s failed: %s", task_id, task.result)
                        raise APIError(f"Task {task_id} failed: {task.result}")

                    elif task.status == TaskStatus.REVOKED.value:
                        logger.warning("Task %s was revoked", task_id)
                        raise APIError(f"Task {task_id} was revoked")

                except ResourceNotFoundError:
                    pass  # Task not found yet, continue waiting

            if pending_tasks:
                time.sleep(poll_interval)

        if pending_tasks:
            raise APIError(f"Timed out waiting for tasks: {', '.join(pending_tasks)}")

        return completed_tasks

    def get_task_result(self, task_id: str, wait: bool = True, max_wait: int = 300) -> str | None:
        """
        Get the result of a task.

        Args:
            task_id: The task ID.
            wait: Whether to wait for the task to complete if it's not already.
            max_wait: Maximum time (in seconds) to wait if wait=True.

        Returns:
            The result of the task.

        Raises:
            APIError: If the task fails or times out.
            ResourceNotFoundError: If the task cannot be found.

        """
        task = None
        if wait:
            task = self.wait_for_task(task_id, max_wait=max_wait)
        else:
            task = self(task_id=task_id).first()

        if task is None:
            raise ResourceNotFoundError(f"Task {task_id} not found")

        if task.status != TaskStatus.SUCCESS.value:
            raise APIError(f"Task {task_id} is not successful (status: {task.status})")

        return task.result

    def execute_task(self, method: str, endpoint: str, data: dict[str, Any] | None = None, max_wait: int = 300) -> Task:
        """
        Execute a task synchronously.

        This is a helper method that executes a task and waits for its completion.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            data: Optional data to send with the request
            max_wait: Maximum time to wait for task completion

        Returns:
            The task object, once completed.

        Raises:
            APIError: If the task fails or times out

        """
        response = self.client.request(method, endpoint, data=data)
        if not response or not isinstance(response, str):
            raise BadResponseError("Expected task ID in response")

        task_id = str(response)
        return self.wait_for_task(task_id, max_wait=max_wait)
