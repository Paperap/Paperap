"""




----------------------------------------------------------------------------

   METADATA:

       File:    storage_path.py
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
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.model import StandardModel
from paperap.models.storage_path.queryset import StoragePathQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class StoragePath(StandardModel):
    """
    Represents a storage path in Paperless-NgX.
    """

    name: str
    slug: str | None = None
    path: str | None = None
    match: str | None = None
    matching_algorithm: int | None = None
    is_insensitive: bool
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = StoragePathQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents in this storage path.
        """
        return self._client.documents().all().storage_path_id(self.id)
