"""




----------------------------------------------------------------------------

   METADATA:

       File:    share_links.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
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

from yarl import URL

from paperap.models.abstract.model import PaperlessModel
from paperap.models.share_links.queryset import ShareLinksQuerySet

if TYPE_CHECKING:
    from paperap.models.correspondent import Correspondent
    from paperap.models.document_type import DocumentType
    from paperap.models.storage_path import StoragePath
    from paperap.models.tag import Tag


class ShareLinks(PaperlessModel):
    expiration: datetime | None = None
    slug: str
    document: int
    file_version: str = "original"

    class Meta(PaperlessModel.Meta):
        queryset = ShareLinksQuerySet
