"""




----------------------------------------------------------------------------

   METADATA:

       File:    saved_views.py
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

from __future__ import annotations

from paperap.models.saved_view import SavedView, SavedViewQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class SavedViewResource(StandardResource[SavedView, SavedViewQuerySet]):
    """Resource for managing saved views."""

    model_class = SavedView
    name = "saved_views"
