

from __future__ import annotations

from paperap.models.workflow import WorkflowTrigger, WorkflowTriggerQuerySet
from paperap.resources.base import StandardResource


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """Resource for managing workflow triggers."""

    model_class = WorkflowTrigger
    queryset_class = WorkflowTriggerQuerySet
    name: str = "workflow_triggers"
