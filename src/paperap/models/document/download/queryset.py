

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.download.model import DownloadedDocument

logger = logging.getLogger(__name__)


class DownloadedDocumentQuerySet(StandardQuerySet["DownloadedDocument"]):
    pass
