"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    document_type.py                                                                                     *
*        Project: models                                                                                               *
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
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from paperwrap.models.base import PaperlessModel

class DocumentType(PaperlessModel):
    """
    Represents a document type in Paperless-NgX.
    """
    name: str
    slug: str
    match: str
    matching_algorithm: int
    is_insensitive: bool
    document_count: int
    
    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        
