"""




----------------------------------------------------------------------------

   METADATA:

       File:    workflow.py
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

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import PaperlessModel


class WorkflowTrigger(PaperlessModel):
    """
    Represents a workflow trigger in Paperless-NgX.
    """
    sources : list[Any] # TODO unknown subtype
    type: int
    filter_path: str | None = None
    filter_filename: str | None = None
    filter_mailrule : str | None = None
    matching_algorithm: int
    match : str
    is_insensitive: bool = True
    filter_has_tags : list[int] = Field(default_factory=list)
    filter_has_correspondent : int | None = None
    filter_has_document_type : int | None = None


class WorkflowAction(PaperlessModel):
    """
    Represents a workflow action in Paperless-NgX.
    """

    type: str
    assign_title: str | None = None
    assign_tags: list[int] = Field(default_factory=list)
    assign_correspondent: int | None = None
    assign_document_type: int | None = None
    assign_storage_path: int | None = None
    assign_owner: int | None = None
    assign_owner: int | None = None
    assign_view_users: list[int] = Field(default_factory=list)
    assign_view_groups: list[int] = Field(default_factory=list)
    assign_change_users: list[int] = Field(default_factory=list)
    assign_change_groups: list[int] = Field(default_factory=list)
    assign_custom_fields: list[int] = Field(default_factory=list)
    remove_all_tags: bool = False
    remove_tags: list[int] = Field(default_factory=list)
    remove_all_correspondents: bool = False
    remove_correspondents: list[int] = Field(default_factory=list)
    remove_all_document_types: bool = False
    remove_document_types: list[int] = Field(default_factory=list)
    remove_all_storage_paths: bool = False
    remove_storage_paths: list[int] = Field(default_factory=list)
    remove_custom_fields: list[int] = Field(default_factory=list)
    remove_all_custom_fields: bool = False
    remove_all_owners: bool = False
    remove_owners: list[int] = Field(default_factory=list)
    remove_all_permissions: bool = False
    remove_view_users: list[int] = Field(default_factory=list)
    remove_view_groups: list[int] = Field(default_factory=list)
    remove_change_users: list[int] = Field(default_factory=list)
    remove_change_groups: list[int] = Field(default_factory=list)

class Workflow(PaperlessModel):
    """
    Represents a workflow in Paperless-NgX.
    """

    name: str
    order: int = 0
    enabled: bool = True
    triggers: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
