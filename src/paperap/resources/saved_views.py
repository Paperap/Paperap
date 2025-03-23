

from __future__ import annotations

from paperap.models.saved_view import SavedView, SavedViewQuerySet
from paperap.resources.base import BaseResource, StandardResource


class SavedViewResource(StandardResource[SavedView, SavedViewQuerySet]):
    """Resource for managing saved views."""

    model_class = SavedView
    queryset_class = SavedViewQuerySet
    name: str = "saved_views"
