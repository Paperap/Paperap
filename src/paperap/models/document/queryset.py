"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    queryset.py
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

from string import Template
from typing import Any, Generic, Iterable, Iterator, Optional, TypeVar, Union, TYPE_CHECKING
import logging
from yarl import URL
from paperap.exceptions import MultipleObjectsFoundError, ObjectNotFoundError
from paperap.models.abstract.queryset import QuerySet
from paperap.models.document.model import Document

if TYPE_CHECKING:
    from paperap.models.abstract.model import PaperlessModel
    from paperap.resources.documents import DocumentResource

_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel")

logger = logging.getLogger(__name__)

class DocumentQuerySet(QuerySet[Document]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.
    """
