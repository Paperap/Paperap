"""
Module for managing document types in Paperless-NgX.

This module provides the `DocumentTypeResource` class for interacting with
the document types API endpoint in Paperless-NgX. Document types are used to
categorize documents and can have matching rules for automatic assignment.

The resource supports standard CRUD operations (create, retrieve, update, delete)
as well as bulk operations on multiple document types.

Classes:
    DocumentTypeResource: Resource class for managing document types.
"""

from __future__ import annotations

from typing import Type

from paperap.models.document_type import DocumentType, DocumentTypeQuerySet
from paperap.resources.base import BulkEditingMixin, StandardResource


class DocumentTypeResource(StandardResource[DocumentType, DocumentTypeQuerySet], BulkEditingMixin[DocumentType]):
    """
    Resource for managing document types in Paperless-NgX.

    This class provides methods for interacting with the document types API endpoint,
    allowing for operations such as retrieving, creating, updating, and deleting
    document types. Document types are used to categorize documents and can include
    matching rules for automatic assignment during document processing.

    The resource extends `StandardResource` to include standard ID-based operations
    and implements the `BulkEditing` interface for batch operations on multiple
    document types.

    Attributes:
        model_class (Type[DocumentType]): The model class for document types.
        queryset_class (Type[DocumentTypeQuerySet]): The queryset class for
            document type queries.
        name (str): The resource name used in API endpoints ("document_types").

    Examples:
        Basic usage with a client:

        >>> # Get all document types
        >>> all_types = client.document_types.all()
        >>>
        >>> # Create a new document type
        >>> invoice_type = client.document_types.create(
        ...     name="Invoice",
        ...     matching_algorithm="auto",
        ...     match="invoice"
        ... )
        >>>
        >>> # Get a document type by ID
        >>> tax_type = client.document_types.get(5)
        >>>
        >>> # Update a document type
        >>> tax_type.name = "Tax Documents"
        >>> tax_type.save()
        >>>
        >>> # Delete a document type
        >>> tax_type.delete()

    """

    model_class: Type[DocumentType] = DocumentType
    queryset_class: Type[DocumentTypeQuerySet] = DocumentTypeQuerySet
    name: str = "document_types"
