

from __future__ import annotations

from paperap.models.workflow import WorkflowAction, WorkflowActionQuerySet
from paperap.resources.base import StandardResource


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """Resource for managing workflow actions."""

    model_class = WorkflowAction
    queryset_class = WorkflowActionQuerySet
    name: str = "workflow_actions"
