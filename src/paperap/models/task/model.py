"""
----------------------------------------------------------------------------

   METADATA:

       File:    task.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paperap.const import TaskNameType, TaskStatusType, TaskTypeType
from paperap.models.abstract.model import StandardModel
from paperap.models.task.queryset import TaskQuerySet


class Task(StandardModel):
    """
    Represents a task in Paperless-NgX.
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
        queryset = TaskQuerySet
