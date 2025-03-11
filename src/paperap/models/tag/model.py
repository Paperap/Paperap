"""
----------------------------------------------------------------------------

   METADATA:

       File:    tag.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field, field_validator

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
    colour: str | None = Field(alias="color", default=None)
    is_inbox_tag: bool | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = TagQuerySet

    @classmethod
    @field_validator("colour", mode="before")
    def validate_colour(cls, value: str | int | None) -> str | None:
        if value is None:
            return None
        return str(value)

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents with this tag.

        Returns:
            List of documents.

        """
        return self._client.documents().all().tag_id(self.id)
