from __future__ import annotations

from paperap.models.share_links import ShareLinks
from paperap.resources.base import PaperlessResource


class ShareLinksResource(PaperlessResource[ShareLinks]):
    """Resource for managing share links."""

    model_class = ShareLinks
