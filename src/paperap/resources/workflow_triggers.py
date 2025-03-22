"""
----------------------------------------------------------------------------

   METADATA:

       File:    workflow_triggers.py
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

from paperap.models.workflow import WorkflowTrigger, WorkflowTriggerQuerySet
from paperap.resources.base import StandardResource


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """Resource for managing workflow triggers."""

    model_class = WorkflowTrigger
    queryset_class = WorkflowTriggerQuerySet
    name: str = "workflow_triggers"
