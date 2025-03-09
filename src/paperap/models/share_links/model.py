"""




----------------------------------------------------------------------------

   METADATA:

       File:    share_links.py
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

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from pydantic import Field, field_serializer
from yarl import URL

from paperap.models.abstract.model import StandardModel
from paperap.models.share_links.queryset import ShareLinksQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag
    from paperap.models.document import Document


class ShareLinks(StandardModel):
    expiration: datetime | None = None
    slug: str | None = None
    document: int | None = None
    created: datetime | None = Field(description="Creation timestamp", default=None, alias="created_on")
    file_version: str | None = None

    class Meta(StandardModel.Meta):
        queryset = ShareLinksQuerySet

    @field_serializer("expiration", "created")
    def serialize_datetime(self, value: datetime | None, _info):
        return value.isoformat() if value else None

    def get_document(self) -> "Document":
        if not self.document:
            raise ValueError("Document ID not set")
        return self._client.documents().get(id=self.document)
