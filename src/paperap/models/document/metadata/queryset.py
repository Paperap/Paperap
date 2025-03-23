

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.metadata.model import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentMetadataQuerySet(StandardQuerySet["DocumentMetadata"]):
    pass
