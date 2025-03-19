"""




----------------------------------------------------------------------------

METADATA:

File:    queryset.py
Project: paperap
Created: 2025-03-18
Version: 0.0.8
Author:  Jess Mann
Email:   jess@jmann.me
Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.document.suggestions.model import DocumentSuggestions

logger = logging.getLogger(__name__)


class DocumentSuggestionsQuerySet(StandardQuerySet["DocumentSuggestions"]):
    pass
