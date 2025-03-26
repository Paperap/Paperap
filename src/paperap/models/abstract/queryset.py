"""
Provide query interfaces for interacting with Paperless-ngx API resources.

This module implements QuerySet classes that offer a Django-like interface for
querying, filtering, and manipulating Paperless-ngx resources. The QuerySets
are lazy-loaded and chainable, allowing for efficient API interactions.
"""

from __future__ import annotations

import copy
import logging
from string import Template
from typing import TYPE_CHECKING, Any, Generic, Iterable, Iterator, Protocol, Self, override

from pydantic import HttpUrl
from typing_extensions import TypeVar

from paperap.const import ClientResponse
from paperap.exceptions import FilterDisabledError, MultipleObjectsFoundError, ObjectNotFoundError

if TYPE_CHECKING:
    from paperap.models.abstract.model import BaseModel, StandardModel
    from paperap.resources.base import BaseResource, StandardResource

logger = logging.getLogger(__name__)

# _BaseResource = TypeVar("_BaseResource", bound="BaseResource", default="BaseResource")


class BaseQuerySet[_Model: BaseModel](Iterable[_Model]):
    """
    A lazy-loaded, chainable query interface for Paperless-ngx resources.

    Provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    Only fetches data when it's actually needed, optimizing API requests and performance.

    Attributes:
        resource: The resource instance associated with the queryset.
        filters: Dictionary of filters to apply to the API request.
        _last_response: The last response received from the API.
        _result_cache: List of model instances already fetched.
        _fetch_all: Whether all results have been fetched.
        _next_url: URL for the next page of results, if any.
        _urls_fetched: List of URLs already fetched to prevent loops.
        _iter: Current iterator over results, if any.

    Examples:
        Basic usage:

        >>> docs = client.documents()  # Returns a BaseQuerySet
        >>> for doc in docs.filter(title__contains="invoice"):
        ...     print(doc.title)

    """

    resource: "BaseResource[_Model, Self]"  # type: ignore # because mypy doesn't accept nested generics
    filters: dict[str, Any]
    _last_response: ClientResponse | None = None
    _result_cache: list[_Model] = []
    _fetch_all: bool = False
    _next_url: str | None = None
    _urls_fetched: list[str] = []
    _iter: Iterator[_Model] | None

    def __init__(
        self,
        resource: "BaseResource[_Model, Self]",  # type: ignore # because mypy doesn't accept nested generics # noqa: F811
        filters: dict[str, Any] | None = None,
        _cache: list[_Model] | None = None,
        _fetch_all: bool = False,
        _next_url: str | None = None,
        _last_response: ClientResponse = None,
        _iter: Iterator[_Model] | None = None,
        _urls_fetched: list[str] | None = None,
    ) -> None:
        """
        Initialize a new BaseQuerySet.

        Args:
            resource: The resource instance that will handle API requests.
            filters: Initial filters to apply to the queryset.
            _cache: Pre-populated result cache (internal use).
            _fetch_all: Whether all results have been fetched (internal use).
            _next_url: URL for the next page of results (internal use).
            _last_response: Last API response received (internal use).
            _iter: Current iterator over results (internal use).
            _urls_fetched: List of URLs already fetched (internal use).

        """
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
        Get the model class associated with the resource.

        Returns:
            The model class for this queryset.

        Examples:
            Create a model instance:

            >>> model = queryset._model(**params)

        """
        return self.resource.model_class

    @property
    def _meta(self) -> "BaseModel.Meta[Any]":
        """
        Get the model's metadata.

        Returns:
            The model's metadata containing information about filtering capabilities,
            resource paths, and field properties.

        Examples:
            Get the model's read-only fields:

            >>> queryset._meta.read_only_fields
            {'id', 'added', 'modified'}

        """
        return self._model._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    def _reset(self) -> None:
        """
        Reset the QuerySet to its initial state.

        Clears the result cache and resets the fetch state, making the queryset
        behave as if it was newly created. Called internally when filters or
        other query parameters change.
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

        Updates the current queryset instance in-place. Does not return a new
        instance. For that reason, do not call this directly. Use filter() or
        exclude() instead.

        Args:
            values: Dictionary of new filter values to add to the existing filters.

        Raises:
            FilterDisabledError: If a filter is not allowed by the resource's metadata.

        Note:
            This is an internal method that should not be called directly by users.

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
            **kwargs: Filters to apply, where keys are field names and values are
                desired values. Supports Django-style lookups like field__contains,
                field__in, etc.

        Returns:
            A new QuerySet with the additional filters applied.

        Examples:
            Get documents with specific correspondent:

            >>> docs = client.documents().filter(correspondent=1)

            Filter with multiple conditions:

            >>> docs = client.documents().filter(
            ...     title__contains="invoice",
            ...     created__gt="2023-01-01"
            ... )

        """
        processed_filters = {}

        for key, value in kwargs.items():
            if isinstance(value, (list, set, tuple)):
                # Convert list to comma-separated string for the API
                processed_value = ",".join(str(item) for item in value)
                processed_filters[key] = processed_value
            elif isinstance(value, bool):
                processed_filters[key] = str(value).lower()
            else:
                processed_filters[key] = value

        return self._chain(filters={**self.filters, **processed_filters})

    def exclude(self, **kwargs: Any) -> Self:
        """
        Return a new QuerySet excluding objects with the given filters.

        Args:
            **kwargs: Filters to exclude, where keys are field names and values are
                excluded values. Supports the same lookup syntax as filter().

        Returns:
            A new QuerySet excluding objects that match the filters.

        Examples:
            Get documents with any correspondent except ID 1:

            >>> docs = client.documents().exclude(correspondent=1)

            Exclude documents with specific words in title:

            >>> docs = client.documents().exclude(title__contains="draft")

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

        This base implementation raises NotImplementedError. Subclasses like
        StandardQuerySet implement this method for models with ID fields.

        Args:
            pk: The primary key (e.g., the id) of the object to retrieve.

        Returns:
            A single object matching the query.

        Raises:
            ObjectNotFoundError: If no object is found.
            MultipleObjectsFoundError: If multiple objects match the query.
            NotImplementedError: If the method is not implemented by the subclass.

        Examples:
            Get document with ID 123:

            >>> doc = client.documents().get(123)

        """
        raise NotImplementedError("Getting a single resource is not defined by BaseModels without an id.")

    def _get_last_count(self) -> int | None:
        """
        Get the count from the last API response.

        Returns:
            The count from the last response, or None if not available.

        """
        if self._last_response is None:
            return None
        if isinstance(self._last_response, list):
            return len(self._last_response)
        return self._last_response.get("count")

    def count(self) -> int:
        """
        Return the total number of objects in the queryset.

        Makes an API request if necessary to determine the total count
        of objects matching the current filters.

        Returns:
            The total count of objects matching the filters.

        Raises:
            NotImplementedError: If the count cannot be determined from the API response.

        Examples:
            Count all documents:

            >>> total = client.documents().count()
            >>> print(f"Total documents: {total}")

            Count filtered documents:

            >>> invoice_count = client.documents().filter(title__contains="invoice").count()

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

        # If we have a last_response and it has 'results', count them
        if self._last_response and isinstance(self._last_response, dict) and "results" in self._last_response:
            return len(self._last_response["results"])

        # Fall back to counting the results we have already
        if self._fetch_all:
            return len(self._result_cache)

        # If we've tried everything and still can't get a count, raise an error
        raise NotImplementedError(
            f"Unexpected Error: Could not determine count of objects. Last response: {self._last_response}",
        )

    def count_this_page(self) -> int:
        """
        Return the number of objects on the current page.

        Counts only the objects on the current page of results,
        without fetching additional pages. Useful for pagination displays.

        Returns:
            The count of objects on the current page.

        Raises:
            NotImplementedError: If the current page count cannot be determined.

        Examples:
            Get count of current page:

            >>> page_count = client.documents().count_this_page()
            >>> print(f"Items on this page: {page_count}")

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

        Creates a copy of the current queryset with the same filters.
        Often used to create a new queryset instance for method chaining.

        Returns:
            A copy of the current QuerySet.

        Examples:
            Create a copy of a queryset:

            >>> all_docs = client.documents().all()

            Chain with other methods:

            >>> recent_docs = client.documents().all().order_by('-created')

        """
        return self._chain()

    def order_by(self, *fields: str) -> Self:
        """
        Return a new QuerySet ordered by the specified fields.

        Args:
            *fields: Field names to order by. Prefix with '-' for descending order.
                Multiple fields can be specified for multi-level sorting.

        Returns:
            A new QuerySet with the ordering applied.

        Examples:
            Order documents by title ascending:

            >>> docs = client.documents().order_by('title')

            Order by multiple fields (created date descending, then title ascending):

            >>> docs = client.documents().order_by('-created', 'title')

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

        Optimizes the API request by limiting to a single result when possible.

        Returns:
            The first object or None if no objects match.

        Examples:
            Get the first document:

            >>> first_doc = client.documents().first()
            >>> if first_doc:
            ...     print(f"First document: {first_doc.title}")

            Get the first document matching a filter:

            >>> first_invoice = client.documents().filter(title__contains="invoice").first()

        """
        if self._result_cache and len(self._result_cache) > 0:
            return self._result_cache[0]

        # If not cached, create a copy limited to 1 result
        results = list(self._chain(filters={**self.filters, "limit": 1}))
        return results[0] if results else None

    def last(self) -> _Model | None:
        """
        Return the last object in the QuerySet, or None if empty.

        Note:
            This method requires fetching all results to determine the last one,
            which may be inefficient for large result sets.

        Returns:
            The last object or None if no objects match.

        Examples:
            Get the last document:

            >>> last_doc = client.documents().last()
            >>> if last_doc:
            ...     print(f"Last document: {last_doc.title}")

            Get the last document in a specific order:

            >>> oldest_doc = client.documents().order_by('created').last()

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

        Optimizes the API request by checking for at least one result
        rather than fetching all results.

        Returns:
            True if there are any objects matching the filters.

        Examples:
            Check if any documents exist:

            >>> if client.documents().exists():
            ...     print("Documents found")

            Check if specific documents exist:

            >>> has_invoices = client.documents().filter(title__contains="invoice").exists()

        """
        # Check the cache before potentially making a new request
        if self._fetch_all or self._result_cache:
            return len(self._result_cache) > 0

        # Check if there's at least one result
        return self.first() is not None

    def none(self) -> Self:
        """
        Return an empty QuerySet.

        Creates a queryset that will always return no results,
        which is useful for conditional queries.

        Returns:
            An empty QuerySet.

        Examples:
            Create an empty queryset:

            >>> empty_docs = client.documents().none()
            >>> len(empty_docs)
            0

            Conditional query:

            >>> if condition:
            ...     docs = client.documents().filter(title__contains="invoice")
            ... else:
            ...     docs = client.documents().none()

        """
        return self._chain(filters={"limit": 0})

    def filter_field_by_str(self, field: str, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter a queryset based on a given string field.

        Allows subclasses to easily implement custom filter methods
        for string fields with consistent behavior.

        Args:
            field: The field name to filter by.
            value: The string value to filter against.
            exact: Whether to filter by an exact match (True) or contains (False).
            case_insensitive: Whether the filter should be case-insensitive.

        Returns:
            A new QuerySet instance with the filter applied.

        Examples:
            Filter documents by title (case-insensitive exact match):

            >>> docs = client.documents().filter_field_by_str('title', 'Invoice', exact=True)

            Filter documents by title containing text (case-insensitive):

            >>> docs = client.documents().filter_field_by_str('title', 'invoice', exact=False)

        """
        if exact:
            lookup = f"{field}__iexact" if case_insensitive else field
        else:
            lookup = f"{field}__icontains" if case_insensitive else f"{field}__contains"

        return self.filter(**{lookup: value})

    def _fetch_all_results(self) -> None:
        """
        Fetch all results from the API and populate the cache.

        Retrieves all results from the API by following pagination links
        and stores them in the internal cache for future access. Called internally
        when operations require the complete result set.

        Note:
            This is an internal method that should not be called directly by users.
            For large result sets, this may make multiple API requests.

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

    def _request_iter(
        self,
        url: str | HttpUrl | Template | None = None,
        params: dict[str, Any] | None = None,
    ) -> Iterator[_Model]:
        """
        Get an iterator of resources from the API.

        Makes a request to the API and returns an iterator over the resulting
        model instances. Updates internal state for pagination tracking.

        Args:
            url: The URL to request, if different from the resource's default.
            params: Query parameters to include in the request.

        Returns:
            An iterator over the model instances.

        Raises:
            NotImplementedError: If the request cannot be completed.

        Note:
            This is an internal method that should not be called directly by users.

        """
        if not (response := self.resource.request_raw(url=url, params=params)):
            logger.debug("No response from request.")
            return

        self._last_response = response

        yield from self.resource.handle_response(response)

    def _get_next(self, response: ClientResponse | None = None) -> str | None:
        """
        Get the next URL and adjust references accordingly.

        Updates the internal state to point to the next URL for
        pagination, if available. Also tracks visited URLs to prevent loops.

        Args:
            response: The response to use for determining the next URL.
                Defaults to the last response.

        Returns:
            The next URL, or None if there are no more pages.

        Note:
            This is an internal method that should not be called directly by users.

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
        Return a copy of the current QuerySet with updated attributes.

        Creates a new instance of the queryset with the same base attributes
        as the current one, but with specified attributes updated. Used internally
        for method chaining.

        Args:
            **kwargs: Attributes to update in the new QuerySet.

        Returns:
            A new QuerySet with the updated attributes.

        Note:
            This is an internal method that should not be called directly by users.

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

    def delete(self) -> Any:
        """
        Delete all objects in the queryset.

        The Base QuerySet calls a separate delete request for each object. Some
        child classes offer bulk deletion functionality that will perform it all
        in one request.

        """
        for model in self:
            model.delete()

    def update(self, **kwargs: Any) -> Self:
        """
        Update this model with new values.

        This is implemented by subclasses (i.e. StandardQuerySet) that have
        an ID field. This base implementation raises a NotImplementedError.

        Returns:
            Self: The chainable queryset

        """
        raise NotImplementedError("Update is not implemented for models without an id")

    @override
    def __iter__(self) -> Iterator[_Model]:
        """
        Iterate over the objects in the QuerySet.

        Implements lazy loading of results, fetching additional pages
        as needed when iterating through the queryset.

        Returns:
            An iterator over the model instances.

        Examples:
            Iterate through documents:

            >>> for doc in client.documents():
            ...     print(doc.title)

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

        Calls count() to determine the total number of objects
        matching the current filters.

        Returns:
            The count of objects.

        Examples:
            Get the number of documents:

            >>> num_docs = len(client.documents())
            >>> print(f"Total documents: {num_docs}")

        """
        return self.count()

    def __bool__(self) -> bool:
        """
        Return True if the QuerySet has any results.

        Calls exists() to check if any objects match the current filters.

        Returns:
            True if there are any objects matching the filters.

        Examples:
            Check if any documents exist:

            >>> if client.documents():
            ...     print("Documents found")

        """
        return self.exists()

    def __getitem__(self, key: int | slice) -> _Model | list[_Model]:
        """
        Retrieve an item or slice of items from the QuerySet.

        Supports both integer indexing and slicing, optimizing
        API requests when possible by using limit and offset parameters.

        Args:
            key: An integer index or slice object.

        Returns:
            A single object or list of objects.

        Raises:
            IndexError: If the index is out of range.

        Examples:
            Get a single document by position:

            >>> first_doc = client.documents()[0]

            Get a slice of documents:

            >>> recent_docs = client.documents().order_by('-created')[:10]

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

        Checks if the given object is present in the queryset
        by comparing it with each object in the queryset.

        Args:
            item: The object to check for.

        Returns:
            True if the object is in the QuerySet.

        Examples:
            Check if a document is in a queryset:

            >>> doc = client.documents().get(123)
            >>> if doc in client.documents().filter(title__contains="invoice"):
            ...     print("Document is an invoice")

        """
        if not isinstance(item, self._model):
            return False

        return any(obj == item for obj in self)


class StandardQuerySet[_Model: StandardModel](BaseQuerySet[_Model]):
    """
    A queryset for StandardModel instances with ID fields.

    Extends BaseQuerySet to provide additional functionality specific
    to models with standard fields like 'id', including direct lookups by ID,
    bulk operations, and specialized filtering methods.

    Attributes:
        resource: The StandardResource instance associated with the queryset.

    Examples:
        Get documents by ID:

        >>> doc = client.documents().get(123)

        Filter documents by ID:

        >>> docs = client.documents().id([1, 2, 3])

        Perform bulk operations:

        >>> client.documents().filter(title__contains="draft").delete()

    """

    resource: "StandardResource[_Model, Self]"  # type: ignore # pyright is getting inheritance wrong

    @override
    def get(self, pk: int) -> _Model:
        """
        Retrieve a single object from the API by its ID.

        First checks the result cache for an object with the given ID,
        then falls back to making a direct API request if not found.

        Args:
            pk: The ID of the object to retrieve.

        Returns:
            A single object matching the ID.

        Raises:
            ObjectNotFoundError: If no object with the given ID exists.

        Examples:
            Get document with ID 123:

            >>> doc = client.documents().get(123)
            >>> print(f"Retrieved: {doc.title}")

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

        Provides a convenient way to filter objects by their ID
        or a list of IDs.

        Args:
            value: The ID or list of IDs to filter by.

        Returns:
            Filtered QuerySet containing only objects with the specified ID(s).

        Examples:
            Get document with ID 123:

            >>> doc = client.documents().id(123).first()

            Get multiple documents by ID:

            >>> docs = client.documents().id([123, 456, 789])
            >>> for doc in docs:
            ...     print(doc.title)

        """
        if isinstance(value, list):
            return self.filter(id__in=value)
        return self.filter(id=value)

    @override
    def update(self, **kwargs: Any) -> Self:
        """
        Update all objects in the queryset with the given values.

        Unless called on a model that supports bulk updates, this method
        will iterate over each object and call its update method individually,
        resulting in multiple API requests.

        Returns:
            The updated QuerySet instance.

        """
        for model in self:
            model.update(**kwargs)
        return self._chain()

    @override
    def __contains__(self, item: Any) -> bool:
        """
        Return True if the QuerySet contains the given object.

        Checks if an object with the same ID is in the queryset.
        Can accept either a model instance or an integer ID.

        Note:
            This method only ensures a match by ID, not by full object equality.
            This is intentional, as the object may be outdated or not fully populated.

        Args:
            item: The object or ID to check for.

        Returns:
            True if an object with the matching ID is in the QuerySet.

        Examples:
            Check if a document is in a queryset:

            >>> doc = client.documents().get(123)
            >>> if doc in client.documents().filter(title__contains="invoice"):
            ...     print("Document is an invoice")

            Check if a document ID is in a queryset:

            >>> if 123 in client.documents().filter(title__contains="invoice"):
            ...     print("Document 123 is an invoice")

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


class BaseQuerySetProtocol[_Model: BaseModel](Protocol):
    resource: "BaseResource"

    def filter(self, **kwargs: Any) -> Self: ...
    def exclude(self, **kwargs: Any) -> Self: ...
    def all(self) -> Self: ...
    def order_by(self, *fields: str) -> Self: ...
    def first(self) -> _Model | None: ...
    def last(self) -> _Model | None: ...
    def exists(self) -> bool: ...
    def none(self) -> Self: ...
    def count(self) -> int: ...
    def count_this_page(self) -> int: ...
    def __iter__(self) -> Iterator[_Model]: ...
    def __len__(self) -> int: ...
    def __bool__(self) -> bool: ...
    def __getitem__(self, key: int | slice) -> _Model | list[_Model]: ...
    def __contains__(self, item: Any) -> bool: ...


class BulkQuerySet[_Model: StandardModel](StandardQuerySet[_Model]):
    def _bulk_action(self, action: str, **kwargs: Any) -> ClientResponse:
        """
        Perform a bulk action on all objects in the queryset.

        Fetches all IDs in the queryset and passes them to the
        resource's bulk_action method, allowing operations to be performed
        on multiple objects in a single API request.

        Args:
            action: The action to perform (e.g., "delete", "merge").
            **kwargs: Additional parameters for the action.

        Returns:
            The API response containing results of the bulk action.

        Raises:
            NotImplementedError: If the resource doesn't support bulk actions.

        Examples:
            Delete all documents with "draft" in the title:

            >>> client.documents().filter(title__contains="draft")._bulk_action("delete")

            Merge documents with custom parameters:

            >>> client.documents().filter(correspondent_id=5)._bulk_action(
            ...     "merge",
            ...     metadata_document_id=123
            ... )

        """
        if not (fn := getattr(self.resource, "_bulk_operation", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk actions")

        # Fetch all IDs in the queryset
        # We only need IDs, so optimize by requesting just the ID field if possible
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids=ids, operation=action, **kwargs)

    @override
    def delete(self) -> ClientResponse:
        """
        Delete all objects in the queryset.

        This is a convenience method that calls _bulk_action("delete").

        Returns:
            The API response containing results of the delete operation.

        Examples:
            Delete all documents with "draft" in the title:

            >>> client.documents().filter(title__contains="draft").delete()

            Delete old documents:

            >>> from datetime import datetime, timedelta
            >>> one_year_ago = (datetime.now() - timedelta(days=365)).isoformat()
            >>> client.documents().filter(created__lt=one_year_ago).delete()

        """
        # Fetch all IDs in the queryset
        # We only need IDs, so optimize by requesting just the ID field if possible
        ids = [obj.id for obj in self]

        return self.resource.delete(ids)  # type: ignore # Not sure why pyright is complaining

    @override
    def update(self, **kwargs: Any) -> Self:
        """
        Update all objects in the queryset with the given values.

        Allows updating multiple objects with the same field values
        in a single API request.

        Args:
            **kwargs: Fields to update and their new values.

        Returns:
            The API response containing results of the update operation.

        Raises:
            NotImplementedError: If the resource doesn't support bulk updates.

        Examples:
            Update the correspondent for all documents with "invoice" in the title:

            >>> client.documents().filter(title__contains="invoice").bulk_update(
            ...     correspondent=5,
            ...     document_type=3
            ... )

        """
        if not (fn := getattr(self.resource, "bulk_update", None)):
            return super().update(**kwargs)

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return self

        fn(ids, **kwargs)

        return self._chain()

    def assign_owner(self, owner_id: int) -> ClientResponse:
        """
        Assign an owner to all objects in the queryset.

        Sets the owner for all objects in the queryset
        to the specified owner ID.

        Args:
            owner_id: Owner ID to assign.

        Returns:
            The API response containing results of the operation.

        Raises:
            NotImplementedError: If the resource doesn't support bulk owner assignment.

        Examples:
            Set owner for all personal documents:

            >>> client.documents().filter(title__contains="personal").assign_owner(1)

        """
        if not (fn := getattr(self.resource, "assign_owner", None)):
            raise NotImplementedError(f"Resource {self.resource.name} does not support bulk owner assignment")

        # Fetch all IDs in the queryset
        ids = [obj.id for obj in self]

        if not ids:
            return {"success": True, "count": 0}

        return fn(ids, owner_id)
