"""
Define the Tag model for interacting with Paperless-NgX tags.

This module provides the Tag model class for working with tags in Paperless-NgX.
Tags are used to categorize and organize documents, and this module enables
creating, retrieving, updating, and deleting tags, as well as accessing
documents associated with specific tags.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field, field_validator, model_validator

from paperap.const import MatchingAlgorithmType
from paperap.models.abstract.model import StandardModel
from paperap.models.mixins.models import MatcherMixin
from paperap.models.tag.queryset import TagQuerySet

if TYPE_CHECKING:
    from paperap.models.document import Document, DocumentQuerySet


class Tag(StandardModel, MatcherMixin):
    """
    Represent a tag in Paperless-NgX for document categorization.

    Tags are used to categorize and organize documents in Paperless-NgX. Each tag
    has a name, color, and can be designated as an inbox tag. Tags can be assigned
    to documents and used for filtering and searching.

    This class provides methods for interacting with tags, including retrieving
    associated documents and managing tag properties.

    Attributes:
        name (str, optional): The display name of the tag.
        slug (str, optional): The URL-friendly version of the name (auto-generated).
        colour (str or int, optional): The color of the tag (hex string or integer).
        is_inbox_tag (bool, optional): Whether this tag is used to mark documents for review.
        document_count (int): The number of documents with this tag (read-only).
        owner (int, optional): The ID of the user who owns this tag.
        user_can_change (bool, optional): Whether the current user has permission to modify this tag.

    Examples:
        Create a new tag:
        ```python
        tag = client.tags.create(
            name="Tax Documents",
            color="#ff0000",
            is_inbox_tag=False
        )
        ```

        Update an existing tag:
        ```python
        tag = client.tags.get(5)
        tag.name = "Important Tax Documents"
        tag.color = "#00ff00"
        tag.save()
        ```

    """

    name: str | None = None
    slug: str | None = None
    colour: str | int | None = Field(alias="color", default=None)
    is_inbox_tag: bool | None = None
    document_count: int = 0
    owner: int | None = None
    user_can_change: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_text_color_alias(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Handle 'text_color' as an alias for 'colour'.

        Ensure compatibility with different API versions by accepting 'text_color'
        as an alternative field name for the tag color.

        Args:
            data (dict[str, Any]): The input data dictionary to validate.

        Returns:
            dict[str, Any]: The modified data dictionary with normalized color field.

        """
        if isinstance(data, dict) and "text_color" in data and data.get("colour") is None and data.get("color") is None:
            data["colour"] = data.pop("text_color")
        return data

    # Alias for colour
    @property
    def color(self) -> str | int | None:
        """
        Get the tag color (alias for the colour field).

        Provide American English spelling alternative for the British 'colour' field.

        Returns:
            str | int | None: The color value as a string (hex code) or integer.

        """
        return self.colour

    @color.setter
    def color(self, value: str | int | None) -> None:
        """
        Set the tag color (setter for the colour field).

        Allow setting the tag color using American English spelling.

        Args:
            value (str | int | None): The color value to set (hex string or integer).

        """
        self.colour = value

    class Meta(StandardModel.Meta):
        """
        Define metadata for the Tag model.

        Specify model-specific metadata including read-only fields and
        the associated queryset class.

        Attributes:
            read_only_fields (set): Fields that cannot be modified by the client.
            queryset (TagQuerySet): The queryset class used for querying tags.

        """

        # Fields that should not be modified
        read_only_fields = {"slug", "document_count"}
        queryset = TagQuerySet

    @property
    def documents(self) -> "DocumentQuerySet":
        """
        Get all documents associated with this tag.

        Retrieve a queryset of all documents that have been tagged with this tag.
        The queryset is lazy-loaded, so no API requests are made until the queryset
        is evaluated.

        Returns:
            DocumentQuerySet: A queryset containing all documents with this tag.

        Examples:
            Get documents with a specific tag:
            ```python
            # Get a tag
            tax_tag = client.tags.get(5)

            # Get all documents with this tag
            tax_documents = tax_tag.documents

            # Count documents with this tag
            count = tax_tag.documents.count()

            # Filter documents with this tag further
            recent_tax_docs = tax_tag.documents.filter(created__gt="2023-01-01")
            ```

        """
        return self._client.documents().all().tag_id(self.id)
