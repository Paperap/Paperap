"""
Module for managing saved views in Paperap.

This module provides the `SavedViewResource` class for interacting with saved views
in the Paperless-NgX application. Saved views are predefined filters that users can
apply to quickly access specific sets of documents based on custom criteria.

The module integrates with the Paperless-NgX API to allow creating, retrieving,
updating, and deleting saved views, as well as applying them to document queries.

Examples:
    Basic usage through a PaperlessClient instance:

    ```python
    from paperap import PaperlessClient

    client = PaperlessClient()

    # Get all saved views
    all_views = client.saved_views.all()

    # Create a new saved view with filter rules
    new_view = client.saved_views.create(
        name="Tax Documents",
        show_on_dashboard=True,
        filter_rules=[
            {"rule_type": "document_type", "value": "5"},
            {"rule_type": "tag", "value": "7"}
        ]
    )
    ```

"""

from __future__ import annotations

from paperap.models.saved_view import SavedView, SavedViewQuerySet
from paperap.resources.base import StandardResource


class SavedViewResource(StandardResource[SavedView, SavedViewQuerySet]):
    """
    Resource for managing saved views in Paperless-NgX.

    This class provides methods to interact with the saved views endpoint
    of the Paperless-NgX API. Saved views store predefined filter configurations
    that can be quickly applied to document lists.

    Attributes:
        model_class (Type[SavedView]): The model class for saved view objects.
        queryset_class (Type[SavedViewQuerySet]): The queryset class for query operations.
        name (str): The resource name used in API endpoints.

    Examples:
        Retrieve all saved views:

        ```python
        saved_views = client.saved_views.all()
        for view in saved_views:
            print(f"{view.name}: {len(view.filter_rules)} rules")
        ```

        Create a new saved view with filter rules:

        ```python
        new_view = client.saved_views.create(
            name="Tax Documents 2023",
            show_on_dashboard=True,
            show_in_sidebar=True,
            filter_rules=[
                {"rule_type": "document_type", "value": "5"},
                {"rule_type": "created", "rule": "gt", "value": "2023-01-01"}
            ]
        )
        ```

        Update an existing saved view:

        ```python
        view = client.saved_views.get(5)
        view.filter_rules.append({"rule_type": "correspondent", "value": "7"})
        view.save()
        ```

        Delete a saved view:

        ```python
        client.saved_views.get(5).delete()
        ```

    """

    model_class = SavedView
    queryset_class = SavedViewQuerySet
    name: str = "saved_views"
