"""
Manage Paperless-ngx workflows through the API.

Provides resource classes for interacting with workflow-related endpoints
in the Paperless-ngx API. Enables programmatic creation, retrieval, updating,
and deletion of workflows, triggers, and actions.

Resources:
    WorkflowResource: Manages workflow definitions
    WorkflowTriggerResource: Manages conditions that activate workflows
    WorkflowActionResource: Manages operations performed by workflows

Workflows automate document processing by executing predefined actions when
documents match specific criteria, such as automatically tagging invoices
or assigning correspondents based on document content.
"""

from __future__ import annotations

from typing import Any, Type

from paperap.models.workflow import (
    Workflow,
    WorkflowAction,
    WorkflowActionQuerySet,
    WorkflowQuerySet,
    WorkflowTrigger,
    WorkflowTriggerQuerySet,
)
from paperap.resources.base import StandardResource


class WorkflowResource(StandardResource[Workflow, WorkflowQuerySet]):
    """
    Manage Paperless-ngx workflow definitions.

    Provides methods for creating, retrieving, updating, and deleting workflow
    definitions through the Paperless-ngx API. Workflows define automated processes
    that execute when specific conditions are met.

    Attributes:
        model_class (Type[Workflow]): Class representing workflow instances.
        queryset_class (Type[WorkflowQuerySet]): Class for querying workflow collections.
        name (str): Resource identifier used in API endpoint paths.

    Example:
        Create and manage workflows:

        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>>
        >>> # Create a new workflow
        >>> workflow = client.workflows.create(
        ...     name="Invoice Processing",
        ...     order=1,
        ...     enabled=True
        ... )
        >>>
        >>> # Enable or disable a workflow
        >>> workflow.enabled = False
        >>> workflow.save()
        >>>
        >>> # Find workflows by name
        >>> invoice_flows = client.workflows.filter(name__contains="invoice")
        >>>
        >>> # Get all enabled workflows
        >>> active_flows = client.workflows.filter(enabled=True)

    """

    model_class: Type[Workflow] = Workflow
    queryset_class: Type[WorkflowQuerySet] = WorkflowQuerySet
    name: str = "workflows"


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """
    Manage conditions that activate Paperless-ngx workflows.

    Provides methods for creating, retrieving, updating, and deleting workflow trigger
    definitions. Triggers define when workflows should execute, typically based on
    document events (creation, modification) and matching criteria.

    Attributes:
        model_class (Type[WorkflowTrigger]): Class representing workflow trigger instances.
        queryset_class (Type[WorkflowTriggerQuerySet]): Class for querying trigger collections.
        name (str): Resource identifier used in API endpoint paths.

    Example:
        Create and query triggers with document matching rules:

        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>>
        >>> # Create a trigger for new documents with "invoice" in the title
        >>> trigger = client.workflow_triggers.create(
        ...     workflow=1,  # ID of the parent workflow
        ...     type=1,      # Document created trigger type (1=created, 2=modified)
        ...     sources=[],  # Empty list means all sources
        ...     filter_rules=[
        ...         {"rule_type": "title", "value": "invoice", "operator": "icontains"}
        ...     ]
        ... )
        >>>
        >>> # Create a trigger for documents from a specific correspondent
        >>> trigger = client.workflow_triggers.create(
        ...     workflow=2,
        ...     type=1,
        ...     filter_rules=[
        ...         {"rule_type": "correspondent", "value": "5"}
        ...     ]
        ... )
        >>>
        >>> # Find triggers for a specific workflow
        >>> workflow_id = 5
        >>> triggers = client.workflow_triggers.filter(workflow=workflow_id)

    """

    model_class = WorkflowTrigger
    queryset_class = WorkflowTriggerQuerySet
    name: str = "workflow_triggers"


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """
    Manage operations performed by Paperless-ngx workflows.

    Provides methods for creating, retrieving, updating, and deleting workflow action
    definitions. Actions define what operations are performed when a workflow is triggered,
    such as assigning tags, correspondents, or document types to matching documents.

    Attributes:
        model_class (Type[WorkflowAction]): Class representing workflow action instances.
        queryset_class (Type[WorkflowActionQuerySet]): Class for querying action collections.
        name (str): Resource identifier used in API endpoint paths.

    Example:
        Create and manage actions for document processing:

        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>>
        >>> # Create an action to tag documents
        >>> action1 = client.workflow_actions.create(
        ...     workflow=1,           # ID of the parent workflow
        ...     type="assign_tag",    # Action type
        ...     assign_tags=[5, 8],   # IDs of tags to assign
        ...     order=1               # Execution order within workflow
        ... )
        >>>
        >>> # Create an action to assign a correspondent
        >>> action2 = client.workflow_actions.create(
        ...     workflow=1,
        ...     type="assign_correspondent",
        ...     assign_correspondent=3,  # ID of correspondent to assign
        ...     order=2                  # Execute after the first action
        ... )
        >>>
        >>> # Create an action to set a document type
        >>> action3 = client.workflow_actions.create(
        ...     workflow=1,
        ...     type="assign_document_type",
        ...     assign_document_type=7,  # ID of document type to assign
        ...     order=3                  # Execute third in sequence
        ... )
        >>>
        >>> # Order actions by their execution sequence
        >>> actions = client.workflow_actions.filter(workflow=1).order_by("order")
        >>>
        >>> # Update an action's order
        >>> action1.order = 3  # Move to end of sequence
        >>> action1.save()

    """

    model_class = WorkflowAction
    queryset_class = WorkflowActionQuerySet
    name: str = "workflow_actions"
