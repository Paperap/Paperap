"""
Manage workflow triggers in Paperless-NgX.

Workflow triggers define conditions that, when met, execute a workflow
in the Paperless-NgX system. This module provides classes for interacting
with the workflow triggers API endpoint, enabling creation, retrieval,
modification, and deletion of trigger configurations.

Examples:
    Basic usage to retrieve and filter workflow triggers:

    >>> from paperap import PaperlessClient
    >>> client = PaperlessClient()
    >>>
    >>> # Get all workflow triggers
    >>> all_triggers = client.workflow_triggers.all()
    >>>
    >>> # Get a specific trigger by ID
    >>> trigger = client.workflow_triggers.get(5)
    >>>
    >>> # Filter triggers by name
    >>> invoice_triggers = client.workflow_triggers.filter(name__contains="invoice")

"""

from __future__ import annotations

from typing import Type

from paperap.models.workflow import WorkflowTrigger, WorkflowTriggerQuerySet
from paperap.resources.base import StandardResource


class WorkflowTriggerResource(StandardResource[WorkflowTrigger, WorkflowTriggerQuerySet]):
    """
    Manage workflow triggers in Paperless-NgX.

    Provides methods to interact with the workflow triggers endpoint of the
    Paperless-NgX API. Supports standard CRUD operations (create, read,
    update, delete) for workflow triggers, which define conditions that activate
    workflows in the system.

    Workflow triggers can be configured to activate based on document properties,
    such as specific tags, correspondents, document types, or custom fields.
    When a document matches the specified conditions, the associated workflow
    will be executed.

    Args:
        client: PaperlessClient instance for making API requests.

    Attributes:
        model_class: The model class for workflow triggers.
        queryset_class: The queryset class for query operations on workflow triggers.
        name: The resource name used in API endpoints.

    Examples:
        Create a trigger that activates when documents with a specific tag are added:

        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>>
        >>> # Create a trigger for documents with tag ID 7
        >>> tag_trigger = client.workflow_triggers.create(
        ...     name="Invoice Processing",
        ...     workflow=3,  # ID of the workflow to trigger
        ...     sources=[{"rule_type": "tag", "value": "7"}]
        ... )

        Create a trigger with multiple conditions (AND logic):

        >>> # Trigger for invoices from a specific correspondent
        >>> complex_trigger = client.workflow_triggers.create(
        ...     name="Vendor Invoice Processing",
        ...     workflow=5,
        ...     sources=[
        ...         {"rule_type": "document_type", "value": "3"},  # Invoice type
        ...         {"rule_type": "correspondent", "value": "12"}  # Specific vendor
        ...     ]
        ... )

        Update an existing trigger:

        >>> trigger = client.workflow_triggers.get(5)
        >>> trigger.name = "Updated Trigger Name"
        >>> trigger.save()

        Delete a trigger:

        >>> trigger = client.workflow_triggers.get(5)
        >>> trigger.delete()

    """

    model_class: Type[WorkflowTrigger] = WorkflowTrigger
    queryset_class: Type[WorkflowTriggerQuerySet] = WorkflowTriggerQuerySet
    name: str = "workflow_triggers"
