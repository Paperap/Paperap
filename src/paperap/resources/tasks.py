"""
Resources for managing Paperless-NgX tasks.

This module provides classes and methods to interact with the Paperless-NgX task system.
It enables tracking, acknowledging, and waiting for asynchronous operations to complete.
Tasks are used for long-running operations like document uploads, OCR processing, and
bulk operations.

Classes:
    TaskStatus: Enum representing possible states of a task.
    TaskResource: Resource for interacting with the tasks API endpoint.

Example:
    >>> # Wait for a document upload task to complete
    >>> task_id = client.documents.upload_async("document.pdf")
    >>> task = client.tasks.wait_for_task(task_id)
    >>> print(f"Document {task.related_document} uploaded successfully")

"""

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
    """
    Enum representing the possible states of a Paperless-NgX task.

    These values match the Celery task states used by Paperless-NgX's backend.

    Attributes:
        PENDING: Task is queued but not yet started.
        STARTED: Task is currently executing.
        RETRY: Task failed but is scheduled for retry.
        SUCCESS: Task completed successfully.
        FAILURE: Task failed and will not be retried.
        REVOKED: Task was cancelled before completion.

    """

    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY = "RETRY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"


T = TypeVar("T")


class TaskResource(StandardResource[Task, TaskQuerySet]):
    """
    Resource for interacting with Paperless-NgX tasks.

    This class provides methods to track, acknowledge, and wait for asynchronous
    operations to complete. It extends the StandardResource class with task-specific
    functionality like polling for completion and retrieving results.

    Tasks in Paperless-NgX represent background operations like document processing,
    OCR, classification, and bulk operations.

    Attributes:
        model_class: The Task model class.
        queryset_class: The TaskQuerySet class for querying tasks.

    Example:
        >>> # Get all pending tasks
        >>> pending_tasks = client.tasks().filter(status="PENDING")
        >>> for task in pending_tasks:
        >>>     print(f"Task {task.id}: {task.task_name}")

    """

    model_class = Task
    queryset_class = TaskQuerySet

    def acknowledge(self, task_id: int) -> None:
        """
        Acknowledge a task to remove it from the task list.

        This method marks a task as acknowledged in the Paperless-NgX system,
        which removes it from the pending tasks list in the UI. This is useful
        for cleaning up the task list after processing completed tasks.

        Args:
            task_id: ID of the task to acknowledge.

        Example:
            >>> # Acknowledge a completed task
            >>> client.tasks.acknowledge(123)

        """
        self.client.request("PUT", f"tasks/{task_id}/acknowledge/")

    def bulk_acknowledge(self, task_ids: list[int]) -> None:
        """
        Acknowledge multiple tasks at once.

        This method efficiently acknowledges multiple tasks in a single API call,
        removing them from the pending tasks list in the Paperless-NgX UI.

        Args:
            task_ids: List of task IDs to acknowledge.

        Example:
            >>> # Acknowledge all completed upload tasks
            >>> completed_tasks = client.tasks().filter(status="SUCCESS")
            >>> task_ids = [task.id for task in completed_tasks]
            >>> client.tasks.bulk_acknowledge(task_ids)

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
        Wait for a task to complete and return the result.

        This method polls the Paperless-NgX API at regular intervals to check the status
        of a task until it completes successfully, fails, or the maximum wait time is reached.
        Optional callbacks can be executed on success or failure.

        Args:
            task_id: The task ID to wait for.
            max_wait: Maximum time in seconds to wait for completion (default: 300).
            poll_interval: Seconds between polling attempts (default: 1.0).
            success_callback: Optional function to call when task succeeds.
            failure_callback: Optional function to call when task fails.

        Returns:
            The completed Task instance.

        Raises:
            APIError: If the task fails, is revoked, or times out.
            ResourceNotFoundError: If the task cannot be found.

        Example:
            >>> # Upload a document asynchronously and wait for completion
            >>> task_id = client.documents.upload_async("large_document.pdf")
            >>>
            >>> # Define callbacks
            >>> def on_success(task):
            >>>     print(f"Document {task.related_document} uploaded successfully")
            >>>
            >>> def on_failure(task):
            >>>     print(f"Upload failed: {task.result}")
            >>>
            >>> # Wait with callbacks
            >>> task = client.tasks.wait_for_task(
            >>>     task_id,
            >>>     success_callback=on_success,
            >>>     failure_callback=on_failure
            >>> )

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
        Wait for multiple tasks to complete and return their results.

        This method efficiently polls the Paperless-NgX API to check the status of
        multiple tasks until they all complete successfully or the maximum wait time
        is reached. If any task fails, an exception is raised immediately.

        Args:
            task_ids: List of task IDs to wait for.
            max_wait: Maximum time in seconds to wait for all tasks (default: 300).
            poll_interval: Seconds between polling attempts (default: 1.0).

        Returns:
            Dictionary mapping task IDs to completed Task instances.

        Raises:
            APIError: If any task fails, is revoked, or if the wait times out.

        Example:
            >>> # Upload multiple documents asynchronously
            >>> task_ids = []
            >>> for file_path in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
            >>>     task_id = client.documents.upload_async(file_path)
            >>>     task_ids.append(task_id)
            >>>
            >>> # Wait for all uploads to complete
            >>> completed_tasks = client.tasks.wait_for_tasks(task_ids)
            >>>
            >>> # Process the results
            >>> for task_id, task in completed_tasks.items():
            >>>     print(f"Task {task_id} completed: {task.status_str}")

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
        Get the result data of a completed task.

        This method retrieves the result string of a task, optionally waiting for
        its completion if it is not already finished. The result format depends on
        the specific task type.

        Args:
            task_id: The task ID to get results for.
            wait: Whether to wait for the task to complete if not already done (default: True).
            max_wait: Maximum time in seconds to wait if wait=True (default: 300).

        Returns:
            The result string of the task, or None if no result is available.

        Raises:
            APIError: If the task fails, is not successful, or times out.
            ResourceNotFoundError: If the task cannot be found.

        Example:
            >>> # Get result of a document processing task
            >>> task_id = client.documents.upload_async("document.pdf")
            >>> result = client.tasks.get_task_result(task_id)
            >>> print(f"Task result: {result}")

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
        Execute a task and wait for its completion.

        This helper method executes an asynchronous operation by sending a request to
        the specified API endpoint and then waits for the resulting task to complete.
        It combines the request and wait_for_task operations into a single method.

        Args:
            method: HTTP method to use (GET, POST, PUT, etc.).
            endpoint: API endpoint to call (without the base URL).
            data: Optional data to send with the request (default: None).
            max_wait: Maximum time in seconds to wait for completion (default: 300).

        Returns:
            The completed Task instance.

        Raises:
            APIError: If the task fails or times out.
            BadResponseError: If the response doesn't contain a valid task ID.

        Example:
            >>> # Execute a bulk tagging operation
            >>> task = client.tasks.execute_task(
            >>>     "POST",
            >>>     "documents/bulk_edit/",
            >>>     data={
            >>>         "documents": [1, 2, 3],
            >>>         "method": "add_tag",
            >>>         "parameters": {"tag": 5}
            >>>     }
            >>> )
            >>> print(f"Bulk operation completed: {task.status_str}")

        """
        response = self.client.request(method, endpoint, data=data)
        if not response or not isinstance(response, str):
            raise BadResponseError("Expected task ID in response")

        task_id = str(response)
        return self.wait_for_task(task_id, max_wait=max_wait)
