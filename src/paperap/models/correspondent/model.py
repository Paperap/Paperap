"""
----------------------------------------------------------------------------

   METADATA:

       File:    correspondent.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.5
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.correspondent.queryset import CorrespondentQuerySet
from paperap.models.mixins.models import MatcherMixin

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class Correspondent(StandardModel, MatcherMixin):
    """
    Represents a correspondent in Paperless-NgX.
    """

    slug: str | None = None
    name: str | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        # Fields that should not be modified
        read_only_fields = {
            "slug",
            "document_count",
        }
        queryset = CorrespondentQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get documents for this correspondent.
        """
        return self._client.documents().all().correspondent_id(self.id)
