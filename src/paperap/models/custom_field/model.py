"""
Module for working with custom fields in Paperless-NgX.

This module provides the CustomField model class for interacting with custom fields
in a Paperless-NgX instance. Custom fields allow users to add additional metadata
to documents beyond the standard fields provided by Paperless-NgX.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field, field_validator

from paperap.const import CustomFieldTypes
from paperap.models.abstract.model import StandardModel

if TYPE_CHECKING:
    from paperap.models.document import DocumentQuerySet


class CustomField(StandardModel):
    """
    Represents a custom field in Paperless-NgX.

    Custom fields allow adding additional metadata to documents beyond the standard
    fields provided by Paperless-NgX. Each custom field has a name, data type, and
    can be applied to multiple documents.

    Attributes:
        name: The display name of the custom field.
        data_type: The data type of the custom field (string, integer, boolean, etc.).
        extra_data: Additional data associated with the custom field.
        document_count: Number of documents using this custom field.

    Examples:
        >>> # Create a new custom field
        >>> date_field = client.custom_fields.create(
        ...     name="Due Date",
        ...     data_type="date"
        ... )
        >>>
        >>> # Set custom field on a document
        >>> doc = client.documents.get(123)
        >>> doc.custom_fields = {date_field.id: "2023-04-15"}
        >>> doc.save()

    """

    name: str
    data_type: CustomFieldTypes | None = None

    @field_validator("data_type", mode="before")
    @classmethod
    def validate_data_type(cls, v: Any) -> CustomFieldTypes | None:
        """
        Validate the data_type field.

        Converts string values to the appropriate CustomFieldTypes enum value
        and validates that the data type is supported.

        Args:
            v: The value to validate, can be a string, CustomFieldTypes enum, or None.

        Returns:
            The validated CustomFieldTypes enum value or None.

        Raises:
            ValueError: If the value is not a valid data type.

        """
        if v is None:
            return v

        if isinstance(v, CustomFieldTypes):
            return v

        if isinstance(v, str):
            try:
                # Try to convert string to enum
                return CustomFieldTypes(v)
            except (ValueError, TypeError):
                raise ValueError(f"data_type must be a valid CustomFieldTypes: {', '.join(CustomFieldTypes.__members__)}")

        return v

    extra_data: dict[str, Any] = Field(default_factory=dict)
    document_count: int = 0

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
        "extra": "allow",
    }

    class Meta(StandardModel.Meta):
        """
        Metadata for the CustomField model.

        Defines read-only fields and other metadata for the CustomField model.

        Attributes:
            read_only_fields: Set of field names that should not be modified by the client.

        """

        # Fields that should not be modified
        read_only_fields = {"slug"}

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents that have this custom field.

        Returns:
            A DocumentQuerySet containing all documents that have this custom field.

        Examples:
            >>> # Get all documents with a specific custom field
            >>> field = client.custom_fields.get(5)
            >>> for doc in field.documents:
            ...     print(doc.title)

        """
        return self._client.documents().all().has_custom_field_id(self.id)
