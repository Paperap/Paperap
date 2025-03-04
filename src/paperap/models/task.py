"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    task.py                                                                                              *
*        Project: models                                                                                               *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class Task(PaperlessModel):
    """
    Represents a task in Paperless-NgX.
    """

    task_id: str
    task_file_name: str
    date_done: str | None = Field(default=None)  # ISO format date
    status: str
    result: str | None = Field(default=None)
    acknowledged: bool = Field(default=False)
    related_document: int | None = Field(default=None)
    type: str | None = Field(default=None)
