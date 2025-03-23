

from __future__ import annotations

from paperap.models.workflow import (
    Workflow,
    WorkflowAction,
    WorkflowActionQuerySet,
    WorkflowQuerySet,
    WorkflowTrigger,
    WorkflowTriggerQuerySet,
)
from paperap.resources.base import BaseResource, StandardResource


class WorkflowResource(StandardResource[Workflow, WorkflowQuerySet]):
    """Resource for managing workflows."""

    model_class = Workflow
    queryset_class = WorkflowQuerySet
    name: str = "workflows"


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """Resource for managing workflow triggers."""

    model_class = WorkflowTrigger
    queryset_class = WorkflowTriggerQuerySet
    name: str = "workflow_triggers"


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """Resource for managing workflow actions."""

    model_class = WorkflowAction
    queryset_class = WorkflowActionQuerySet
    name: str = "workflow_actions"
