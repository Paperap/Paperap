"""
----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import copy
import logging
from datetime import datetime
from string import Template
from typing import TYPE_CHECKING, Any, Final, Generic, Iterable, Iterator, Self, TypeAlias, Union, override

from pydantic import HttpUrl
from typing_extensions import TypeVar

from paperap.exceptions import FilterDisabledError, MultipleObjectsFoundError, ObjectNotFoundError

if TYPE_CHECKING:
    from paperap.models.abstract.model import BaseModel, StandardModel
    from paperap.resources.base import BaseResource, StandardResource

logger = logging.getLogger(__name__)

# _BaseResource = TypeVar("_BaseResource", bound="BaseResource", default="BaseResource")

type ClientResponse = dict[str, Any] | list[dict[str, Any]] | None


class BaseQuerySet[_Model: BaseModel](Iterable[_Model]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    BaseQuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.

    Args:
        resource: The BaseResource instance.
        filters: Initial filter parameters.
        _cache: Optional internal result cache.
        _fetch_all: Whether all results have been fetched.
        _next_url: URL for the next page of results.
        _last_response: Optional last response from the API.
        _iter: Optional iterator for the results.

    Returns:
        A new instance of BaseQuerySet.

    Examples:
        # Create a QuerySet for documents
        >>> docs = client.documents()
        >>> for doc in docs:
        ...    print(doc.id)
        1
        2
        3

    """

    resource: "BaseResource[_Model, Self]"
    filters: dict[str, Any]
    _last_response: ClientResponse | None = None
    _result_cache: list[_Model] = []
    _fetch_all: bool = False
    _next_url: str | None = None
    _urls_fetched: list[str] = []
    _iter: Iterator[_Model] | None

    def __init__(
        self,
        resource: "BaseResource[_Model, Self]",
        filters: dict[str, Any] | None = None,
        _cache: list[_Model] | None = None,
        _fetch_all: bool = False,
        _next_url: str | None = None,
        _last_response: ClientResponse = None,
        _iter: Iterator[_Model] | None = None,
        _urls_fetched: list[str] | None = None,
    ) -> None:
        self.resource = resource
        self.filters = filters or {}
        self._result_cache = _cache or []
        self._fetch_all = _fetch_all
        self._next_url = _next_url
        self._urls_fetched = _urls_fetched or []
        self._last_response = _last_response
        self._iter = _iter

        super().__init__()

    @property
    def _model(self) -> type[_Model]:
        """
        Return the model class associated with the resource.

        Returns:
            The model class

        Examples:
            # Create a model instance
            >>> model = queryset._model(**params)

        """
        return self.resource.model_class

    @property
    def _meta(self) -> "BaseModel.Meta[Any]":
        """
        Return the model's metadata.

        Returns:
            The model's metadata

        Examples:
            # Get the model's metadata
            >>> queryset._meta.read_only_fields
            {'id', 'added', 'modified'}

        """
        return self._model._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    def _reset(self) -> None:
        """
        Reset the QuerySet to its initial state.

        This clears the result cache and resets the fetch state.
        """
        self._result_cache = []
        self._fetch_all = False
        self._next_url = None
        self._urls_fetched = []
        self._last_response = None
        self._iter = None

    def _update_filters(self, values: dict[str, Any]) -> None:
        """
        Update the current filters with new values.

        This updates the current queryset instance. It does not return a new instance. For that reason,
        do not call this directly. Call filter() or exclude() instead.

        Args:
            values: New filter values to add

        Raises:
            FilterDisabledError: If a filter is not allowed by the resource

        Examples:
            # Update filters with new values
            queryset._update_filters({"correspondent": 1})

            # Update filters with multiple values
            queryset._update_filters({"correspondent": 1, "document_type": 2})

        """
        for key, _value in values.items():
            if not self._meta.filter_allowed(key):
                raise FilterDisabledError(f"Filtering by {key} for {self.resource.name} does not appear to be supported by the API.")

        if values:
            # Reset the cache if filters change
            self._reset()
            self.filters.update(**values)

    def filter(self, **kwargs: Any) -> Self:
        """
        Return a new QuerySet with the given filters applied.

        Args:
            **kwargs: Filters to apply, where keys are field names and values are desired values.
                    Supports Django-style lookups like field__contains, field__in, etc.

        Returns:
            A new QuerySet with the additional filters applied

        Examples:
            # Get documents with specific correspondent
            docs = client.documents.filter(correspondent=1)

            # Get documents with specific correspondent and document type
            docs = client.documents.filter(correspondent=1, document_type=2)

            # Get documents with title containing "invoice"
            docs = client.documents.filter(title__contains="invoice")

            # Get documents with IDs in a list
            docs = client.documents.filter(id__in=[1, 2, 3])

        """
        processed_filters = {}

        for key, value in kwargs.items():
            # Handle list values for __in lookups
            if isinstance(value, (list, set, tuple)):
                # Convert list to comma-separated string for the API
                processed_value = ",".join(str(item) for item in value)
                processed_filters[key] = processed_value
            # Handle boolean values
            elif isinstance(value, bool):
                processed_filters[key] = str(value).lower()
            # Handle normal values
            else:
                processed_filters[key] = value

        return self._chain(filters={**self.filters, **processed_filters})

    def exclude(self, **kwargs: Any) -> Self:
        """
        Return a new QuerySet excluding objects with the given filters.

        Args:
            **kwargs: Filters to exclude, where keys are field names and values are excluded values

        Returns:
            A new QuerySet excluding objects that match the filters

        Examples:
            # Get documents with any correspondent except ID 1
            docs = client.documents.exclude(correspondent=1)

        """
        # Transform each key to its "not" equivalent
        exclude_filters = {}
        for key, value in kwargs.items():
            if "__" in key:
                field, lookup = key.split("__", 1)
                # If it already has a "not" prefix, remove it
                if lookup.startswith("not_"):
                    exclude_filters[f"{field}__{lookup[4:]}"] = value
                else:
                    exclude_filters[f"{field}__not_{lookup}"] = value
            else:
                exclude_filters[f"{key}__not"] = value

        return self._chain(filters={**self.filters, **exclude_filters})

    def get(self, pk: Any) -> _Model:
        """
        Retrieve a single object from the API.

        Raises NotImplementedError. Subclasses may implement this.

        Args:
             pk: The primary key (e.g. the id) of the object to retrieve

        Returns:
            A single object matching the query

        Raises:
            ObjectNotFoundError: If no object or multiple objects are found
            NotImplementedError: If the method is not implemented by the subclass

        Examples:
            # Get document with ID 123
            doc = client.documents.get(123)

        """
        raise NotImplementedError("Getting a single resource is not defined by BaseModels without an id.")

    def _get_last_count(self) -> int | None:
        if self._last_response is None:
            return None
        if isinstance(self._last_response, list):
            return len(self._last_response)
        return self._last_response.get("count")

    def count(self) -> int:
        """
        Return the total number of objects in the queryset.

        Returns:
            The total count of objects matching the filters

        Raises:
            NotImplementedError: If the response does not have a count attribute

        """
        # If we have a last response, we can use the "count" field
        if (count := self._get_last_count()) is not None:
            return count

        # Get one page of results, to populate last response
        _iter = self._request_iter(params=self.filters)

        # TODO Hack
        for _ in _iter:
            break

        if not self._last_response:
            # I don't think this should ever occur, but just in case.
            raise NotImplementedError("Requested iter, but no last response")

        if (count := self._get_last_count()) is not None:
            return count

        # I don't think this should ever occur, but just in case.
        raise NotImplementedError(f"Unexpected Error: Could not determine count of objects. Last response: {self._last_response}")

    def count_this_page(self) -> int:
        """
        Return the number of objects on the current page.

        Returns:
            The count of objects on the current page

        Raises:
            NotImplementedError: If _last_response is not set

        """
        # If we have a last response, we can count it without a new request
        if self._last_response:
            if isinstance(self._last_response, list):
                return len(self._last_response)
            results = self._last_response.get("results", [])
            return len(results)

        # Get one page of results, to populate last response
        _iter = self._request_iter(params=self.filters)

        # TODO Hack
        for _ in _iter:
            break

        if not self._last_response:
            # I don't think this should ever occur, but just in case.
            raise NotImplementedError("Requested iter, but no last response")

        if isinstance(self._last_response, list):
            return len(self._last_response)
        results = self._last_response.get("results", [])
        return len(results)

    def all(self) -> Self:
        """
        Return a new QuerySet that copies the current one.

        Returns:
            A copy of the current BaseQuerySet

        """
        return self._chain()

    def order_by(self, *fields: str) -> Self:
        """
        Return a new QuerySet ordered by the specified fields.

        Args:
            *fields: Field names to order by. Prefix with '-' for descending order.

        Returns:
            A new QuerySet with the ordering applied

        Examples:
            # Order documents by title ascending
            docs = client.documents.order_by('title')

            # Order documents by added date descending
            docs = client.documents.order_by('-added')

        """
        if not fields:
            return self

        # Combine with existing ordering if any
        ordering = self.filters.get("ordering", [])
        if isinstance(ordering, str):
            ordering = [ordering]
        elif not isinstance(ordering, list):
            ordering = list(ordering)

        # Add new ordering fields
        new_ordering = ordering + list(fields)

        # Join with commas for API
        ordering_param = ",".join(new_ordering)

        return self._chain(filters={**self.filters, "ordering": ordering_param})

    def first(self) -> _Model | None:
        """
        Return the first object in the QuerySet, or None if empty.

        Returns:
            The first object or None if no objects match

        """
        if self._result_cache and len(self._result_cache) > 0:
            return self._result_cache[0]

        # If not cached, create a copy limited to 1 result
        results = list(self._chain(filters={**self.filters, "limit": 1}))
        return results[0] if results else None

    def last(self) -> _Model | None:
        """
        Return the last object in the QuerySet, or None if empty.

        Note: This requires fetching all results to determine the last one.

        Returns:
            The last object or None if no objects match

        """
        # If we have all results, we can just return the last one
        if self._fetch_all:
            if self._result_cache and len(self._result_cache) > 0:
                return self._result_cache[-1]
            return None

        # We need all results to get the last one
        self._fetch_all_results()

        if self._result_cache and len(self._result_cache) > 0:
            return self._result_cache[-1]
        return None

    def exists(self) -> bool:
        """
        Return True if the QuerySet contains any results.

        Returns:
            True if there are any objects matching the filters

        """
        # Check the cache before potentially making a new request
        if self._fetch_all or self._result_cache:
            return len(self._result_cache) > 0

        # Check if there's at least one result
        return self.first() is not None

    def none(self) -> Self:
        """
        Return an empty QuerySet.

        Returns:
            An empty QuerySet

        """
        return self._chain(filters={"limit": 0})

    def filter_field_by_str(self, field: str, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter a queryset based on a given field.

        This allows subclasses to easily implement custom filter methods.

        Args:
            field: The field name to filter by.
            value: The value to filter against.
            exact: Whether to filter by an exact match.
            case_insensitive: Whether the filter should be case-insensitive.

        Returns:
            A new QuerySet instance with the filter applied.

        """
        if exact:
            lookup = f"{field}__iexact" if case_insensitive else field
        else:
            lookup = f"{field}__icontains" if case_insensitive else f"{field}__contains"

        return self.filter(**{lookup: value})

    def _fetch_all_results(self) -> None:
        """
        Fetch all results from the API and populate the cache.

        Returns:
            None

        """
        if self._fetch_all:
            return

        # Clear existing cache if any
        self._result_cache = []

        # Initial fetch
        iterator = self._request_iter(params=self.filters)

        # Collect results from initial page
        # TODO: Consider itertools chain for performance reasons (?)
        self._result_cache.extend(list(iterator))

        # Fetch additional pages if available
        while self._last_response and self._next_url:
            iterator = self._request_iter(url=self._next_url)
            self._result_cache.extend(list(iterator))

        self._fetch_all = True

    def _request_iter(self, url: str | HttpUrl | Template | None = None, params: dict[str, Any] | None = None) -> Iterator[_Model]:
        """
        Get an iterator of resources.

        Args:
            url: The URL to request, if different from the resource's default.
            params: Query parameters.

        Returns:
            An iterator over the resources.

        Raises:
            NotImplementedError: If the request cannot be completed.

        Examples:
            # Iterate over documents
            for doc in queryset._request_iter():
                print(doc)

        """
        if not (response := self.resource.request_raw(url=url, params=params)):
            logger.debug("No response from request.")
            return

        self._last_response = response

        yield from self.resource.handle_response(response)

    def _get_next(self, response: ClientResponse | None = None) -> str | None:
        """
        Get the next url, and adjust our references accordingly.
        """
        # Allow passing a different response
        if response is None:
            response = self._last_response

        if isinstance(response, list):
            return None

        # Last response is not set
        if not response or not (next_url := response.get("next")):
            self._next_url = None
            return None

        # For safety, check both instance attributes, even though the first check isn't strictly necessary
        # this hopefully future proofs any changes to the implementation
        if next_url == self._next_url or next_url in self._urls_fetched:
            logger.debug(
                "Next URL was previously fetched. Stopping iteration. URL: %s, Already Fetched: %s",
                next_url,
                self._urls_fetched,
            )
            self._next_url = None
            return None

        # Cache it
        self._next_url = next_url
        self._urls_fetched.append(next_url)
        return self._next_url

    def _chain(self, **kwargs: Any) -> Self:
        """
        Return a copy of the current BaseQuerySet with updated attributes.

        Args:
            **kwargs: Attributes to update in the new BaseQuerySet

        Returns:
            A new QuerySet with the updated attributes

        """
        # Create a new BaseQuerySet with copied attributes
        clone = self.__class__(self.resource)  # type: ignore # pyright not handling Self correctly

        # Copy attributes from self
        clone.filters = copy.deepcopy(self.filters)
        # Do not copy the cache, fetch_all, etc, since filters may change it

        # Update with provided kwargs
        for key, value in kwargs.items():
            if key == "filters" and value:
                clone._update_filters(value)  # pylint: disable=protected-access
            else:
                setattr(clone, key, value)

        return clone

    @override
    def __iter__(self) -> Iterator[_Model]:
        """
        Iterate over the objects in the QuerySet.

        Returns:
            An iterator over the objects

        """
        # If we have a fully populated cache, use it
        if self._fetch_all:
            yield from self._result_cache
            return

        if not self._iter:
            # Start a new iteration
            self._iter = self._request_iter(params=self.filters)

            # Yield objects from the current page
            for obj in self._iter:
                self._result_cache.append(obj)
                yield obj

            self._get_next()

        # If there are more pages, keep going
        count = 0
        while self._next_url:
            count += 1
            self._iter = self._request_iter(url=self._next_url)

            # Yield objects from the current page
            for obj in self._iter:
                self._result_cache.append(obj)
                yield obj

            self._get_next()

        # We've fetched everything
        self._fetch_all = True
        self._iter = None

    def __len__(self) -> int:
        """
        Return the number of objects in the QuerySet.

        Returns:
            The count of objects

        """
        return self.count()

    def __bool__(self) -> bool:
        """
        Return True if the QuerySet has any results.

        Returns:
            True if there are any objects matching the filters

        """
        return self.exists()

    def __getitem__(self, key: int | slice) -> _Model | list[_Model]:
        """
        Retrieve an item or slice of items from the QuerySet.

        Args:
            key: An integer index or slice

        Returns:
            A single object or list of objects

        Raises:
            IndexError: If the index is out of range

        """
        if isinstance(key, slice):
            # Handle slicing
            start = key.start if key.start is not None else 0
            stop = key.stop

            if start < 0 or (stop is not None and stop < 0):
                # Negative indexing requires knowing the full size
                self._fetch_all_results()
                return self._result_cache[key]

            # Optimize by using limit/offset if available
            if start == 0 and stop is not None:
                # Simple limit
                clone = self._chain(filters={**self.filters, "limit": stop})
                results = list(clone)
                return results

            if start > 0 and stop is not None:
                # Limit with offset
                clone = self._chain(
                    filters={
                        **self.filters,
                        "limit": stop - start,
                        "offset": start,
                    }
                )
                results = list(clone)
                return results

            if start > 0 and stop is None:
                # Just offset
                clone = self._chain(filters={**self.filters, "offset": start})
                self._fetch_all_results()  # We need all results after the offset
                return self._result_cache

            # Default to fetching all and slicing
            self._fetch_all_results()
            return self._result_cache[key]

        # Handle integer indexing
        if key < 0:
            # Negative indexing requires the full result set
            self._fetch_all_results()
            return self._result_cache[key]

        # Positive indexing - we can optimize with limit/offset
        if len(self._result_cache) > key:
            # Already have this item cached
            return self._result_cache[key]

        # Fetch specific item by position
        clone = self._chain(filters={**self.filters, "limit": 1, "offset": key})
        results = list(clone)
        if not results:
            raise IndexError(f"BaseQuerySet index {key} out of range")
        return results[0]

    def __contains__(self, item: Any) -> bool:
        """
        Return True if the QuerySet contains the given object.

        Args:
            item: The object to check for

        Returns:
            True if the object is in the QuerySet

        """
        if not isinstance(item, self._model):
            return False

        return any(obj == item for obj in self)


class StandardQuerySet[_Model: StandardModel](BaseQuerySet[_Model]):
    """
    A queryset for StandardModel instances (i.e. BaseModels with standard fields, like id).

    Returns:
        A new instance of StandardModel.

    Raises:
        ValueError: If resource is not provided.

    Examples:
        # Create a StandardModel instance
        model = StandardModel(id=1)

    Args:
        resource: The BaseResource instance.
        filters: Initial filter parameters.

    Returns:
        A new instance of StandardQuerySet.

    Raises:
        ObjectNotFoundError: If no object or multiple objects are found.

    Examples:
        # Create a StandardQuerySet for documents
        docs = StandardQuerySet(resource=client.documents)

    """

    resource: "StandardResource[_Model, Self]"  # type: ignore # pyright is getting inheritance wrong

    @override
    def get(self, pk: int) -> _Model:
        """
        Retrieve a single object from the API.

        Args:
            pk: The ID of the object to retrieve

        Returns:
            A single object matching the query

        Raises:
            ObjectNotFoundError: If no object or multiple objects are found

        Examples:
            # Get document with ID 123
            doc = client.documents.get(123)

        """
        # Attempt to find it in the result cache
        if self._result_cache:
            for obj in self._result_cache:
                if obj.id == pk:
                    return obj

        # Direct lookup by ID - use the resource's get method
        return self.resource.get(pk)

    def id(self, value: int | list[int]) -> Self:
        """
        Filter models by ID.

        Args:
            value: The ID or list of IDs to filter by

        Returns:
            Filtered QuerySet

        """
        if isinstance(value, list):
            return self.filter(id__in=value)
        return self.filter(id=value)

    @override
    def __contains__(self, item: Any) -> bool:
        """
        Return True if the QuerySet contains the given object.

        NOTE: This method only ensures a match by ID, not by full object equality.
        This is intentional, as the object may be outdated or not fully populated.

        Args:
            item: The object or ID to check for

        Returns:
            True if the object is in the QuerySet

        """
        # Handle integers directly
        if isinstance(item, int):
            return any(obj.id == item for obj in self)

        # Handle model objects that have an id attribute
        try:
            if hasattr(item, "id"):
                return any(obj.id == item.id for obj in self)
        except (AttributeError, TypeError):
            pass

        # For any other type, it's not in the queryset
        return False

    def bulk_action(self, action: str, **kwargs: Any) -> ClientResponse:
        """
        Perform a bulk action on all objects in the queryset.

        This method fetches all IDs in the queryset and passes them to the resource's bulk_action method.

        Args:
            action: The action to perform
            **kwargs: Additional parameters for the action

        Returns:
            The API response

        Raises:
            NotImplementedError: If the resource doesn't support bulk actions

        """
        if not (fn := getattr(self.resource, "bulk_action", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk actions")

        # Fetch all IDs in the queryset
        # We only need IDs, so optimize by requesting just the ID field if possible
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(action, ids, **kwargs)

    def bulk_delete(self) -> ClientResponse:
        """
        Delete all objects in the queryset.

        Returns:
            The API response

        """
        return self.bulk_action("delete")

    def bulk_update(self, **kwargs: Any) -> ClientResponse:
        """
        Update all objects in the queryset with the given values.

        Args:
            **kwargs: Fields to update

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_update", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk updates")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, **kwargs)

    def bulk_assign_tags(self, tag_ids: list[int], remove_existing: bool = False) -> ClientResponse:
        """
        Assign tags to all objects in the queryset.

        Args:
            tag_ids: List of tag IDs to assign
            remove_existing: If True, remove existing tags before assigning new ones

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_assign_tags", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk tag assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, tag_ids, remove_existing)

    def bulk_assign_correspondent(self, correspondent_id: int) -> ClientResponse:
        """
        Assign a correspondent to all objects in the queryset.

        Args:
            correspondent_id: Correspondent ID to assign

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_assign_correspondent", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk correspondent assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, correspondent_id)

    def bulk_assign_document_type(self, document_type_id: int) -> ClientResponse:
        """
        Assign a document type to all objects in the queryset.

        Args:
            document_type_id: Document type ID to assign

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_assign_document_type", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk document type assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, document_type_id)

    def bulk_assign_storage_path(self, storage_path_id: int) -> ClientResponse:
        """
        Assign a storage path to all objects in the queryset.

        Args:
            storage_path_id: Storage path ID to assign

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_assign_storage_path", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk storage path assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, storage_path_id)

    def bulk_assign_owner(self, owner_id: int) -> ClientResponse:
        """
        Assign an owner to all objects in the queryset.

        Args:
            owner_id: Owner ID to assign

        Returns:
            The API response

        """
        if not (fn := getattr(self.resource, "bulk_assign_owner", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk owner assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, owner_id)
