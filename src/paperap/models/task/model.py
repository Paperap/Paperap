"""




----------------------------------------------------------------------------

   METADATA:

       File:    task.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.task.queryset import TaskQuerySet


class Task(StandardModel):
    """
    Represents a task in Paperless-NgX.
    """

    task_id: str
    task_file_name: str | None = None
    date_done: str | None = None  # ISO format date
    type: str | None = None
    status: str | None = None
    result: str | None = None
    acknowledged: bool
    related_document: int | None = None

    class Meta(StandardModel.Meta):
        queryset = TaskQuerySet
