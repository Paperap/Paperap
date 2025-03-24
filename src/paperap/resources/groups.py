"""
Group resource module for interacting with Paperless-NgX groups API.

This module provides the GroupResource class for managing user groups in
Paperless-NgX. It enables operations such as retrieving, creating, updating,
and deleting group resources through the API.
"""

from __future__ import annotations

from paperap.models.user import Group, GroupQuerySet
from paperap.resources.base import StandardResource


class GroupResource(StandardResource[Group, GroupQuerySet]):
    """
    Resource for managing user groups in Paperless-NgX.

    This class provides methods for interacting with the groups API endpoint
    in Paperless-NgX. It allows for the retrieval, creation, updating, and
    deletion of group resources. Groups are used for organizing users and
    controlling access permissions within Paperless-NgX.

    The GroupResource inherits from StandardResource, providing standard CRUD
    operations with proper typing for Group models and GroupQuerySet results.

    Attributes:
        model_class (Type[Group]): The model class associated with this resource.
        queryset_class (Type[GroupQuerySet]): The queryset class used for query operations.
        name (str): The resource name used in API endpoints.

    Example:
        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>> # Get all groups
        >>> all_groups = client.groups.all()
        >>> # Create a new group
        >>> new_group = client.groups.create(name="Finance Team")
        >>> # Get a specific group by ID
        >>> finance_group = client.groups.get(5)
        >>> # Update a group
        >>> finance_group.name = "Finance Department"
        >>> finance_group.save()

    """

    model_class = Group
    queryset_class = GroupQuerySet
    name: str = "groups"
