

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
    """

    name: str
    data_type: CustomFieldTypes | None = None

    @field_validator("data_type", mode="before")
    @classmethod
    def validate_data_type(cls, v: Any) -> CustomFieldTypes | None:
        """
        Validate the data_type field.

        Args:
            v: The value to validate.

        Returns:
            The validated value.

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
        # Fields that should not be modified
        read_only_fields = {"slug"}

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents with this custom field.
        """
        return self._client.documents().all().has_custom_field_id(self.id)
