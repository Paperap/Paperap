"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    storage_paths.py                                                                                     *
*        Project: resources                                                                                            *
*        Created: 2025-03-03                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-03     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from paperap.models.storage_path import StoragePath
from paperap.resources.base import PaperlessResource


class StoragePathResource(PaperlessResource[StoragePath]):
    """Resource for managing storage paths."""

    model_class = StoragePath
