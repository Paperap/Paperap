"""
Module for managing workflow actions in the Paperless-NgX API.

This module provides the WorkflowActionResource class which encapsulates all interactions
with workflow actions in a Paperless-NgX system. It leverages the underlying StandardResource
functionality to provide CRUD operations, filtering, and other specialized behaviors for
workflow action management.

Workflow actions are operations that can be performed as part of a workflow in the system,
such as assigning tags, changing document types, or executing custom scripts.
"""

from paperap.models.workflow import WorkflowAction, WorkflowActionQuerySet
from paperap.resources.base import StandardResource


class WorkflowActionResource(StandardResource[WorkflowAction, WorkflowActionQuerySet]):
    """
    Resource for managing workflow actions in Paperless-NgX.

    This resource class extends the StandardResource to provide CRUD operations,
    robust filtering, and other specialized methods for managing workflow actions,
    allowing users to define, update, and remove actions within workflows.

    Workflow actions are the operations that get executed when a workflow is triggered,
    such as adding tags to documents, changing document metadata, or executing scripts.

    Args:
        client: The PaperlessClient instance this resource is associated with.
            This is automatically set when the resource is accessed through the client.

    Attributes:
        model_class (type): The model class associated with this resource (WorkflowAction).
        queryset_class (type): The queryset class used for query operations (WorkflowActionQuerySet).
        name (str): The resource name used in API endpoints.

    Example:
        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>> # Get all workflow actions
        >>> all_actions = client.workflow_actions.all()
        >>> for action in all_actions:
        ...     print(f"{action.id}: {action.name} ({action.type})")
        >>>
        >>> # Create a new tag action
        >>> new_action = client.workflow_actions.create(
        ...     name="Add Tax Tag",
        ...     type="assign_tag",
        ...     arguments={"tag": 5}  # ID of the tax tag
        ... )
        >>>
        >>> # Get a specific action by ID
        >>> action = client.workflow_actions.get(123)
        >>>
        >>> # Update an action
        >>> action.arguments = {"tag": 7}  # Change to a different tag
        >>> action.save()

    """

    model_class: type = WorkflowAction
    """The model class associated with this resource."""

    queryset_class: type = WorkflowActionQuerySet
    """The queryset class used for query operations."""

    name: str = "workflow_actions"
    """The resource name used in API endpoints."""
