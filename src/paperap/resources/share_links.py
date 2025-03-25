"""
Manage share links resources in Paperless-NgX.

Provide functionality for creating, retrieving, and managing
temporary public access URLs for documents in Paperless-NgX. Share links
allow documents to be accessed without authentication for a limited time.

Classes:
    ShareLinksResource: Resource for managing share links operations.
"""

from __future__ import annotations
from paperap.models.share_links import ShareLinks, ShareLinksQuerySet
from paperap.resources.base import StandardResource


class ShareLinksResource(StandardResource[ShareLinks, ShareLinksQuerySet]):
    """
    Manage share links in Paperless-NgX.

    Provide methods to interact with the share links API endpoint for creating,
    retrieving, and deleting temporary public access links to documents. These
    links allow document access without authentication for a specified period.

    Extends StandardResource to leverage common operations like get(), all(),
    filter(), create(), update(), and delete().

    Args:
        client: PaperlessClient instance for making API requests.

    Attributes:
        model_class (Type[ShareLinks]): The model class for share links.
        queryset_class (Type[ShareLinksQuerySet]): The queryset class for query operations.
        name (str): The resource name used in API endpoints ("share_links").

    Example:
        Create and manage share links for documents:

        >>> from datetime import datetime, timedelta
        >>> # Get all share links
        >>> all_share_links = client.share_links.all()
        >>>
        >>> # Create a new share link for document with ID 123
        >>> new_link = client.share_links.create(
        ...     document=123,
        ...     expiration=datetime.now() + timedelta(days=7)
        ... )
        >>>
        >>> # Get the public URL
        >>> print(new_link.url)
        >>>
        >>> # Delete an expired link
        >>> old_link = client.share_links.get(456)
        >>> old_link.delete()

    """

    model_class = ShareLinks
    queryset_class = ShareLinksQuerySet
    name: str = "share_links"
