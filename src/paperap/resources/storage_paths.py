"""




----------------------------------------------------------------------------

   METADATA:

       File:    storage_paths.py
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

from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class StoragePathResource(StandardResource[StoragePath, StoragePathQuerySet]):
    """Resource for managing storage paths."""

    model_class = StoragePath
    name = "storage_paths"
