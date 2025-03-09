"""




----------------------------------------------------------------------------

   METADATA:

       File:    workflows.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations
from paperap.models.workflow import (
    Workflow,
    WorkflowAction,
    WorkflowTrigger,
    WorkflowActionQuerySet,
    WorkflowQuerySet,
    WorkflowTriggerQuerySet,
)
from paperap.resources.base import PaperlessResource, StandardResource


class WorkflowResource(StandardResource[Workflow, WorkflowQuerySet]):
    """Resource for managing workflows."""

    model_class = Workflow
    name = "workflows"


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """Resource for managing workflow triggers."""

    model_class = WorkflowTrigger
    name = "workflow_triggers"


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """Resource for managing workflow actions."""

    model_class = WorkflowAction
    name = "workflow_actions"
