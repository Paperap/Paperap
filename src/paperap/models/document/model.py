"""



----------------------------------------------------------------------------

METADATA:

File:    model.py
        Project: paperap
Created: 2025-03-09
        Version: 0.0.8
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-09     By Jess Mann

"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Iterable, Iterator, Optional, TypedDict, cast, override

import pydantic
from pydantic import Field, field_serializer, field_validator, model_serializer
from typing_extensions import TypeVar

from paperap.const import CustomFieldTypedDict, CustomFieldValues
from paperap.exceptions import ResourceNotFoundError
from paperap.models.abstract import FilteringStrategies, StandardModel
from paperap.models.document.queryset import DocumentQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.custom_field import CustomField, CustomFieldQuerySet
    from paperap.models.document.download import DownloadedDocument
    from paperap.models.document.metadata import DocumentMetadata
    from paperap.models.document.suggestions import DocumentSuggestions
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag, TagQuerySet
    from paperap.models.user import User

logger = logging.getLogger(__name__)


class DocumentNote(StandardModel):

    """
    Represents a note on a Paperless-NgX document.
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

        Args:
            value: The datetime value to serialize.

        Returns:
            The serialized datetime value or None if the value is None.

        """
        return value.isoformat() if value else None

    def get_document(self) -> "Document":
        """
        Get the document associated with this note.

        Returns:
            The document associated with this note.

        """
        return self._client.documents().get(self.document)

    def get_user(self) -> "User":
        """
        Get the user who created this note.

        Returns:
            The user who created this note.

        """
        return self._client.users().get(self.user)


class Document(StandardModel):

    """
    Represents a Paperless-NgX document.

    Attributes:
        added: The timestamp when the document was added to the system.
        archive_serial_number: The serial number of the archive.
        archived_file_name: The name of the archived file.
        content: The content of the document.
        correspondent: The correspondent associated with the document.
        created: The timestamp when the document was created.
        created_date: The date when the document was created.
        updated: The timestamp when the document was last updated.
        custom_fields: Custom fields associated with the document.
        deleted_at: The timestamp when the document was deleted.
        document_type: The document type associated with the document.
        is_shared_by_requester: Whether the document is shared by the requester.
        notes: Notes associated with the document.
        original_file_name: The original file name of the document.
        owner: The owner of the document.
        page_count: The number of pages in the document.
        storage_path: The storage path of the document.
        tags: The tags associated with the document.
        title: The title of the document.
        user_can_change: Whether the user can change the document.
        checksum: The checksum of the document.

    Examples:
        >>> document = client.documents().get(pk=1)
        >>> document.title = 'Example Document'
        >>> document.save()
        >>> document.title
        'Example Document'

        # Get document metadata
        >>> metadata = document.get_metadata()
        >>> print(metadata.original_mime_type)

        # Download document
        >>> download = document.download()
        >>> with open(download.disposition_filename, 'wb') as f:
        ...     f.write(download.content)

        # Get document suggestions
        >>> suggestions = document.get_suggestions()
        >>> print(suggestions.tags)

    """

    added: datetime | None = None
    archive_serial_number: int | None = None
    archived_file_name: str | None = None
    content: str = ""
    is_shared_by_requester: bool = False
    notes: "list[DocumentNote]" = Field(default_factory=list)
    original_file_name: str | None = None
    owner: int | None = None
    page_count: int | None = None
    title: str = ""
    user_can_change: bool | None = None
    checksum: str | None = None

    created: datetime | None = Field(description="Creation timestamp", default=None)
    created_date: str | None = None
    # where did this come from? It's not in sample data?
    updated: datetime | None = Field(description="Last update timestamp", default=None)
    deleted_at: datetime | None = None

    custom_field_dicts: Annotated[list[CustomFieldValues], Field(default_factory=list)]
    correspondent_id: int | None = None
    document_type_id: int | None = None
    storage_path_id: int | None = None
    tag_ids: Annotated[list[int], Field(default_factory=list)]

    _correspondent: tuple[int, Correspondent] | None = None
    _document_type: tuple[int, DocumentType] | None = None
    _storage_path: tuple[int, StoragePath] | None = None
    __search_hit__: Optional[dict[str, Any]] = None

    class Meta(StandardModel.Meta):
        # NOTE: Filtering appears to be disabled by paperless on page_count
        read_only_fields = {"page_count", "deleted_at", "updated", "is_shared_by_requester", "archived_file_name"}
        filtering_disabled = {"page_count", "deleted_at", "updated", "is_shared_by_requester"}
        filtering_strategies = {FilteringStrategies.WHITELIST}
        field_map = {
            "tags": "tag_ids",
            "custom_fields": "custom_field_dicts",
            "document_type": "document_type_id",
            "correspondent": "correspondent_id",
            "storage_path": "storage_path_id",
        }
        supported_filtering_params = {
            "id__in",
            "id",
            "title__istartswith",
            "title__iendswith",
            "title__icontains",
            "title__iexact",
            "content__istartswith",
            "content__iendswith",
            "content__icontains",
            "content__iexact",
            "archive_serial_number",
            "archive_serial_number__gt",
            "archive_serial_number__gte",
            "archive_serial_number__lt",
            "archive_serial_number__lte",
            "archive_serial_number__isnull",
            "content__contains",  # maybe?
            "correspondent__isnull",
            "correspondent__id__in",
            "correspondent__id",
            "correspondent__name__istartswith",
            "correspondent__name__iendswith",
            "correspondent__name__icontains",
            "correspondent__name__iexact",
            "correspondent__slug__iexact",  # maybe?
            "created__year",
            "created__month",
            "created__day",
            "created__date__gt",
            "created__gt",
            "created__date__lt",
            "created__lt",
            "added__year",
            "added__month",
            "added__day",
            "added__date__gt",
            "added__gt",
            "added__date__lt",
            "added__lt",
            "modified__year",
            "modified__month",
            "modified__day",
            "modified__date__gt",
            "modified__gt",
            "modified__date__lt",
            "modified__lt",
            "original_filename__istartswith",
            "original_filename__iendswith",
            "original_filename__icontains",
            "original_filename__iexact",
            "checksum__istartswith",
            "checksum__iendswith",
            "checksum__icontains",
            "checksum__iexact",
            "tags__id__in",
            "tags__id",
            "tags__name__istartswith",
            "tags__name__iendswith",
            "tags__name__icontains",
            "tags__name__iexact",
            "document_type__isnull",
            "document_type__id__in",
            "document_type__id",
            "document_type__name__istartswith",
            "document_type__name__iendswith",
            "document_type__name__icontains",
            "document_type__name__iexact",
            "storage_path__isnull",
            "storage_path__id__in",
            "storage_path__id",
            "storage_path__name__istartswith",
            "storage_path__name__iendswith",
            "storage_path__name__icontains",
            "storage_path__name__iexact",
            "owner__isnull",
            "owner__id__in",
            "owner__id",
            "is_tagged",
            "tags__id__all",
            "tags__id__none",
            "correspondent__id__none",
            "document_type__id__none",
            "storage_path__id__none",
            "is_in_inbox",
            "title_content",
            "owner__id__none",
            "custom_fields__icontains",
            "custom_fields__id__all",
            "custom_fields__id__none",  # ??
            "custom_fields__id__in",
            "custom_field_query",  # ??
            "has_custom_fields",
            "shared_by__id",
            "shared_by__id__in",
        }

    @field_serializer("added", "created", "updated", "deleted_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        Serialize datetime fields to ISO format.

        Args:
            value: The datetime value to serialize.

        Returns:
            The serialized datetime value.

        """
        return value.isoformat() if value else None

    @field_serializer("notes")
    def serialize_notes(self, value: list[DocumentNote]) -> list[dict[str, Any]]:
        """
        Serialize notes to a list of dictionaries.

        Args:
            value: The list of DocumentNote objects to serialize.

        Returns:
            A list of dictionaries representing the notes.

        """
        return [note.to_dict() for note in value] if value else []

    @field_validator("tag_ids", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> list[int]:
        """
        Validate and convert tag IDs to a list of integers.

        Args:
            value: The list of tag IDs to validate.

        Returns:
            A list of validated tag IDs.

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

        Args:
            value: The list of custom field dictionaries to validate.

        Returns:
            A list of validated custom field dictionaries.

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

        Args:
            value: The value of the text field to validate.

        Returns:
            The validated text value.

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

        Args:
            value: The list of notes to validate.

        Returns:
            The validated list of notes.

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

        Args:
            value: The flag to validate.

        Returns:
            The validated flag.

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
        """
        return [element.field for element in self.custom_field_dicts]

    @property
    def custom_field_values(self) -> list[Any]:
        """
        Get the values of the custom fields for this document.
        """
        return [element.value for element in self.custom_field_dicts]

    @property
    def tag_names(self) -> list[str]:
        """
        Get the names of the tags for this document.
        """
        return [tag.name for tag in self.tags if tag.name]

    @property
    def tags(self) -> TagQuerySet:
        """
        Get the tags for this document.

        Returns:
            List of tags associated with this document.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> for tag in document.tags:
            ...     print(f'{tag.name} # {tag.id}')
            'Tag 1 # 1'
            'Tag 2 # 2'
            'Tag 3 # 3'

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

        Args:
            value: The tags to set.

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

        Returns:
            The correspondent or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> document.correspondent.name
            'Example Correspondent'

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

        Args:
            value: The correspondent to set.

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

        Returns:
            The document type or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> document.document_type.name
            'Example Document Type

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

        Args:
            value: The document type to set.

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

        Returns:
            The storage path or None if not set.

        Examples:
            >>> document = client.documents().get(pk=1)
            >>> document.storage_path.name
            'Example Storage Path'

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

        Args:
            value: The storage path to set.

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

        Returns:
            List of custom fields associated with this document.

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

        Args:
            value: The custom fields to set.

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
        return self.__search_hit__ is not None

    @property
    def search_hit(self) -> Optional[dict[str, Any]]:
        return self.__search_hit__

    def custom_field_value(self, field_id: int, default: Any = None, *, raise_errors: bool = False) -> Any:
        """
        Get the value of a custom field by ID.

        Args:
            field_id: The ID of the custom field.
            default: The value to return if the field is not found.
            raise_errors: Whether to raise an error if the field is not found.

        Returns:
            The value of the custom field or the default value if not found.

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

        Args:
            tag: The tag to add.

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

        Args:
            tag: The tag to remove.

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

    def get_metadata(self) -> "DocumentMetadata":
        """
        Get the metadata for this document.

        Returns:
            The document metadata.

        Examples:
            >>> metadata = document.get_metadata()
            >>> print(metadata.original_mime_type)

        """
        raise NotImplementedError()

    def download(self, original: bool = False) -> "DownloadedDocument":
        """
        Download the document file.

        Args:
            original: Whether to download the original file instead of the archived version.

        Returns:
            The downloaded document.

        Examples:
            >>> download = document.download()
            >>> with open(download.disposition_filename, 'wb') as f:
            ...     f.write(download.content)

        """
        raise NotImplementedError()

    def preview(self, original: bool = False) -> "DownloadedDocument":
        """
        Get a preview of the document.

        Args:
            original: Whether to preview the original file instead of the archived version.

        Returns:
            The document preview.

        """
        raise NotImplementedError()

    def thumbnail(self, original: bool = False) -> "DownloadedDocument":
        """
        Get the document thumbnail.

        Args:
            original: Whether to get the thumbnail of the original file.

        Returns:
            The document thumbnail.

        """
        raise NotImplementedError()

    def get_suggestions(self) -> "DocumentSuggestions":
        """
        Get suggestions for this document.

        Returns:
            The document suggestions.

        Examples:
            >>> suggestions = document.get_suggestions()
            >>> print(suggestions.tags)

        """
        raise NotImplementedError()

    def append_content(self, value: str):
        """
        Append content to the document.

        Args:
            value: The content to append.

        """
        self.content = f"{self.content}\n{value}"

    @override
    def update_locally(self, from_db: bool | None = None, **kwargs: Any):
        """
        Update the document locally with the provided data.

        Args:
            from_db: Whether to update from the database.
            **kwargs: Additional data to update the document with.

        Raises:
            NotImplementedError: If attempting to set notes or tags to None when they are not already None.

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
