"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    tag.py                                                                                               *
*        Project: models                                                                                               *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class Tag(PaperlessModel):
    """
    Represents a tag in Paperless-NgX.
    """

    name: str
    slug: str
    color: str
    match: str
    matching_algorithm: int
    is_insensitive: bool
    is_inbox_tag: bool = False
    document_count: int = 0

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
