from __future__ import annotations

from paperap.models.storage_path import StoragePath
from paperap.resources.base import PaperlessResource


class StoragePathResource(PaperlessResource[StoragePath]):
    """Resource for managing storage paths."""

    model_class = StoragePath
