"""




----------------------------------------------------------------------------

   METADATA:

       File:    storage_path.py
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
from typing import Any

from paperap.models.abstract.model import PaperlessModel
from paperap.models.storage_path.queryset import StoragePathQuerySet


class StoragePath(PaperlessModel):
    """
    Represents a storage path in Paperless-NgX.
    """

    name: str
    slug: str
    path: str = "{{ created_year }}/{{ correspondent }}/{{ title }}"
    match: str = ".*"
    matching_algorithm: int = 0
    is_insensitive: bool = True
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool = True

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = StoragePathQuerySet
