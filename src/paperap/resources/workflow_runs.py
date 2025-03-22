"""
----------------------------------------------------------------------------

   METADATA:

       File:    workflow_runs.py
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

from paperap.models.workflow import WorkflowRun, WorkflowRunQuerySet
from paperap.resources.base import StandardResource


class WorkflowRunResource(StandardResource[WorkflowRun, WorkflowRunQuerySet]):
    """Resource for managing workflow runs."""

    model_class = WorkflowRun
    queryset_class = WorkflowRunQuerySet
    name: str = "workflow_runs"
