"""
Define the Correspondent model for interacting with Paperless-NgX correspondents.

This module provides the Correspondent model class, which represents a person,
company, or organization that sends or receives documents in Paperless-NgX.
Correspondents help organize documents and make them easier to find.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.correspondent.queryset import CorrespondentQuerySet
from paperap.models.mixins.models import MatcherMixin

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class Correspondent(StandardModel, MatcherMixin):
    """
    Represent a correspondent in Paperless-NgX.

    A correspondent typically represents a person, company, or organization that sends
    or receives documents. Correspondents can be assigned to documents to help with
    organization and searching.

    Attributes:
        slug: URL-friendly identifier for the correspondent, auto-generated.
        name: Display name of the correspondent.
        document_count: Number of documents associated with this correspondent.
        owner: ID of the user who owns this correspondent.
        user_can_change: Whether the current user has permission to modify this correspondent.

    Examples:
        Create a new correspondent:
            >>> correspondent = client.correspondents.create(name="Electric Company")

        Assign a correspondent to a document:
            >>> document = client.documents.get(123)
            >>> document.correspondent = correspondent.id
            >>> document.save()

    """

    slug: str | None = None
    name: str | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    class Meta(StandardModel.Meta):
        """
        Define metadata for the Correspondent model.

        Specifies read-only fields and the associated queryset class for
        the Correspondent model.

        Attributes:
            read_only_fields: Set of field names that cannot be modified.
            queryset: The queryset class to use for this model.

        """

        # Fields that should not be modified
        read_only_fields = {
            "slug",
            "document_count",
        }
        queryset = CorrespondentQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get all documents associated with this correspondent.

        Provides a convenient way to access all documents that have been
        assigned to this correspondent without having to construct a filter.

        Returns:
            A queryset containing all documents associated with this correspondent.

        Examples:
            Get all documents for a correspondent:
                >>> correspondent = client.correspondents.get(5)
                >>> docs = correspondent.documents
                >>> print(f"Found {docs.count()} documents")

            Filter documents further:
                >>> recent_docs = correspondent.documents.filter(created__gt="2023-01-01")

        """
        return self._client.documents().all().correspondent_id(self.id)
