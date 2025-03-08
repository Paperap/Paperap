"""




----------------------------------------------------------------------------

   METADATA:

       File:    workflow.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.workflow.queryset import WorkflowQuerySet, WorkflowActionQuerySet, WorkflowTriggerQuerySet


class WorkflowTrigger(StandardModel):
    """
    Represents a workflow trigger in Paperless-NgX.
    """

    sources: list[Any] = Field(default_factory=list)  # TODO unknown subtype
    type: int | None = None
    filter_path: str | None = None
    filter_filename: str | None = None
    filter_mailrule: str | None = None
    matching_algorithm: int | None = None
    match: str | None = None
    is_insensitive: bool
    filter_has_tags: list[int] = Field(default_factory=list)
    filter_has_correspondent: int | None = None
    filter_has_document_type: int | None = None

    class Meta(StandardModel.Meta):
        queryset = WorkflowTriggerQuerySet


class WorkflowAction(StandardModel):
    """
    Represents a workflow action in Paperless-NgX.
    """

    type: str | None = None
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
        queryset = WorkflowQuerySet
