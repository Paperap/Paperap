

from __future__ import annotations

from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.resources.base import BaseResource, BulkEditing, StandardResource


class StoragePathResource(StandardResource[StoragePath, StoragePathQuerySet], BulkEditing):
    """Resource for managing storage paths."""

    model_class = StoragePath
    queryset_class = StoragePathQuerySet
    name: str = "storage_paths"
