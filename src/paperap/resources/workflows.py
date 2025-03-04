"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    workflows.py                                                                                         *
*        Project: resources                                                                                            *
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

from paperap.models.workflow import Workflow, WorkflowAction, WorkflowTrigger
from paperap.resources.base import PaperlessResource


class WorkflowResource(PaperlessResource[Workflow]):
    """Resource for managing workflows."""

    model_class = Workflow


class WorkflowTriggerResource(PaperlessResource[WorkflowTrigger]):
    """Resource for managing workflow triggers."""

    model_class = WorkflowTrigger


class WorkflowActionResource(PaperlessResource[WorkflowAction]):
    """Resource for managing workflow actions."""

    model_class = WorkflowAction
