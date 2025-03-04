from __future__ import annotations

from paperap.models.search import Search
from paperap.resources.base import PaperlessResource


class SearchResource(PaperlessResource[Search]):
    """Resource for managing searches."""

    model_class = Search
