

from __future__ import annotations

from paperap.models.share_links import ShareLinks, ShareLinksQuerySet
from paperap.resources.base import BaseResource, StandardResource


class ShareLinksResource(StandardResource[ShareLinks, ShareLinksQuerySet]):
    """Resource for managing share links."""

    model_class = ShareLinks
    queryset_class = ShareLinksQuerySet
    name: str = "share_links"
