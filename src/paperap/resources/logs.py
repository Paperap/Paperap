"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    logs.py                                                                                              *
*        Project: resources                                                                                            *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from typing import Any, Dict, List, Optional

from paperap.models.log import Log
from paperap.resources.base import PaperlessResource


class LogResource(PaperlessResource[Log]):
    """Resource for managing logs."""

    model_class = Log

    def create(self, data: dict[str, Any]) -> Log:
        """
        Create is not supported for logs as they are read-only.

        Raises:
            NotImplementedError: This operation is not supported.
        """
        raise NotImplementedError("Creating logs is not supported")

    def update(self, resource_id: int, data: dict[str, Any]) -> Log:
        """
        Update is not supported for logs as they are read-only.

        Raises:
            NotImplementedError: This operation is not supported.
        """
        raise NotImplementedError("Updating logs is not supported")

    def delete(self, resource_id: int) -> None:
        """
        Delete is not supported for logs as they are read-only.

        Raises:
            NotImplementedError: This operation is not supported.
        """
        raise NotImplementedError("Deleting logs is not supported")
