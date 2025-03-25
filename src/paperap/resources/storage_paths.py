"""
Storage path resource for interacting with Paperless-NgX storage paths.

This module provides the StoragePathResource class, which is responsible for
managing storage paths in the Paperless-NgX system. It extends the functionality
of the StandardResource class to include operations specific to storage paths.

Storage paths in Paperless-NgX define where documents are physically stored in the
file system, allowing for organization of documents based on custom rules.

Example:
    To use the StoragePathResource, you can access it via the PaperlessClient::

        from paperap import PaperlessClient

        client = PaperlessClient()

        # Get all storage paths
        storage_paths = client.storage_paths.all()
        for path in storage_paths:
            print(f"{path.name}: {path.path}")

        # Create a new storage path
        new_path = client.storage_paths.create(
            name="Tax Documents",
            path="/documents/taxes/"
        )

"""

from __future__ import annotations

from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.resources.base import BaseResource, BulkEditingMixin, StandardResource


class StoragePathResource(StandardResource[StoragePath, StoragePathQuerySet], BulkEditingMixin[StoragePath]):
    """
    Resource for managing storage paths in Paperless-NgX.

    This class provides methods for interacting with the storage paths API
    endpoint, allowing for the creation, retrieval, updating, and deletion
    of storage paths within the Paperless-NgX system. Storage paths define
    where documents are physically stored in the file system.

    The StoragePathResource supports all standard CRUD operations as well as
    bulk operations inherited from the BulkEditing mixin.

    Attributes:
        model_class (Type[StoragePath]): The StoragePath model class used for
            instantiating storage path objects.
        queryset_class (Type[StoragePathQuerySet]): The StoragePathQuerySet class
            used for query operations and filtering.
        name (str): The resource name used in API endpoints ("storage_paths").

    Example:
        Create a new storage path with matching rules::

            # Create a path for invoices that will store them in a dedicated folder
            new_path = client.storage_paths.create(
                name="Invoices",
                path="/documents/invoices/",
                matching_algorithm="any",  # Match any of the rules
                match="invoice,bill,receipt",
                is_insensitive=True
            )

            # Update an existing path
            path = client.storage_paths.get(5)
            path.path = "/new/path/location/"
            path.save()

            # Delete a storage path
            path.delete()

            # Bulk operations
            paths = client.storage_paths.filter(name__contains="temp")
            paths.delete()  # Delete all matching paths

    """

    model_class = StoragePath
    queryset_class = StoragePathQuerySet
    name: str = "storage_paths"
