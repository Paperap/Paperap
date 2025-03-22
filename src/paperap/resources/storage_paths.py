"""
----------------------------------------------------------------------------

   METADATA:

       File:    storage_paths.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.resources.base import BaseResource, BulkEditing, StandardResource


class StoragePathResource(StandardResource[StoragePath, StoragePathQuerySet], BulkEditing):
    """Resource for managing storage paths."""

    model_class = StoragePath
    queryset_class = StoragePathQuerySet
    name: str = "storage_paths"
