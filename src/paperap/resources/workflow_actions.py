"""
----------------------------------------------------------------------------

   METADATA:

       File:    workflow_actions.py
        Project: paperap
       Created: 2025-03-21
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-21     By Jess Mann

"""

from __future__ import annotations

from paperap.models.workflow import WorkflowAction, WorkflowActionQuerySet
from paperap.resources.base import StandardResource


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """Resource for managing workflow actions."""

    model_class = WorkflowAction
    queryset_class = WorkflowActionQuerySet
    name: str = "workflow_actions"
