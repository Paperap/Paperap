"""
----------------------------------------------------------------------------

   METADATA:

       File:    tag.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.10
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field, field_validator, model_validator

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.mixins.models import MatcherMixin
from paperap.models.tag.queryset import TagQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class Tag(StandardModel, MatcherMixin):
    """
    Represents a tag in Paperless-NgX.
    """

    name: str | None = None
    slug: str | None = None
    colour: str | int | None = Field(alias="color", default=None)
    is_inbox_tag: bool | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_text_color_alias(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Handle 'text_color' as an alias for 'colour'."""
        if isinstance(data, dict) and "text_color" in data and data.get("colour") is None and data.get("color") is None:
            data["colour"] = data.pop("text_color")
        return data

    # Alias for colour
    @property
    def color(self) -> str | int | None:
        """Alias for colour field."""
        return self.colour

    @color.setter
    def color(self, value: str | int | None) -> None:
        """Setter for colour field."""
        self.colour = value

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = TagQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents with this tag.

        Returns:
            List of documents.

        """
        return self._client.documents().all().tag_id(self.id)
