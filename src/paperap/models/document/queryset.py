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
    from paperap.models.document.model import Document

logger = logging.getLogger(__name__)


class DocumentQuerySet(QuerySet["Document"]):
    """
    QuerySet for Paperless-ngx documents with specialized filtering methods.
    """

    def with_tag_id(self, tag_id: Union[int, List[int]]) -> Self:
        """
        Filter documents that have the specified tag ID(s).

        Args:
            tag_id: A single tag ID or list of tag IDs

        Returns:
            Filtered DocumentQuerySet
        """
        if isinstance(tag_id, list):
            tag_ids_param = ",".join(str(tid) for tid in tag_id)
            return self.filter(tags__id__in=tag_ids_param)
        return self.filter(tags__id=tag_id)

    def with_tag_name(self, tag_name: str, exact: bool = True) -> Self:
        """
        Filter documents that have a tag with the specified name.

        Args:
            tag_name: The name of the tag
            exact: If True, match the exact tag name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            return self.filter(tags__name=tag_name)
        return self.filter(tags__name__contains=tag_name)

    def with_title(self, title: str, exact: bool = True) -> Self:
        """
        Filter documents by title.

        Args:
            title: The document title to filter by
            exact: If True, match the exact title, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            return self.filter(title=title)
        return self.filter(title__contains=title)

    def with_correspondent_id(self, correspondent_id: int) -> Self:
        """
        Filter documents by correspondent ID.

        Args:
            correspondent_id: The correspondent ID to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(correspondent=correspondent_id)

    def with_correspondent_name(self, name: str, exact: bool = True) -> Self:
        """
        Filter documents by correspondent name.

        Args:
            name: The correspondent name to filter by
            exact: If True, match the exact name, otherwise use contains

        Returns:
            Filtered DocumentQuerySet
        """
        if exact:
            return self.filter(correspondent__name=name)
        return self.filter(correspondent__name__contains=name)

    def with_document_type_id(self, document_type_id: int) -> Self:
        """
        Filter documents by document type ID.

        Args:
            document_type_id: The document type ID to filter by

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(document_type=document_type_id)

    def with_content(self, text: str) -> Self:
        """
        Filter documents whose content contains the specified text.

        Args:
            text: The text to search for in document content

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(content__contains=text)

    def created_after(self, date_str: str) -> Self:
        """
        Filter documents created after the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(created__gt=date_str)

    def created_before(self, date_str: str) -> Self:
        """
        Filter documents created before the specified date.

        Args:
            date_str: ISO format date string (YYYY-MM-DD)

        Returns:
            Filtered DocumentQuerySet
        """
        return self.filter(created__lt=date_str)
