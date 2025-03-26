"""
Provide document models for interacting with Paperless-ngx documents.

This module contains the Document and DocumentNote models, which represent
documents and their associated notes in the Paperless-ngx system. These models
provide methods for retrieving, updating, and managing document metadata,
content, and relationships with other entities like tags, correspondents,
and custom fields.
"""

from __future__ import annotations

import logging
from datetime import datetime
import re
from typing import TYPE_CHECKING, Annotated, Any, Iterable, Iterator, Self, TypedDict, cast, override

import pydantic
from pydantic import Field, field_serializer, field_validator, model_serializer
from typing_extensions import TypeVar

from paperap.const import (
    CustomFieldTypedDict,
    CustomFieldTypes,
    CustomFieldValues,
    DocumentStorageType,
    FilteringStrategies,
)
from paperap.exceptions import ResourceNotFoundError
from paperap.models.abstract.model import StandardModel
from paperap.models.document.meta import SUPPORTED_FILTERING_PARAMS
from paperap.models.document.queryset import DocumentQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent.model import Correspondent
    from paperap.models.custom_field import CustomField, CustomFieldQuerySet
    from paperap.models.document.download.model import DownloadedDocument
    from paperap.models.document.metadata.model import DocumentMetadata
    from paperap.models.document.suggestions.model import DocumentSuggestions
    from paperap.models.document_type.model import DocumentType
    from paperap.models.storage_path.model import StoragePath
    from paperap.models.tag import Tag, TagQuerySet
    from paperap.models.user.model import User
    from paperap.resources.documents import DocumentResource

logger = logging.getLogger(__name__)


class DocumentNote(StandardModel):
    """
    Represent a note on a Paperless-ngx document.

    This class models user-created notes that can be attached to documents in the
    Paperless-ngx system. Notes include information about when they were created,
    who created them, and their content.

    Attributes:
        deleted_at (datetime | None): Timestamp when the note was deleted, or None if not deleted.
        restored_at (datetime | None): Timestamp when the note was restored after deletion, or None.
        transaction_id (int | None): ID of the transaction that created or modified this note.
        note (str): The text content of the note.
        created (datetime): Timestamp when the note was created.
        document (int): ID of the document this note is attached to.
        user (int): ID of the user who created this note.

    Examples:
        >>> note = client.document_notes().get(1)
        >>> print(note.note)
        'This is an important document'
        >>> print(note.created)
        2023-01-15 14:30:22

    """

    deleted_at: datetime | None = None
    restored_at: datetime | None = None
    transaction_id: int | None = None
    note: str
    created: datetime
    document: int
    user: int

    class Meta(StandardModel.Meta):
        read_only_fields = {"deleted_at", "restored_at", "transaction_id", "created"}

    @field_serializer("deleted_at", "restored_at", "created")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        Serialize datetime fields to ISO format.

        Converts datetime objects to ISO 8601 formatted strings for JSON serialization.
        Returns None if the input value is None.

        Args:
            value (datetime | None): The datetime value to serialize.

        Returns:
            str | None: The serialized datetime value as an ISO 8601 string, or None if the value is None.

        """
        return value.isoformat() if value else None

    def get_document(self) -> "Document":
        """
        Get the document associated with this note.

        Retrieves the full Document object that this note is attached to
        by making an API request using the document ID.

        Returns:
            Document: The document associated with this note.

        Example:
            >>> note = client.document_notes().get(1)
            >>> document = note.get_document()
            >>> print(document.title)
            'Invoice #12345'

        """
        return self._client.documents().get(self.document)

    def get_user(self) -> "User":
        """
        Get the user who created this note.

        Retrieves the full User object for the user who created this note
        by making an API request using the user ID.

        Returns:
            User: The user who created this note.

        Example:
            >>> note = client.document_notes().get(1)
            >>> user = note.get_user()
            >>> print(user.username)
            'admin'

        """
        return self._client.users().get(self.user)


class Document(StandardModel):
    """
    Represent a Paperless-ngx document.

    This class models documents stored in the Paperless-ngx system, providing access
    to document metadata, content, and related objects. It supports operations like
    downloading, updating metadata, and managing tags and custom fields.

    Attributes:
        added (datetime | None): Timestamp when the document was added to the system.
        archive_checksum (str | None): Checksum of the archived version of the document.
        archive_filename (str | None): Filename of the archived version.
        archive_serial_number (int | None): Serial number in the archive system.
        archived_file_name (str | None): Original name of the archived file.
        checksum (str | None): Checksum of the original document.
        content (str): Full text content of the document.
        correspondent_id (int | None): ID of the associated correspondent.
        created (datetime | None): Timestamp when the document was created.
        created_date (str | None): Creation date as a string.
        custom_field_dicts (list[CustomFieldValues]): Custom fields associated with the document.
        deleted_at (datetime | None): Timestamp when the document was deleted, or None.
        document_type_id (int | None): ID of the document type.
        filename (str | None): Current filename in the system.
        is_shared_by_requester (bool): Whether the document is shared by the requester.
        notes (list[DocumentNote]): Notes attached to this document.
        original_filename (str | None): Original filename when uploaded.
        owner (int | None): ID of the document owner.
        page_count (int | None): Number of pages in the document.
        storage_path_id (int | None): ID of the storage path.
        storage_type (DocumentStorageType | None): Type of storage used.
        tag_ids (list[int]): List of tag IDs associated with this document.
        title (str): Title of the document.
        user_can_change (bool | None): Whether the current user can modify this document.

    Examples:
        >>> document = client.documents().get(pk=1)
        >>> document.title = 'Example Document'
        >>> document.save()
        >>> document.title
        'Example Document'

        # Get document metadata
        >>> metadata = document.get_metadata()
        >>> print(metadata.original_mime_type)
        'application/pdf'

        # Download document
        >>> download = document.download()
        >>> with open(download.disposition_filename, 'wb') as f:
        ...     f.write(download.content)

        # Get document suggestions
        >>> suggestions = document.get_suggestions()
        >>> print(suggestions.tags)
        ['Invoice', 'Tax', '2023']

    """

    # where did this come from? It's not in sample data?
    added: datetime | None = None
    archive_checksum: str | None = None
    archive_filename: str | None = None
    archive_serial_number: int | None = None
    archived_file_name: str | None = None
    checksum: str | None = None
    content: str = ""
    correspondent_id: int | None = None
    created: datetime | None = Field(description="Creation timestamp", default=None)
    created_date: str | None = None
    custom_field_dicts: Annotated[list[CustomFieldValues], Field(default_factory=list)]
    deleted_at: datetime | None = None
    document_type_id: int | None = None
    filename: str | None = None
    is_shared_by_requester: bool = False
    notes: "list[DocumentNote]" = Field(default_factory=list)
    original_filename: str | None = None
    owner: int | None = None
    page_count: int | None = None
    storage_path_id: int | None = None
    storage_type: DocumentStorageType | None = None
    tag_ids: Annotated[list[int], Field(default_factory=list)]
    title: str = ""
    user_can_change: bool | None = None

    _correspondent: tuple[int, Correspondent] | None = None
    _document_type: tuple[int, DocumentType] | None = None
    _storage_path: tuple[int, StoragePath] | None = None
    _resource: "DocumentResource"  # type: ignore # nested generics not supported
    __search_hit__: dict[str, Any] | None = None

    class Meta(StandardModel.Meta):
        # NOTE: Filtering appears to be disabled by paperless on page_count
        read_only_fields = {"page_count", "deleted_at", "is_shared_by_requester", "archived_file_name"}
        filtering_disabled = {"page_count", "deleted_at", "is_shared_by_requester"}
        filtering_strategies = {FilteringStrategies.WHITELIST}
        field_map = {
            "tags": "tag_ids",
            "custom_fields": "custom_field_dicts",
            "document_type": "document_type_id",
            "correspondent": "correspondent_id",
            "storage_path": "storage_path_id",
        }
        supported_filtering_params = SUPPORTED_FILTERING_PARAMS

    @field_serializer("added", "created", "deleted_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        Serialize datetime fields to ISO format.

        Converts datetime objects to ISO 8601 formatted strings for JSON serialization.
        Returns None if the input value is None.

        Args:
            value (datetime | None): The datetime value to serialize.

        Returns:
            str | None: The serialized datetime value as an ISO 8601 string, or None.

        """
        return value.isoformat() if value else None

    @field_serializer("notes")
    def serialize_notes(self, value: list[DocumentNote]) -> list[dict[str, Any]]:
        """
        Serialize notes to a list of dictionaries.

        Converts DocumentNote objects to dictionaries for JSON serialization.
        Returns an empty list if the input value is None or empty.

        Args:
            value (list[DocumentNote]): The list of DocumentNote objects to serialize.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the notes.

        """
        return [note.to_dict() for note in value] if value else []

    @field_validator("tag_ids", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> list[int]:
        """
        Validate and convert tag IDs to a list of integers.

        Ensures tag IDs are properly formatted as a list of integers.
        Handles various input formats including None, single integers, and lists.

        Args:
            value (Any): The tag IDs to validate, which can be None, an integer, or a list.

        Returns:
            list[int]: A list of validated tag IDs.

        Raises:
            TypeError: If the input value is not None, an integer, or a list.

        Examples:
            >>> Document.validate_tags(None)
            []
            >>> Document.validate_tags(5)
            [5]
            >>> Document.validate_tags([1, 2, 3])
            [1, 2, 3]

        """
        if value is None:
            return []

        if isinstance(value, list):
            return [int(tag) for tag in value]

        if isinstance(value, int):
            return [value]

        raise TypeError(f"Invalid type for tags: {type(value)}")

    @field_validator("custom_field_dicts", mode="before")
    @classmethod
    def validate_custom_fields(cls, value: Any) -> list[CustomFieldValues]:
        """
        Validate and return custom field dictionaries.

        Ensures custom fields are properly formatted as a list of CustomFieldValues.
        Returns an empty list if the input value is None.

        Args:
            value (Any): The list of custom field dictionaries to validate.

        Returns:
            list[CustomFieldValues]: A list of validated custom field dictionaries.

        Raises:
            TypeError: If the input value is not None or a list.

        """
        if value is None:
            return []

        if isinstance(value, list):
            return value

        raise TypeError(f"Invalid type for custom fields: {type(value)}")

    @field_validator("content", "title", mode="before")
    @classmethod
    def validate_text(cls, value: Any) -> str:
        """
        Validate and return a text field.

        Ensures text fields are properly formatted as strings.
        Converts integers to strings and returns an empty string if the input value is None.

        Args:
            value (Any): The value of the text field to validate.

        Returns:
            str: The validated text value.

        Raises:
            TypeError: If the input value is not None, a string, or an integer.

        Examples:
            >>> Document.validate_text(None)
            ''
            >>> Document.validate_text("Hello")
            'Hello'
            >>> Document.validate_text(123)
            '123'

        """
        if value is None:
            return ""

        if isinstance(value, (str, int)):
            return str(value)

        raise TypeError(f"Invalid type for text: {type(value)}")

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, value: Any) -> list[Any]:
        """
        Validate and return the list of notes.

        Ensures notes are properly formatted as a list of DocumentNote objects.
        Handles various input formats including None, single DocumentNote objects, and lists.

        Args:
            value (Any): The list of notes to validate.

        Returns:
            list[Any]: The validated list of notes.

        Raises:
            TypeError: If the input value is not None, a DocumentNote, or a list.

        """
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, DocumentNote):
            return [value]

        raise TypeError(f"Invalid type for notes: {type(value)}")

    @field_validator("is_shared_by_requester", mode="before")
    @classmethod
    def validate_is_shared_by_requester(cls, value: Any) -> bool:
        """
        Validate and return the is_shared_by_requester flag.

        Ensures the is_shared_by_requester flag is properly formatted as a boolean.
        Returns False if the input value is None.

        Args:
            value (Any): The flag to validate.

        Returns:
            bool: The validated flag.

        Raises:
            TypeError: If the input value is not None or a boolean.

        """
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        raise TypeError(f"Invalid type for is_shared_by_requester: {type(value)}")

    @property
    def custom_field_ids(self) -> list[int]:
        """
        Get the IDs of the custom fields for this document.

        Returns:
            list[int]: A list of custom field IDs associated with this document.

        Example:
            >>> document = client.documents().get(1)
            >>> field_ids = document.custom_field_ids
            >>> print(field_ids)
            [1, 3, 5]

        """
        return [element.field for element in self.custom_field_dicts]

    @property
    def custom_field_values(self) -> list[Any]:
        """
        Get the values of the custom fields for this document.

        Returns:
            list[Any]: A list of values for the custom fields associated with this document.

        Example:
            >>> document = client.documents().get(1)
            >>> values = document.custom_field_values
            >>> print(values)
            ['2023-01-15', 'INV-12345', True]

        """
        return [element.value for element in self.custom_field_dicts]

    @property
    def tag_names(self) -> list[str]:
        """
        Get the names of the tags for this document.

        Returns:
            list[str]: A list of tag names associated with this document.

        Example:
            >>> document = client.documents().get(1)
            >>> names = document.tag_names
            >>> print(names)
            ['Invoice', 'Tax', 'Important']

        """
        return [tag.name for tag in self.tags if tag.name]

    @property
    def tags(self) -> TagQuerySet:
        """
        Get the tags for this document.

        Returns a QuerySet of Tag objects associated with this document.
        The QuerySet is lazily loaded, so API requests are only made when
        the tags are actually accessed.

        Returns:
            TagQuerySet: QuerySet of tags associated with this document.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> for tag in document.tags:
            ...     print(f'{tag.name} # {tag.id}')
            Tag 1 # 1
            Tag 2 # 2
            Tag 3 # 3

            >>> if 5 in document.tags:
            ...     print('Tag ID #5 is associated with this document')

            >>> tag = client.tags().get(pk=1)
            >>> if tag in document.tags:
            ...     print('Tag ID #1 is associated with this document')

            >>> filtered_tags = document.tags.filter(name__icontains='example')
            >>> for tag in filtered_tags:
            ...     print(f'{tag.name} # {tag.id}')

        """
        if not self.tag_ids:
            return self._client.tags().none()

        # Use the API's filtering capability to get only the tags with specific IDs
        # The paperless-ngx API supports id__in filter for retrieving multiple objects by ID
        return self._client.tags().id(self.tag_ids)

    @tags.setter
    def tags(self, value: "Iterable[Tag | int] | None") -> None:
        """
        Set the tags for this document.

        Updates the document's tag_ids list based on the provided tags.
        Accepts None (to clear all tags), an iterable of Tag objects,
        or an iterable of tag IDs.

        Args:
            value (Iterable[Tag | int] | None): The tags to set. Can be None, an iterable of Tag objects,
                  or an iterable of tag IDs.

        Raises:
            TypeError: If the input value is not None, an iterable of Tag objects,
                      or an iterable of integers.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set tags by ID
            >>> document.tags = [1, 2, 3]
            >>> # Set tags by Tag objects
            >>> document.tags = client.tags().filter(name__icontains='invoice')
            >>> # Clear all tags
            >>> document.tags = None

        """
        if value is None:
            self.tag_ids = []
            return

        if isinstance(value, Iterable):
            # Reset tag_ids to ensure we only have the new values
            self.tag_ids = []
            for tag in value:
                if isinstance(tag, int):
                    self.tag_ids.append(tag)
                    continue

                # Check against StandardModel to avoid circular imports
                # If it is another type of standard model, pydantic validators will complain
                if isinstance(tag, StandardModel):
                    self.tag_ids.append(tag.id)
                    continue

                raise TypeError(f"Invalid type for tags: {type(tag)}")
            return

        raise TypeError(f"Invalid type for tags: {type(value)}")

    @property
    def correspondent(self) -> "Correspondent | None":
        """
        Get the correspondent for this document.

        Retrieves the Correspondent object associated with this document.
        Uses caching to minimize API requests when accessing the same correspondent
        multiple times.

        Returns:
            Correspondent | None: The correspondent object or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> if document.correspondent:
            ...     print(document.correspondent.name)
            Example Correspondent

        """
        # Return cache
        if self._correspondent is not None:
            pk, value = self._correspondent
            if pk == self.correspondent_id:
                return value

        # None set to retrieve
        if not self.correspondent_id:
            return None

        # Retrieve it
        correspondent = self._client.correspondents().get(self.correspondent_id)
        self._correspondent = (self.correspondent_id, correspondent)
        return correspondent

    @correspondent.setter
    def correspondent(self, value: "Correspondent | int | None") -> None:
        """
        Set the correspondent for this document.

        Updates the document's correspondent_id based on the provided correspondent.
        Accepts None (to clear the correspondent), a Correspondent object,
        or a correspondent ID.

        Args:
            value (Correspondent | int | None): The correspondent to set. Can be None, a Correspondent object,
                  or a correspondent ID.

        Raises:
            TypeError: If the input value is not None, a Correspondent object,
                      or an integer.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set correspondent by ID
            >>> document.correspondent = 5
            >>> # Set correspondent by object
            >>> document.correspondent = client.correspondents().get(5)
            >>> # Clear correspondent
            >>> document.correspondent = None

        """
        if value is None:
            # Leave cache in place in case it changes again
            self.correspondent_id = None
            return

        if isinstance(value, int):
            # Leave cache in place in case id is the same, or id changes again
            self.correspondent_id = value
            return

        # Check against StandardModel to avoid circular imports
        # If it is another type of standard model, pydantic validators will complain
        if isinstance(value, StandardModel):
            self.correspondent_id = value.id
            # Pre-populate the cache
            self._correspondent = (value.id, value)
            return

        raise TypeError(f"Invalid type for correspondent: {type(value)}")

    @property
    def document_type(self) -> "DocumentType | None":
        """
        Get the document type for this document.

        Retrieves the DocumentType object associated with this document.
        Uses caching to minimize API requests when accessing the same document type
        multiple times.

        Returns:
            DocumentType | None: The document type object or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> if document.document_type:
            ...     print(document.document_type.name)
            Example Document Type

        """
        # Return cache
        if self._document_type is not None:
            pk, value = self._document_type
            if pk == self.document_type_id:
                return value

        # None set to retrieve
        if not self.document_type_id:
            return None

        # Retrieve it
        document_type = self._client.document_types().get(self.document_type_id)
        self._document_type = (self.document_type_id, document_type)
        return document_type

    @document_type.setter
    def document_type(self, value: "DocumentType | int | None") -> None:
        """
        Set the document type for this document.

        Updates the document's document_type_id based on the provided document type.
        Accepts None (to clear the document type), a DocumentType object,
        or a document type ID.

        Args:
            value (DocumentType | int | None): The document type to set. Can be None, a DocumentType object,
                  or a document type ID.

        Raises:
            TypeError: If the input value is not None, a DocumentType object,
                      or an integer.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set document type by ID
            >>> document.document_type = 3
            >>> # Set document type by object
            >>> document.document_type = client.document_types().get(3)
            >>> # Clear document type
            >>> document.document_type = None

        """
        if value is None:
            # Leave cache in place in case it changes again
            self.document_type_id = None
            return

        if isinstance(value, int):
            # Leave cache in place in case id is the same, or id changes again
            self.document_type_id = value
            return

        # Check against StandardModel to avoid circular imports
        # If it is another type of standard model, pydantic validators will complain
        if isinstance(value, StandardModel):
            self.document_type_id = value.id
            # Pre-populate the cache
            self._document_type = (value.id, value)
            return

        raise TypeError(f"Invalid type for document_type: {type(value)}")

    @property
    def storage_path(self) -> "StoragePath | None":
        """
        Get the storage path for this document.

        Retrieves the StoragePath object associated with this document.
        Uses caching to minimize API requests when accessing the same storage path
        multiple times.

        Returns:
            StoragePath | None: The storage path object or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> if document.storage_path:
            ...     print(document.storage_path.name)
            Example Storage Path

        """
        # Return cache
        if self._storage_path is not None:
            pk, value = self._storage_path
            if pk == self.storage_path_id:
                return value

        # None set to retrieve
        if not self.storage_path_id:
            return None

        # Retrieve it
        storage_path = self._client.storage_paths().get(self.storage_path_id)
        self._storage_path = (self.storage_path_id, storage_path)
        return storage_path

    @storage_path.setter
    def storage_path(self, value: "StoragePath | int | None") -> None:
        """
        Set the storage path for this document.

        Updates the document's storage_path_id based on the provided storage path.
        Accepts None (to clear the storage path), a StoragePath object,
        or a storage path ID.

        Args:
            value (StoragePath | int | None): The storage path to set. Can be None, a StoragePath object,
                  or a storage path ID.

        Raises:
            TypeError: If the input value is not None, a StoragePath object,
                      or an integer.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set storage path by ID
            >>> document.storage_path = 2
            >>> # Set storage path by object
            >>> document.storage_path = client.storage_paths().get(2)
            >>> # Clear storage path
            >>> document.storage_path = None

        """
        if value is None:
            # Leave cache in place in case it changes again
            self.storage_path_id = None
            return

        if isinstance(value, int):
            # Leave cache in place in case id is the same, or id changes again
            self.storage_path_id = value
            return

        # Check against StandardModel to avoid circular imports
        # If it is another type of standard model, pydantic validators will complain
        if isinstance(value, StandardModel):
            self.storage_path_id = value.id
            # Pre-populate the cache
            self._storage_path = (value.id, value)
            return

        raise TypeError(f"Invalid type for storage_path: {type(value)}")

    @property
    def custom_fields(self) -> "CustomFieldQuerySet":
        """
        Get the custom fields for this document.

        Returns a QuerySet of CustomField objects associated with this document.
        The QuerySet is lazily loaded, so API requests are only made when
        the custom fields are actually accessed.

        Returns:
            CustomFieldQuerySet: QuerySet of custom fields associated with this document.

        Example:
            >>> document = client.documents().get(1)
            >>> for field in document.custom_fields:
            ...     print(f'{field.name}: {field.value}')
            Due Date: 2023-04-15
            Reference: INV-12345

        """
        if not self.custom_field_dicts:
            return self._client.custom_fields().none()

        # Use the API's filtering capability to get only the custom fields with specific IDs
        # The paperless-ngx API supports id__in filter for retrieving multiple objects by ID
        return self._client.custom_fields().id(self.custom_field_ids)

    @custom_fields.setter
    def custom_fields(self, value: "Iterable[CustomField | CustomFieldValues | CustomFieldTypedDict] | None") -> None:
        """
        Set the custom fields for this document.

        Updates the document's custom_field_dicts list based on the provided custom fields.
        Accepts None (to clear all custom fields), an iterable of CustomField objects,
        CustomFieldValues objects, or dictionaries with field and value keys.

        Args:
            value (Iterable[CustomField | CustomFieldValues | CustomFieldTypedDict] | None): The custom fields to set.
                Can be None, an iterable of CustomField objects, CustomFieldValues objects, or dictionaries.

        Raises:
            TypeError: If the input value is not None, an iterable of CustomField objects,
                      CustomFieldValues objects, or dictionaries.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set custom fields by dictionary
            >>> document.custom_fields = [{'field': 1, 'value': '2023-04-15'}, {'field': 2, 'value': 'INV-12345'}]
            >>> # Set custom fields by CustomField objects
            >>> document.custom_fields = client.custom_fields().filter(name__icontains='date')
            >>> # Clear all custom fields
            >>> document.custom_fields = None

        """
        if value is None:
            self.custom_field_dicts = []
            return

        if isinstance(value, Iterable):
            new_list: list[CustomFieldValues] = []
            for field in value:
                if isinstance(field, CustomFieldValues):
                    new_list.append(field)
                    continue

                # isinstance(field, CustomField)
                # Check against StandardModel (instead of CustomField) to avoid circular imports
                # If it is the wrong type of standard model (e.g. a User), pydantic validators will complain
                if isinstance(field, StandardModel):
                    new_list.append(CustomFieldValues(field=field.id, value=getattr(field, "value")))
                    continue

                if isinstance(field, dict):
                    new_list.append(CustomFieldValues(**field))
                    continue

                raise TypeError(f"Invalid type for custom fields: {type(field)}")

            self.custom_field_dicts = new_list
            return

        raise TypeError(f"Invalid type for custom fields: {type(value)}")

    @property
    def has_search_hit(self) -> bool:
        """
        Check if this document has search hit information.

        Returns:
            bool: True if this document was returned as part of a search result
                 and has search hit information, False otherwise.

        """
        return self.__search_hit__ is not None

    @property
    def search_hit(self) -> dict[str, Any] | None:
        """
        Get the search hit information for this document.

        When a document is returned as part of a search result, this property
        contains additional information about the search match.

        Returns:
            dict[str, Any] | None: Dictionary with search hit information or None
                                  if this document was not part of a search result.

        """
        return self.__search_hit__

    def custom_field_value(self, field_id: int, default: Any = None, *, raise_errors: bool = False) -> Any:
        """
        Get the value of a custom field by ID.

        Retrieves the value of a specific custom field associated with this document.

        Args:
            field_id (int): The ID of the custom field to retrieve.
            default (Any, optional): The value to return if the field is not found. Defaults to None.
            raise_errors (bool, optional): Whether to raise an error if the field is not found. Defaults to False.

        Returns:
            Any: The value of the custom field or the default value if not found.

        Raises:
            ValueError: If raise_errors is True and the field is not found.

        Example:
            >>> document = client.documents().get(1)
            >>> # Get value with default
            >>> due_date = document.custom_field_value(3, default="Not set")
            >>> # Get value with error handling
            >>> try:
            ...     reference = document.custom_field_value(5, raise_errors=True)
            ... except ValueError:
            ...     print("Reference field not found")
            Reference field not found

        """
        for field in self.custom_field_dicts:
            if field.field == field_id:
                return field.value

        if raise_errors:
            raise ValueError(f"Custom field {field_id} not found")
        return default

    """
    def __getattr__(self, name: str) -> Any:
        # Allow easy access to custom fields
        for custom_field in self.custom_fields:
            if custom_field['field'] == name:
                return custom_field['value']

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    """

    def add_tag(self, tag: "Tag | int | str") -> None:
        """
        Add a tag to the document.

        Adds a tag to the document's tag_ids list. The tag can be specified as a Tag object,
        a tag ID, or a tag name. If a tag name is provided, the method will look up the
        corresponding tag ID.

        Args:
            tag (Tag | int | str): The tag to add. Can be a Tag object, a tag ID, or a tag name.

        Raises:
            TypeError: If the input value is not a Tag object, an integer, or a string.
            ResourceNotFoundError: If a tag name is provided but no matching tag is found.

        Example:
            >>> document = client.documents().get(1)
            >>> # Add tag by ID
            >>> document.add_tag(5)
            >>> # Add tag by object
            >>> tag = client.tags().get(3)
            >>> document.add_tag(tag)
            >>> # Add tag by name
            >>> document.add_tag("Invoice")

        """
        if isinstance(tag, int):
            self.tag_ids.append(tag)
            return

        if isinstance(tag, StandardModel):
            self.tag_ids.append(tag.id)
            return

        if isinstance(tag, str):
            if not (instance := self._client.tags().filter(name=tag).first()):
                raise ResourceNotFoundError(f"Tag '{tag}' not found")
            self.tag_ids.append(instance.id)
            return

        raise TypeError(f"Invalid type for tag: {type(tag)}")

    def remove_tag(self, tag: "Tag | int | str") -> None:
        """
        Remove a tag from the document.

        Removes a tag from the document's tag_ids list. The tag can be specified as a Tag object,
        a tag ID, or a tag name. If a tag name is provided, the method will look up the
        corresponding tag ID.

        Args:
            tag (Tag | int | str): The tag to remove. Can be a Tag object, a tag ID, or a tag name.

        Raises:
            TypeError: If the input value is not a Tag object, an integer, or a string.
            ResourceNotFoundError: If a tag name is provided but no matching tag is found.
            ValueError: If the tag is not associated with this document.

        Example:
            >>> document = client.documents().get(1)
            >>> # Remove tag by ID
            >>> document.remove_tag(5)
            >>> # Remove tag by object
            >>> tag = client.tags().get(3)
            >>> document.remove_tag(tag)
            >>> # Remove tag by name
            >>> document.remove_tag("Invoice")

        """
        if isinstance(tag, int):
            # TODO: Handle removal with consideration of "tags can't be empty" rule in paperless
            self.tag_ids.remove(tag)
            return

        if isinstance(tag, StandardModel):
            # TODO: Handle removal with consideration of "tags can't be empty" rule in paperless
            self.tag_ids.remove(tag.id)
            return

        if isinstance(tag, str):
            # TODO: Handle removal with consideration of "tags can't be empty" rule in paperless
            if not (instance := self._client.tags().filter(name=tag).first()):
                raise ResourceNotFoundError(f"Tag '{tag}' not found")
            self.tag_ids.remove(instance.id)
            return

        raise TypeError(f"Invalid type for tag: {type(tag)}")

    def set_custom_field(self, field: str | int, value: Any) -> None:
        """
        Set a custom field value for this document.

        Sets the value of a custom field for this document. The field can be specified
        as a CustomField object, a field ID, or a field name. If a field name is provided,
        the method will look up the corresponding field ID.

        Args:
            field (str | int): The field to set. Can be a CustomField object, a field ID, or a field name.
            value (Any): The value to set for the custom field.

        Raises:
            TypeError: If the input value is not a CustomField object, an integer, or a string.
            ResourceNotFoundError: If a field name is provided but no matching field is found.

        Example:
            >>> document = client.documents().get(1)
            >>> # Set custom field by ID
            >>> document.set_custom_field(5, "2023-04-15")
            >>> # Set custom field by object
            >>> field = client.custom_fields().get(3)
            >>> document.set_custom_field(field, "INV-12345")
            >>> # Set custom field by name
            >>> document.set_custom_field("Due Date", "2023-04-15")

        """
        if isinstance(field, int):
            # Check if document already has that field
            for custom_field in self.custom_field_dicts:
                if custom_field.field == field:
                    custom_field.value = value
                    return

            # If not, add it
            self.custom_field_dicts.append(CustomFieldValues(field=field, value=value))
            return

        if isinstance(field, str):
            if not (instance := self._client.custom_fields(name=field).first()):
                raise ResourceNotFoundError(f"Custom field '{field}' not found")

            for custom_field in self.custom_field_dicts:
                if custom_field.field == instance.id:
                    custom_field.value = value
                    return

            self.custom_field_dicts.append(CustomFieldValues(field=instance.id, value=value))
            return

        raise TypeError(f"Invalid type for custom field: {type(field)}")

    def get_metadata(self) -> "DocumentMetadata":
        """
        Get the metadata for this document.

        Retrieves detailed metadata about the document from the Paperless-ngx API.
        This includes information like the original file format, creation date,
        modification date, and other technical details.

        Returns:
            DocumentMetadata: The document metadata object.

        Examples:
            >>> metadata = document.get_metadata()
            >>> print(metadata.original_mime_type)
            application/pdf
            >>> print(metadata.media_filename)
            document.pdf

        """
        return self._client.document_metadata.get_metadata(self.id)

    def download(self, original: bool = False) -> "DownloadedDocument":
        """
        Download the document file.

        Downloads either the archived version (default) or the original version
        of the document from the Paperless-ngx server.

        Args:
            original (bool, optional): Whether to download the original file instead of the archived version.
                     Defaults to False (download the archived version).

        Returns:
            DownloadedDocument: An object containing the downloaded document content
                               and metadata.

        Examples:
            >>> # Download archived version
            >>> download = document.download()
            >>> with open(download.disposition_filename, 'wb') as f:
            ...     f.write(download.content)

            >>> # Download original version
            >>> original = document.download(original=True)
            >>> print(f"Downloaded {len(original.content)} bytes")
            Downloaded 245367 bytes

        """
        return self._client.downloaded_documents.download_document(self.id, original)

    def preview(self, original: bool = False) -> "DownloadedDocument":
        """
        Get a preview of the document.

        Retrieves a preview version of the document from the Paperless-ngx server.
        This is typically a web-friendly version (e.g., PDF) that can be displayed
        in a browser.

        Args:
            original (bool, optional): Whether to preview the original file instead of the archived version.
                     Defaults to False (preview the archived version).

        Returns:
            DownloadedDocument: An object containing the preview document content
                               and metadata.

        Example:
            >>> preview = document.preview()
            >>> with open('preview.pdf', 'wb') as f:
            ...     f.write(preview.content)

        """
        return self._client.downloaded_documents.download_preview(self.id, original)

    def thumbnail(self, original: bool = False) -> "DownloadedDocument":
        """
        Get the document thumbnail.

        Retrieves a thumbnail image of the document from the Paperless-ngx server.
        This is typically a small image representation of the first page.

        Args:
            original (bool, optional): Whether to get the thumbnail of the original file instead of
                     the archived version. Defaults to False (get thumbnail of archived version).

        Returns:
            DownloadedDocument: An object containing the thumbnail image content
                               and metadata.

        Example:
            >>> thumbnail = document.thumbnail()
            >>> with open('thumbnail.png', 'wb') as f:
            ...     f.write(thumbnail.content)

        """
        return self._client.downloaded_documents.download_thumbnail(self.id, original)

    def get_suggestions(self) -> "DocumentSuggestions":
        """
        Get suggestions for this document.

        Retrieves AI-generated suggestions for document metadata from the Paperless-ngx server.
        This can include suggested tags, correspondent, document type, and other metadata
        based on the document's content.

        Returns:
            DocumentSuggestions: An object containing suggested metadata for the document.

        Examples:
            >>> suggestions = document.get_suggestions()
            >>> print(f"Suggested tags: {suggestions.tags}")
            Suggested tags: [{'name': 'Invoice', 'score': 0.95}, {'name': 'Utility', 'score': 0.87}]
            >>> print(f"Suggested correspondent: {suggestions.correspondent}")
            Suggested correspondent: {'name': 'Electric Company', 'score': 0.92}
            >>> print(f"Suggested document type: {suggestions.document_type}")
            Suggested document type: {'name': 'Bill', 'score': 0.89}

        """
        return self._client.document_suggestions.get_suggestions(self.id)

    def append_content(self, value: str) -> None:
        """
        Append content to the document.

        Adds the specified text to the end of the document's content,
        separated by a newline.

        Args:
            value (str): The content to append.

        Example:
            >>> document = client.documents().get(1)
            >>> document.append_content("Additional notes about this document")
            >>> document.save()

        """
        self.content = f"{self.content}\n{value}"

    @override
    def update_locally(self, from_db: bool | None = None, **kwargs: Any) -> None:
        """
        Update the document locally with the provided data.

        Updates the document's attributes with the provided data without sending
        an API request. Handles special cases for notes and tags, which cannot be
        set to None in Paperless-ngx if they already have values.

        Args:
            from_db (bool | None, optional): Whether the update is coming from the database. If True,
                    bypasses certain validation checks. Defaults to None.
            **kwargs: Additional data to update the document with.

        Raises:
            NotImplementedError: If attempting to set notes or tags to None when
                                they are not already None and from_db is False.

        Example:
            >>> document = client.documents().get(1)
            >>> document.update_locally(title="New Title", correspondent_id=5)
            >>> document.save()

        """
        if not from_db:
            # Paperless does not support setting notes or tags to None if not already None
            fields = ["notes", "tag_ids"]
            for field in fields:
                original = self._original_data[field]
                if original and field in kwargs and not kwargs.get(field):
                    raise NotImplementedError(f"Cannot set {field} to None. {field} currently: {original}")

            # Handle aliases
            if self._original_data["tag_ids"] and "tags" in kwargs and not kwargs.get("tags"):
                raise NotImplementedError(f"Cannot set tags to None. Tags currently: {self._original_data['tag_ids']}")

        return super().update_locally(from_db=from_db, **kwargs)
