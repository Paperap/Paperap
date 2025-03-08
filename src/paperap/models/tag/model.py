"""




----------------------------------------------------------------------------

   METADATA:

       File:    tag.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel
from paperap.models.tag.queryset import TagQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class Tag(StandardModel):
    """
    Represents a tag in Paperless-NgX.
    """

    name: str
    slug: str
    colour: str = Field(alias="color")
    match: str
    matching_algorithm: int
    is_insensitive: bool
    is_inbox_tag: bool
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool

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
