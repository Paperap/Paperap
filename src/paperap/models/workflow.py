"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    workflow.py                                                                                          *
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

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class WorkflowTrigger(PaperlessModel):
    """
    Represents a workflow trigger in Paperless-NgX.
    """

    name: str
    type: str
    matching_algorithm: int
    is_insensitive: bool
    filter_path: str | None = None
    filter_filename: str | None = None
    document_matches: str | None = None


class WorkflowAction(PaperlessModel):
    """
    Represents a workflow action in Paperless-NgX.
    """

    id: int
    name: str
    type: str
    assign_title: str | None = None
    assign_tags: list[int] = Field(default_factory=list)
    assign_correspondent: int | None = None
    assign_document_type: int | None = None
    assign_storage_path: int | None = None
    assign_owner: int | None = None


class Workflow(PaperlessModel):
    """
    Represents a workflow in Paperless-NgX.
    """

    id: int
    name: str
    order: int
    enabled: bool
    triggers: list[int]
    actions: list[int]
