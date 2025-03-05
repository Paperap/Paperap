"""




----------------------------------------------------------------------------

   METADATA:

       File:    document_type.py
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

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.abstract.model import PaperlessModel


class DocumentType(PaperlessModel):
    """
    Represents a document type in Paperless-NgX.
    """

    name: str
    slug: str
    match: str
    matching_algorithm: int
    is_insensitive: bool = True
    document_count: int = 0
    owner : int | None = None
    user_can_change : bool = True

    class Meta(PaperlessModel.Meta):
        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
