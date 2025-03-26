"""
Provide resource interface for managing Paperless-NgX tags.

This module implements the TagResource class which serves as the interface for
interacting with tags in the Paperless-NgX system. It extends StandardResource
to provide CRUD operations and bulk editing capabilities for tag objects.

Tags in Paperless-NgX are used to categorize and organize documents, and can
have properties like name, color, and matching rules for automatic assignment.

Example:
    Access tags through a PaperlessClient instance:

    >>> from paperap import PaperlessClient
    >>> client = PaperlessClient()
    >>> tags = client.tags.all()
    >>> for tag in tags:
    ...     print(f"{tag.name}: {tag.color}")

    Create a new tag:

    >>> new_tag = client.tags.create(
    ...     name="Tax Documents",
    ...     color="#00ff00"
    ... )

"""

from __future__ import annotations

from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.base import BaseResource, BulkEditingMixin, StandardResource


class TagResource(StandardResource[Tag, TagQuerySet], BulkEditingMixin[Tag]):
    """
    Manage tag resources in the Paperless-NgX system.

    Provides an interface to interact with the tags endpoint of the Paperless-NgX API.
    Supports standard CRUD operations (create, read, update, delete) and bulk editing
    of tags through the BulkEditing mixin.

    Tags are used to categorize and organize documents within Paperless-NgX and can
    have properties such as name, color, and matching rules for automatic assignment
    to documents.

    Args:
        client: The PaperlessClient instance used for API communication.

    Attributes:
        model_class: The Tag model class associated with this resource.
        queryset_class: The TagQuerySet class used for querying tags.
        name: The name of the resource, used in API endpoints.

    Example:
        Create a new tag:

        >>> client = PaperlessClient()
        >>> new_tag = client.tags.create(
        ...     name="Tax Documents",
        ...     color="#00ff00",
        ...     is_inbox_tag=False
        ... )

        Filter tags by name:

        >>> tax_tags = client.tags.filter(name__contains="tax")
        >>> for tag in tax_tags:
        ...     print(f"{tag.id}: {tag.name}")

        Get a specific tag by ID:

        >>> tag = client.tags.get(5)
        >>> print(f"Tag color: {tag.color}")

    """

    model_class = Tag
    queryset_class = TagQuerySet
    name: str = "tags"
