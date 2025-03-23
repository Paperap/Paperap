

from __future__ import annotations

from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.base import BaseResource, BulkEditing, StandardResource


class TagResource(StandardResource[Tag, TagQuerySet], BulkEditing):
    """Resource for managing tags."""

    model_class = Tag
    queryset_class = TagQuerySet
    name: str = "tags"
