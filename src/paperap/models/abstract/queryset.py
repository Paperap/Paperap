"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import copy
from datetime import datetime
from string import Template
from typing import Any, Generic, Iterable, Iterator, Optional, Self, TypeVar, Union, TYPE_CHECKING
import logging
from yarl import URL
from paperap.exceptions import MultipleObjectsFoundError, ObjectNotFoundError, FilterDisabledError

if TYPE_CHECKING:
    from paperap.models.abstract.model import PaperlessModel, StandardModel
    from paperap.resources.base import PaperlessResource, StandardResource

_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel", covariant=True)
_StandardModel = TypeVar("_StandardModel", bound="StandardModel", covariant=True)

logger = logging.getLogger(__name__)


class QuerySet(Iterable[_PaperlessModel], Generic[_PaperlessModel]):
    """
    A lazy-loaded, chainable query interface for Paperless NGX resources.

    QuerySet provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    It's designed to be lazy - only fetching data when it's actually needed.

    Args:
        resource: The PaperlessResource instance.
        filters: Initial filter parameters.
        _cache: Optional internal result cache.
        _fetch_all: Whether all results have been fetched.
        _next_url: URL for the next page of results.
        _last_response: Optional last response from the API.
        _iter: Optional iterator for the results.

    Returns:
        A new instance of QuerySet.

    Examples:
        # Create a QuerySet for documents
        >>> docs = client.documents()
        >>> for doc in docs:
        ...    print(doc.id)
        1
        2
        3
    """

    resource: "PaperlessResource[_PaperlessModel]"
    filters: dict[str, Any]
    _last_response: dict[str, Any] | None = None
    _result_cache: list[_PaperlessModel] = []
    _fetch_all: bool = False
    _next_url: str | None = None
    _iter: Iterator[_PaperlessModel] | None

    def __init__(
        self,
        resource: "PaperlessResource[_PaperlessModel]",
        filters: Optional[dict[str, Any]] = None,
        _cache: Optional[list[_PaperlessModel]] = None,
        _fetch_all: bool = False,
        _next_url: str | None = None,
        _last_response: Optional[dict[str, Any]] = None,
        _iter: Optional[Iterator[_PaperlessModel]] = None,
    ):
        self.resource = resource
        self.filters = filters or {}
        self._result_cache = _cache or []
        self._fetch_all = _fetch_all
        self._next_url = _next_url
        self._last_response = _last_response
        self._iter = _iter

    @property
    def _model(self) -> type[_PaperlessModel]:
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
    def _meta(self) -> "PaperlessModel.Meta":
        """
        Return the model's metadata.

        Returns:
            The model's metadata

        Examples:
            # Get the model's metadata
            >>> queryset._meta.read_only_fields
            {'id', 'added', 'modified'}
        """
        return self._model._meta

    def _reset(self) -> None:
        """
        Reset the QuerySet to its initial state.

        This clears the result cache and resets the fetch state.
        """
        self._result_cache = []
        self._fetch_all = False
        self._next_url = None
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
                raise FilterDisabledError(
                    f"Filtering by {key} for {self.resource.name} does not appear to be supported by the API."
                )

        if values:
            # Reset the cache if filters change
            self._reset()
            self.filters.update(**values)

    def filter(self, **kwargs) -> Self:
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

    def exclude(self, **kwargs) -> Self:
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

    def get(self, id: int) -> _PaperlessModel:
        """
        Retrieve a single object from the API.

        Raises NotImplementedError. Subclasses may implement this.

        Args:
            id: The ID of the object to retrieve

        Returns:
            A single object matching the query

        Raises:
            ObjectNotFoundError: If no object or multiple objects are found
            NotImplementedError: If the method is not implemented by the subclass

        Examples:
            # Get document with ID 123
            doc = client.documents.get(123)
        """
        raise NotImplementedError("Getting a single resource is not defined by PaperlessModels without an id.")

    def count(self) -> int:
        """
        Return the total number of objects in the queryset.

        Returns:
            The total count of objects matching the filters

        Raises:
            NotImplementedError: If the response does not have a count attribute
        """
        # If we have a last response, we can use the "count" field
        if self._last_response:
            if (count := self._last_response.get("count")) is not None:
                return count
            raise NotImplementedError("Response does not have a count attribute.")

        # Get one page of results, to populate last response
        _iter = self._request_iter(params=self.filters)

        # TODO Hack
        for _ in _iter:
            break

        if not self._last_response:
            # I don't think this should ever occur, but just in case.
            raise NotImplementedError("Requested iter, but no last response")

        if (count := self._last_response.get("count")) is not None:
            return count

        # I don't think this should ever occur, but just in case.
        raise NotImplementedError("Unexpected Error: Could not determine count of objects")

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

        results = self._last_response.get("results", [])
        return len(results)

    def all(self) -> Self:
        """
        Return a new QuerySet that copies the current one.

        Returns:
            A copy of the current QuerySet
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

    def first(self) -> Optional[_PaperlessModel]:
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

    def last(self) -> Optional[_PaperlessModel]:
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
        if self._result_cache is not None:
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
        Generic method to filter a queryset based on a given field.

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
        response = self._last_response

        # Collect results from initial page
        self._result_cache.extend(list(iterator))

        # Fetch additional pages if available
        while response and (next_url := response.get("next")):
            iterator = self._request_iter(url=next_url)
            response = self._last_response
            self._result_cache.extend(list(iterator))

        self._fetch_all = True

    def _request_iter(
        self, url: str | URL | Template | None = None, params: Optional[dict[str, Any]] = None
    ) -> Iterator[_PaperlessModel]:
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
        if not (response := self.resource._request_raw(url=url, params=params)):
            logger.debug("No response from request.")
            return

        self._last_response = response

        yield from self.resource._handle_response(response)

    def _chain(self, **kwargs) -> Self:
        """
        Return a copy of the current QuerySet with updated attributes.

        Args:
            **kwargs: Attributes to update in the new QuerySet

        Returns:
            A new QuerySet with the updated attributes
        """
        # Create a new QuerySet with copied attributes
        clone = self.__class__(self.resource)

        # Copy attributes from self
        clone.filters = copy.deepcopy(self.filters)
        # Do not copy the cache, fetch_all, etc, since filters may change it

        # Update with provided kwargs
        for key, value in kwargs.items():
            if key == "filters" and value:
                clone._update_filters(value)
            else:
                setattr(clone, key, value)

        return clone

    def __iter__(self) -> Iterator[_PaperlessModel]:
        """
        Iterate over the objects in the QuerySet.

        Returns:
            An iterator over the objects
        """
        # If we have a fully populated cache, use it
        if self._fetch_all:
            for obj in self._result_cache or []:
                yield obj
            return

        # We're doing a fresh query
        if self._result_cache is None:
            self._result_cache = []

        if not self._iter:
            # Start a new iteration
            self._iter = self._request_iter(params=self.filters)
            self._next_url = self._last_response.get("next") if self._last_response else None

            # Yield objects from the current page
            for obj in self._iter:
                self._result_cache.append(obj)
                yield obj

        # If there are more pages, keep going
        while self._next_url:
            self._iter = self._request_iter(url=self._next_url)
            self._next_url = self._last_response.get("next") if self._last_response else None

            # Yield objects from the current page
            for obj in self._iter:
                self._result_cache.append(obj)
                yield obj

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

    def __getitem__(self, key: Union[int, slice]) -> Union[_PaperlessModel, list[_PaperlessModel]]:
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
        if self._result_cache is not None and len(self._result_cache) > key:
            # Already have this item cached
            return self._result_cache[key]

        # Fetch specific item by position
        clone = self._chain(filters={**self.filters, "limit": 1, "offset": key})
        results = list(clone)
        if not results:
            raise IndexError(f"QuerySet index {key} out of range")
        return results[0]


class StandardQuerySet(QuerySet[_StandardModel], Generic[_StandardModel]):
    """
    A queryset for StandardModel instances (i.e. Paperless Models with standard fields, like id).

    Returns:
        A new instance of StandardModel.

    Raises:
        ValueError: If resource is not provided.

    Examples:
        # Create a StandardModel instance
        model = StandardModel(id=1)

    Args:
        resource: The PaperlessResource instance.
        filters: Initial filter parameters.

    Returns:
        A new instance of StandardQuerySet.

    Raises:
        ObjectNotFoundError: If no object or multiple objects are found.

    Examples:
        # Create a StandardQuerySet for documents
        docs = StandardQuerySet(resource=client.documents)
    """

    def get(self, id: int) -> _StandardModel:
        """
        Retrieve a single object from the API.

        Args:
            id: The ID of the object to retrieve

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
                if obj.id == id:
                    return obj

        # Direct lookup by ID - use the resource's get method
        return self.resource.get(id)

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
