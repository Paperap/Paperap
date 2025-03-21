"""
----------------------------------------------------------------------------

   METADATA:

       File:    workflow.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Self

from pydantic import Field

from paperap.const import (
    ScheduleDateFieldType,
    WorkflowActionType,
    WorkflowTriggerMatchingType,
    WorkflowTriggerSourceType,
    WorkflowTriggerType,
)
from paperap.models.abstract.model import StandardModel
from paperap.models.mixins.models import MatcherMixin
from paperap.models.workflow.queryset import WorkflowActionQuerySet, WorkflowQuerySet, WorkflowTriggerQuerySet


class WorkflowTrigger(StandardModel, MatcherMixin):
    """
    Represents a workflow trigger in Paperless-NgX.
    """

    sources: list[WorkflowTriggerSourceType] = Field(default_factory=list)
    type: WorkflowTriggerType | None = None
    filter_path: str | None = None
    filter_filename: str | None = None
    filter_mailrule: str | None = None
    filter_has_tags: list[int] = Field(default_factory=list)
    filter_has_correspondent: int | None = None
    filter_has_document_type: int | None = None
    schedule_date_field: ScheduleDateFieldType | None = None

    class Meta(StandardModel.Meta):
        queryset = WorkflowTriggerQuerySet


class WorkflowAction(StandardModel):
    """
    Represents a workflow action in Paperless-NgX.
    """

    type: WorkflowActionType | None = None
    assign_title: str | None = None
    assign_tags: list[int] = Field(default_factory=list)
    assign_correspondent: int | None = None
    assign_document_type: int | None = None
    assign_storage_path: int | None = None
    assign_owner: int | None = None
    assign_view_users: list[int] = Field(default_factory=list)
    assign_view_groups: list[int] = Field(default_factory=list)
    assign_change_users: list[int] = Field(default_factory=list)
    assign_change_groups: list[int] = Field(default_factory=list)
    assign_custom_fields: list[int] = Field(default_factory=list)
    remove_all_tags: bool | None = None
    remove_tags: list[int] = Field(default_factory=list)
    remove_all_correspondents: bool | None = None
    remove_correspondents: list[int] = Field(default_factory=list)
    remove_all_document_types: bool | None = None
    remove_document_types: list[int] = Field(default_factory=list)
    remove_all_storage_paths: bool | None = None
    remove_storage_paths: list[int] = Field(default_factory=list)
    remove_custom_fields: list[int] = Field(default_factory=list)
    remove_all_custom_fields: bool | None = None
    remove_all_owners: bool | None = None
    remove_owners: list[int] = Field(default_factory=list)
    remove_all_permissions: bool | None = None
    remove_view_users: list[int] = Field(default_factory=list)
    remove_view_groups: list[int] = Field(default_factory=list)
    remove_change_users: list[int] = Field(default_factory=list)
    remove_change_groups: list[int] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        queryset = WorkflowActionQuerySet


class Workflow(StandardModel):
    """
    Represents a workflow in Paperless-NgX.
    """

    name: str
    order: int | None = None
    enabled: bool | None = None
    triggers: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        """
        Metadata for the Workflow model.
        """

        queryset = WorkflowQuerySet


class WorkflowRun(StandardModel):
    """
    Represents a workflow run in Paperless-NgX.
    """

    workflow: int | None = None
    document: int | None = None
    type: WorkflowTriggerType | None = None
    run_at: datetime
