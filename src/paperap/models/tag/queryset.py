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

from typing import Any, List, Self, Union, Optional, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.models.tag.model import Tag

logger = logging.getLogger(__name__)


class TagQuerySet(QuerySet["Tag"]):
    """
    QuerySet for Paperless-ngx tags with specialized filtering methods.
    """

    def with_ids(self, ids: List[int]) -> Self:
        """
        Filter tags by multiple IDs.

        Args:
            ids: List of tag IDs to filter by

        Returns:
            Filtered TagQuerySet
        """
        ids_param = ",".join(str(id) for id in ids)
        return self.filter(id__in=ids_param)

    def with_name(self, name: str, exact: bool = True) -> Self:
        """
        Filter tags by name.

        Args:
            name: The tag name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered TagQuerySet
        """
        if exact:
            return self.filter(name=name)
        return self.filter(name__contains=name)

    def with_color(self, color: str) -> Self:
        """
        Filter tags by color.

        Args:
            color: The color code to filter by

        Returns:
            Filtered TagQuerySet
        """
        return self.filter(color=color)

    def is_inbox_tag(self, inbox: bool = True) -> Self:
        """
        Filter tags by inbox status.

        Args:
            inbox: If True, get inbox tags, otherwise non-inbox tags

        Returns:
            Filtered TagQuerySet
        """
        return self.filter(is_inbox_tag=inbox)
