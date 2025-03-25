"""
Correspondent resource module for interacting with Paperless-NgX correspondent endpoints.

This module provides the CorrespondentResource class which handles all API interactions
related to correspondents in a Paperless-NgX system. Correspondents represent people or
organizations that send or receive documents.

Typical usage example:
    >>> # Get all correspondents
    >>> correspondents = client.correspondents.all()
    >>>
    >>> # Create a new correspondent
    >>> new_correspondent = client.correspondents.create(name="Electric Company")
    >>>
    >>> # Get a specific correspondent
    >>> electric = client.correspondents.get(3)
"""

from __future__ import annotations

from paperap.models.correspondent import Correspondent, CorrespondentQuerySet
from paperap.resources.base import BaseResource, BulkEditingMixin, StandardResource


class CorrespondentResource(StandardResource[Correspondent, CorrespondentQuerySet], BulkEditingMixin[Correspondent]):
    """
    Resource for managing correspondents in Paperless-NgX.

    This resource provides methods for creating, retrieving, updating, and deleting
    correspondent objects via the Paperless-NgX API. It extends the standard
    resource methods and incorporates bulk editing capabilities for efficient
    processing of multiple correspondent records.

    Correspondents represent people or organizations that send or receive documents
    in a Paperless-NgX system. They can be used to automatically categorize documents
    based on matching rules.

    Args:
        client: The PaperlessClient instance this resource is attached to.

    Attributes:
        model_class (Type[Correspondent]): Reference to the Correspondent model class.
        queryset_class (Type[CorrespondentQuerySet]): Reference to the query set class for correspondents.
        name (str): The API endpoint name for managing correspondents.

    Examples:
        Create a new correspondent:

        >>> new_correspondent = client.correspondents.create(
        ...     name="Electric Company",
        ...     matching_algorithm="auto",
        ...     match="electric"
        ... )

        Retrieve a correspondent by ID:

        >>> correspondent = client.correspondents.get(3)
        >>> print(correspondent.name)

        Update a correspondent:

        >>> correspondent = client.correspondents.get(3)
        >>> correspondent.name = "Updated Name"
        >>> correspondent.save()

        Delete a correspondent:

        >>> correspondent = client.correspondents.get(3)
        >>> correspondent.delete()

        Filter correspondents:

        >>> electric_correspondents = client.correspondents().filter(
        ...     name__icontains="electric"
        ... )

        Bulk operations on correspondents:

        >>> # Get all correspondents with "Company" in the name
        >>> company_correspondents = client.correspondents().filter(name__icontains="Company")
        >>> # Update all of them at once
        >>> company_correspondents.update(matching_algorithm="auto")

    """

    model_class = Correspondent
    queryset_class = CorrespondentQuerySet
    name: str = "correspondents"
