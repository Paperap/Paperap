

from __future__ import annotations

from paperap.models.correspondent import Correspondent, CorrespondentQuerySet
from paperap.resources.base import BaseResource, BulkEditing, StandardResource


class CorrespondentResource(StandardResource[Correspondent, CorrespondentQuerySet], BulkEditing):
    """Resource for managing correspondents."""

    model_class = Correspondent
    queryset_class = CorrespondentQuerySet
    name: str = "correspondents"
