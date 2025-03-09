"""




----------------------------------------------------------------------------

   METADATA:

       File:    share_links.py
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

from paperap.models.share_links import ShareLinks, ShareLinksQuerySet
from paperap.resources.base import PaperlessResource, StandardResource


class ShareLinksResource(StandardResource[ShareLinks, ShareLinksQuerySet]):
    """Resource for managing share links."""

    model_class = ShareLinks
    name = "share_links"
