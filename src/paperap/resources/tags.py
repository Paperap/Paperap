"""




----------------------------------------------------------------------------

   METADATA:

       File:    tags.py
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

from paperap.models.tag import Tag, TagQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class TagResource(StandardResource[Tag, TagQuerySet]):
    """Resource for managing tags."""

    model_class = Tag
    name = "tags"
