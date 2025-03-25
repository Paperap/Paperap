"""
Document notes resource module.

This module provides the DocumentNoteResource class for managing document notes
in the Paperless-NgX API. Document notes allow users to add annotations and
comments to documents stored in the Paperless-NgX system.

The resource extends StandardResource to provide CRUD operations (create, read,
update, delete) for document notes, with appropriate serialization and
deserialization between the API and the DocumentNote model.

Classes:
    DocumentNoteResource: Resource for managing document notes in Paperless-NgX.
"""

from __future__ import annotations

from paperap.models.document import DocumentNote, DocumentNoteQuerySet
from paperap.resources.base import StandardResource


class DocumentNoteResource(StandardResource[DocumentNote, DocumentNoteQuerySet]):
    """
    Resource for managing document notes in Paperless-NgX.

    This class provides methods for interacting with the document notes API
    endpoint, allowing for operations such as retrieval, creation, updating,
    and deletion of document notes. Document notes are annotations or comments
    attached to specific documents in the Paperless-NgX system.

    The resource handles the communication with the API, including request
    formatting, response parsing, and model instantiation. It provides a
    high-level interface for working with document notes without needing to
    directly interact with the API endpoints.

    Attributes:
        model_class (Type[DocumentNote]): The model class for document notes.
        queryset_class (Type[DocumentNoteQuerySet]): The queryset class for
            query operations on document notes.
        name (str): The resource name used in API endpoints ("document_notes").

    Example:
        >>> # Get a specific note by ID
        >>> note = client.document_notes.get(1)
        >>> print(note.content)
        >>>
        >>> # Create a new note for a document
        >>> new_note = client.document_notes.create(
        ...     document=42,
        ...     content="Important information about this invoice"
        ... )
        >>>
        >>> # Update an existing note
        >>> note.content = "Updated comment"
        >>> note.save()
        >>>
        >>> # Delete a note
        >>> note.delete()

    """

    model_class = DocumentNote
    queryset_class = DocumentNoteQuerySet
    name: str = "document_notes"
