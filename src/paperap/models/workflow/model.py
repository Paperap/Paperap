"""
Models for Paperless-NgX workflow functionality.

This module contains the data models representing workflows, workflow triggers,
workflow actions, and workflow runs in the Paperless-NgX system. These models
map directly to the corresponding API resources and provide a Pythonic interface
for interacting with the workflow system.

Workflows in Paperless-NgX consist of triggers (conditions that start a workflow)
and actions (operations performed when a trigger is activated).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Self

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

    A workflow trigger defines the conditions under which a workflow will be executed.
    Triggers can be based on document creation, modification, scheduled events, or
    other system events.

    Attributes:
        sources: List of source types that can activate this trigger.
        type: The type of trigger (e.g., document added, scheduled).
        filter_path: Path filter for file-based triggers.
        filter_filename: Filename filter for file-based triggers.
        filter_mailrule: Mail rule filter for email-based triggers.
        filter_has_tags: List of tag IDs that documents must have to trigger.
        filter_has_correspondent: Correspondent ID that documents must have.
        filter_has_document_type: Document type ID that documents must have.
        schedule_date_field: Field to use for date-based scheduling.
        schedule_date_custom_field: Custom field ID to use for date-based scheduling.
        schedule_offset_days: Days to offset from the scheduled date.
        schedule_is_recurring: Whether this trigger recurs on a schedule.
        schedule_recurring_interval_days: Interval in days for recurring triggers.

    Examples:
        >>> # Create a trigger for new documents with a specific tag
        >>> trigger = WorkflowTrigger(
        ...     sources=["source_document"],
        ...     type="document_added",
        ...     filter_has_tags=[5]  # Tag ID 5
        ... )

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
    schedule_date_custom_field: int | None = None
    schedule_offset_days: int = 0
    schedule_is_recurring: bool = False
    schedule_recurring_interval_days: int = 1

    class Meta(StandardModel.Meta):
        """Metadata for the WorkflowTrigger model."""

        queryset = WorkflowTriggerQuerySet


class WorkflowAction(StandardModel):
    """
    Represents a workflow action in Paperless-NgX.

    A workflow action defines an operation to be performed when a workflow is triggered.
    Actions can include assigning metadata to documents, removing metadata, sending
    emails, or triggering webhooks.

    Attributes:
        type: The type of action to perform.

        # Assignment action attributes
        assign_title: Title to assign to the document.
        assign_tags: List of tag IDs to assign to the document.
        assign_correspondent: Correspondent ID to assign to the document.
        assign_document_type: Document type ID to assign to the document.
        assign_storage_path: Storage path ID to assign to the document.
        assign_owner: Owner ID to assign to the document.
        assign_view_users: List of user IDs to grant view permissions.
        assign_view_groups: List of group IDs to grant view permissions.
        assign_change_users: List of user IDs to grant change permissions.
        assign_change_groups: List of group IDs to grant change permissions.
        assign_custom_fields: List of custom field IDs to assign.
        assign_custom_fields_values: Dictionary mapping custom field IDs to values.

        # Removal action attributes
        remove_all_tags: Whether to remove all tags from the document.
        remove_tags: List of tag IDs to remove from the document.
        remove_all_correspondents: Whether to remove all correspondents.
        remove_correspondents: List of correspondent IDs to remove.
        remove_all_document_types: Whether to remove all document types.
        remove_document_types: List of document type IDs to remove.
        remove_all_storage_paths: Whether to remove all storage paths.
        remove_storage_paths: List of storage path IDs to remove.
        remove_custom_fields: List of custom field IDs to remove.
        remove_all_custom_fields: Whether to remove all custom fields.
        remove_all_owners: Whether to remove all owners.
        remove_owners: List of owner IDs to remove.
        remove_all_permissions: Whether to remove all permissions.
        remove_view_users: List of user IDs to remove view permissions.
        remove_view_groups: List of group IDs to remove view permissions.
        remove_change_users: List of user IDs to remove change permissions.
        remove_change_groups: List of group IDs to remove change permissions.

        # Email and webhook action attributes
        email: Configuration for email actions.
        webhook: Configuration for webhook actions.

    Examples:
        >>> # Create an action to assign tags and a document type
        >>> action = WorkflowAction(
        ...     type="assign",
        ...     assign_tags=[1, 2],
        ...     assign_document_type=5
        ... )

    """

    type: WorkflowActionType | None = None

    # Assignment actions
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
    assign_custom_fields_values: dict[str, Any] = Field(default_factory=dict)

    # Removal actions
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

    # Email action
    email: dict[str, Any] | None = None

    # Webhook action
    webhook: dict[str, Any] | None = None

    class Meta(StandardModel.Meta):
        """Metadata for the WorkflowAction model."""

        queryset = WorkflowActionQuerySet


class Workflow(StandardModel):
    """
    Represents a workflow in Paperless-NgX.

    A workflow is a combination of triggers and actions that automate document
    processing in Paperless-NgX. When a trigger condition is met, the associated
    actions are executed.

    Attributes:
        name: The name of the workflow.
        order: The execution order of this workflow relative to others.
        enabled: Whether this workflow is currently active.
        triggers: List of trigger configurations for this workflow.
        actions: List of action configurations for this workflow.

    Examples:
        >>> # Create a simple workflow
        >>> workflow = Workflow(
        ...     name="Tag Invoices",
        ...     enabled=True,
        ...     triggers=[{"type": "document_added", "filter_filename": "invoice"}],
        ...     actions=[{"type": "assign", "assign_tags": [5]}]
        ... )

    """

    name: str
    order: int | None = None
    enabled: bool | None = None
    triggers: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)

    class Meta(StandardModel.Meta):
        """Metadata for the Workflow model."""

        queryset = WorkflowQuerySet


class WorkflowRun(StandardModel):
    """
    Represents a workflow run in Paperless-NgX.

    A workflow run is a record of a specific execution of a workflow, including
    its status, timing information, and any errors that occurred during execution.

    Attributes:
        workflow: ID of the workflow that was executed.
        document: ID of the document that triggered the workflow.
        type: The type of trigger that initiated this workflow run.
        run_at: The time when this workflow run was scheduled.
        started: The time when this workflow run started execution.
        finished: The time when this workflow run completed execution.
        status: The current status of this workflow run.
        error: Error message if the workflow run failed.

    Examples:
        >>> # Check the status of a workflow run
        >>> run = client.workflow_runs.get(123)
        >>> if run.status == "SUCCESS":
        ...     print(f"Workflow completed successfully at {run.finished}")
        ... else:
        ...     print(f"Workflow failed: {run.error}")

    """

    workflow: int | None = None
    document: int | None = None
    type: WorkflowTriggerType | None = None
    run_at: datetime
    started: datetime | None = None
    finished: datetime | None = None
    status: str | None = None
    error: str | None = None
