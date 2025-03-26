"""
Provide base resource classes for interacting with Paperless-NgX API endpoints.

This module contains the foundation classes for all API resources in Paperap.
Resources handle communication with the Paperless-NgX API, including request
formatting, response parsing, and model instantiation.

Each resource corresponds to an API endpoint in Paperless-NgX and provides
methods for retrieving, creating, updating, and deleting resources.
"""

from __future__ import annotations

import copy
import logging
from abc import ABC, ABCMeta
from string import Template
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, Iterator, Protocol, overload, override

from pydantic import HttpUrl, field_validator
from typing_extensions import TypeVar

from paperap.const import URLS, ClientResponse, Endpoints
from paperap.exceptions import (
    ConfigurationError,
    ModelValidationError,
    ObjectNotFoundError,
    ResourceNotFoundError,
    ResponseParsingError,
)
from paperap.signals import registry

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.models.abstract.model import BaseModel, StandardModel
    from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

_BaseModel = TypeVar("_BaseModel", bound="BaseModel", default="BaseModel")
_BaseQuerySet = TypeVar("_BaseQuerySet", bound="BaseQuerySet[Any]", default="BaseQuerySet")
_StandardModel = TypeVar("_StandardModel", bound="StandardModel", default="StandardModel")
_StandardQuerySet = TypeVar("_StandardQuerySet", bound="StandardQuerySet[Any]", default="StandardQuerySet")

logger = logging.getLogger(__name__)


class BaseResource(ABC, Generic[_BaseModel, _BaseQuerySet]):
    """
    Base class for API resources.

    Provides the foundation for all API resources in Paperap. Handles communication
    with the Paperless-NgX API, including request formatting, response parsing,
    and model instantiation.

    Each resource corresponds to an API endpoint in Paperless-NgX and provides
    methods for retrieving, creating, updating, and deleting resources.

    Args:
        client: PaperlessClient instance for making API requests.

    Attributes:
        model_class: Model class for this resource.
        queryset_class: QuerySet class for this resource.
        client: PaperlessClient instance.
        name: Name of the resource (defaults to model name + 's').
        endpoints: Dictionary of API endpoint templates.

    Examples:
        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>> resource = DocumentResource(client)
        >>> documents = resource.all()
        >>> for doc in documents[:5]:  # Get first 5 documents
        ...     print(doc.title)

    """

    # The model class for this resource.
    model_class: type[_BaseModel]
    queryset_class: type[_BaseQuerySet]

    # The PaperlessClient instance.
    client: "PaperlessClient"
    # The name of the model. This must line up with the API endpoint
    # It will default to the model's name
    name: str
    # The API endpoint for this model.
    # It will default to a standard schema used by the API
    # Setting it will allow you to contact a different schema or even a completely different API.
    # this will usually not need to be overridden
    endpoints: ClassVar[Endpoints]

    def __init__(self, client: "PaperlessClient") -> None:
        """
        Initialize the resource with a client instance.

        Sets up the resource with the client, configures endpoints, and establishes
        the relationship between the resource and its model class.

        Args:
            client: PaperlessClient instance for making API requests.

        """
        self.client = client
        if not hasattr(self, "name"):
            self.name = f"{self._meta.name.lower()}s"

        # Allow templating
        for key, value in self.endpoints.items():
            # endpoints is always dict[str, Template]
            self.endpoints[key] = Template(value.safe_substitute(resource=self.name))

        # Ensure the model has a link back to this resource
        self.model_class._resource = self  # type: ignore # allow private access

        super().__init__()

    @override
    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize the subclass with required attributes.

        Validates that subclasses define required attributes like model_class
        and sets up default endpoints if not explicitly defined.

        Args:
            **kwargs: Arbitrary keyword arguments passed to parent __init_subclass__.

        Raises:
            ConfigurationError: If model_class is not defined in the subclass.

        """
        super().__init_subclass__(**kwargs)

        # Skip processing for the base class itself. TODO: This is a hack
        if cls.__name__ in ["BaseResource", "StandardResource"]:
            return

        # model_class is required
        if not (_model_class := getattr(cls, "model_class", None)):
            raise ConfigurationError(f"model_class must be defined in {cls.__name__}")

        # API Endpoint must be defined
        if not (endpoints := getattr(cls, "endpoints", {})):
            endpoints = {
                "list": URLS.list,
                "detail": URLS.detail,
                "create": URLS.create,
                "update": URLS.update,
                "delete": URLS.delete,
            }

        cls.endpoints = cls._validate_endpoints(endpoints)  # type: ignore # Allow assigning in subclass

    @property
    def _meta(self) -> "BaseModel.Meta[_BaseModel]":
        """
        Get the Meta class of the model.

        Returns:
            Meta class instance from the model_class.

        """
        return self.model_class._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    @classmethod
    def _validate_endpoints(cls, value: Any) -> Endpoints:
        """
        Validate and convert endpoint definitions to Templates.

        Args:
            value: Endpoints dictionary to validate.

        Returns:
            Dictionary of validated endpoint Templates.

        Raises:
            ModelValidationError: If endpoints are not properly formatted.

        """
        if not isinstance(value, dict):
            raise ModelValidationError("endpoints must be a dictionary")

        converted: Endpoints = {}
        for k, v in value.items():
            if isinstance(v, Template):
                converted[k] = v
                continue

            if not isinstance(v, str):
                raise ModelValidationError(f"endpoints[{k}] must be a string or template")

            try:
                converted[k] = Template(v)
            except ValueError as e:
                raise ModelValidationError(f"endpoints[{k}] is not a valid template: {e}") from e

        # We validated that converted matches endpoints above
        return converted

    def _bulk_operation(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("_bulk_operation method not available for resources without an id")

    def get_endpoint(self, name: str, **kwargs: Any) -> str | HttpUrl:
        """
        Get a fully-formed URL for the specified endpoint.

        Retrieves the endpoint template, substitutes any parameters, and ensures
        the URL is properly formatted with the base URL if needed.

        Args:
            name: Name of the endpoint (e.g., "list", "detail").
            **kwargs: Parameters to substitute in the endpoint template.

        Returns:
            Fully-formed URL for the endpoint.

        Raises:
            ConfigurationError: If the requested endpoint is not defined.

        Examples:
            >>> resource.get_endpoint("detail", pk=123)
            'https://paperless.example.com/api/documents/123/'

        """
        if not (template := self.endpoints.get(name, None)):
            raise ConfigurationError(f"Endpoint {name} not defined for resource {self.name}")

        if "resource" not in kwargs:
            kwargs["resource"] = self.name

        url = template.safe_substitute(**kwargs)

        if not url.startswith("http"):
            url = f"{self.client.base_url}{url.lstrip('/')}"

        return HttpUrl(url)

    def all(self) -> _BaseQuerySet:
        """
        Return a QuerySet representing all objects of this resource type.

        Creates a new QuerySet instance for this resource without any filters.

        Returns:
            QuerySet for this resource.

        Examples:
            >>> all_documents = client.documents.all()
            >>> for doc in all_documents:
            ...     print(doc.title)

        """
        return self.queryset_class(self)  # type: ignore # _meta.queryset is always the right queryset type

    def filter(self, **kwargs: Any) -> _BaseQuerySet:
        """
        Return a QuerySet filtered by the given parameters.

        Creates a new QuerySet with filters applied. Filters use Django-style
        field lookups (e.g., field__contains, field__gt).

        Args:
            **kwargs: Filter parameters as field=value pairs.

        Returns:
            Filtered QuerySet.

        Examples:
            >>> invoices = client.documents.filter(
            ...     title__contains="invoice",
            ...     created__gt="2023-01-01"
            ... )

        """
        return self.all().filter(**kwargs)

    def get(self, *args: Any, **kwargs: Any) -> _BaseModel:
        """
        Get a model by ID.

        This is a base method that raises NotImplementedError.
        Subclasses should implement this method to retrieve a specific model by ID.

        Args:
            *args: Positional arguments (typically model_id).
            **kwargs: Additional keyword arguments.

        Returns:
            Retrieved model.

        Raises:
            NotImplementedError: This base method is not implemented.

        """
        raise NotImplementedError("get method not available for resources without an id")

    def create(self, **kwargs: Any) -> _BaseModel:
        """
        Create a new resource.

        Sends a POST request to the API to create a new resource with the provided data.
        Emits signals before and after the creation.

        Args:
            **kwargs: Resource data as field=value pairs.

        Returns:
            Newly created model instance.

        Raises:
            ConfigurationError: If the create endpoint is not defined.
            ResourceNotFoundError: If the resource cannot be created.

        Examples:
            >>> tag = client.tags.create(
            ...     name="Invoices",
            ...     color="#ff0000"
            ... )

        """
        # Signal before creating resource
        signal_params = {"resource": self.name, "data": kwargs}
        registry.emit("resource.create:before", "Emitted before creating a resource", kwargs=signal_params)

        if not (url := self.get_endpoint("create", resource=self.name)):
            raise ConfigurationError(f"Create endpoint not defined for resource {self.name}")

        if not (response := self.client.request("POST", url, data=kwargs)):
            raise ResourceNotFoundError("Resource {resource} not found after create.", resource_name=self.name)

        model = self.parse_to_model(response)

        # Signal after creating resource
        registry.emit(
            "resource.create:after",
            "Emitted after creating a resource",
            args=[self],
            kwargs={"model": model, **signal_params},
        )

        return model

    def update(self, model: _BaseModel) -> _BaseModel:
        """
        Update a resource.

        This is a base method that raises NotImplementedError.
        Subclasses should implement this method to update a model.

        Args:
            model: Model instance to update.

        Returns:
            Updated model instance.

        Raises:
            NotImplementedError: This base method is not implemented.

        """
        raise NotImplementedError("update method not available for resources without an id")

    def update_dict(self, *args: Any, **kwargs: Any) -> _BaseModel:
        """
        Update a resource using a dictionary of values.

        This is a base method that raises NotImplementedError.
        Subclasses should implement this method to update a model using a dictionary.

        Args:
            *args: Positional arguments (typically model_id).
            **kwargs: Field values to update.

        Returns:
            Updated model instance.

        Raises:
            NotImplementedError: This base method is not implemented.

        """
        raise NotImplementedError("update_dict method not available for resources without an id")

    def delete(self, *args: Any, **kwargs: Any) -> ClientResponse:
        """
        Delete a resource.

        This is a base method that raises NotImplementedError.
        Subclasses should implement this method to delete a model.

        Args:
            *args: Positional arguments (typically model_id).
            **kwargs: Additional keyword arguments.

        Raises:
            NotImplementedError: This base method is not implemented.

        """
        raise NotImplementedError("delete method not available for resources without an id")

    def parse_to_model(self, item: dict[str, Any]) -> _BaseModel:
        """
        Parse an item dictionary into a model instance.

        Transforms the raw API data and validates it against the model class.

        Args:
            item: Dictionary of data from the API.

        Returns:
            Validated model instance.

        Raises:
            ResponseParsingError: If the data cannot be parsed into a valid model.

        """
        try:
            data = self.transform_data_input(**item)
            return self.model_class.model_validate(data)
        except Exception as e:
            logger.error('Error parsing model "%s" with data: %s -> %s', self.name, item, e)
            raise

    def transform_data_input(self, **data: Any) -> dict[str, Any]:
        """
        Transform data after receiving it from the API.

        Maps API field names to model field names using the field_map defined
        in the model's Meta class.

        Args:
            **data: Raw data from the API.

        Returns:
            Transformed data ready for model validation.

        """
        for key, value in self._meta.field_map.items():
            if key in data:
                data[value] = data.pop(key)
        return data

    @overload
    def transform_data_output(self, model: _BaseModel, exclude_unset: bool = True) -> dict[str, Any]: ...

    @overload
    def transform_data_output(self, **data: Any) -> dict[str, Any]: ...

    def transform_data_output(
        self,
        model: _BaseModel | None = None,
        exclude_unset: bool = True,
        **data: Any,
    ) -> dict[str, Any]:
        """
        Transform data before sending it to the API.

        Maps model field names to API field names using the field_map defined
        in the model's Meta class.

        Args:
            model: Model instance to transform. If provided, its to_dict() method is used.
            exclude_unset: If model is provided, whether to exclude unset fields.
            **data: Raw data to transform if no model is provided.

        Returns:
            Transformed data ready to send to the API.

        Raises:
            ValueError: If both model and data are provided.

        """
        if model:
            if data:
                # Combining model.to_dict() and data is ambiguous, so not allowed.
                raise ValueError("Only one of model or data should be provided")
            data = model.to_dict(exclude_unset=exclude_unset)

        for key, value in self._meta.field_map.items():
            if value in data:
                data[key] = data.pop(value)
        return data

    def create_model(self, **kwargs: Any) -> _BaseModel:
        """
        Create a new model instance without saving to the API.

        Instantiates a new model with the provided field values and associates
        it with this resource.

        Args:
            **kwargs: Model field values.

        Returns:
            New, unsaved model instance.

        Examples:
            >>> doc = client.documents.create_model(
            ...     title="New Document",
            ...     correspondent_id=5
            ... )
            >>> doc.save()  # Save to the API

        """
        # Mypy output:
        # base.py:326:52: error: Argument "resource" to "BaseModel" has incompatible type
        # "BaseResource[_BaseModel, _BaseQuerySet]"; expected "BaseResource[BaseModel, BaseQuerySet[BaseModel]] | None
        return self.model_class(**kwargs, resource=self)  # type: ignore

    def request_raw(
        self,
        url: str | Template | HttpUrl | None = None,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """
        Make an HTTP request to the API and return the raw JSON response.

        A low-level method to send requests to the API without processing the response
        into model instances.

        Args:
            url: URL to request. If None, uses the list endpoint.
            method: HTTP method to use (GET, POST, PUT, DELETE).
            params: Query parameters to include in the request.
            data: Request body data for POST/PUT requests.

        Returns:
            JSON-decoded response from the API.

        Raises:
            ConfigurationError: If no URL is provided and the list endpoint is not defined.

        Examples:
            >>> # Get raw data from a custom endpoint
            >>> response = resource.request_raw(
            ...     url="https://paperless.example.com/api/custom/",
            ...     params={"filter": "value"}
            ... )

        """
        if not url and not (url := self.get_endpoint("list", resource=self.name)):
            raise ConfigurationError(f"List endpoint not defined for resource {self.name}")

        if isinstance(url, Template):
            url = url.safe_substitute(resource=self.name)

        response = self.client.request(method, url, params=params, data=data)
        return response

    def handle_response(self, response: Any) -> Iterator[_BaseModel]:
        """
        Process API response and yield model instances.

        Handles different response formats (list or dict) and emits signals
        before and after processing.

        Args:
            response: API response to process.

        Yields:
            Model instances created from the response data.

        Raises:
            ResponseParsingError: If the response format is unexpected.

        """
        registry.emit(
            "resource._handle_response:before",
            "Emitted before listing resources",
            return_type=dict[str, Any],
            args=[self],
            kwargs={"response": response, "resource": self.name},
        )

        if isinstance(response, list):
            yield from self.handle_results(response)
        elif isinstance(response, dict):
            yield from self.handle_dict_response(**response)
        else:
            raise ResponseParsingError(f"Expected response to be list/dict, got {type(response)} -> {response}")

        registry.emit(
            "resource._handle_response:after",
            "Emitted after listing resources",
            return_type=dict[str, Any],
            args=[self],
            kwargs={"response": response, "resource": self.name},
        )

    def handle_dict_response(self, **response: dict[str, Any]) -> Iterator[_BaseModel]:
        """
        Handle a dictionary response from the API and yield model instances.

        Processes responses that are dictionaries, which may contain a 'results' key
        with a list of items or may be a single item directly.

        Args:
            **response: Dictionary response from the API.

        Yields:
            Model instances created from the response data.

        Raises:
            ResponseParsingError: If the response format is unexpected.

        """
        if not (results := response.get("results", response)):
            return

        # Signal after receiving response
        registry.emit(
            "resource._handle_response:after",
            "Emitted after list response, before processing",
            args=[self],
            kwargs={"response": {**response}, "resource": self.name, "results": results},
        )

        # If this is a single-item response (not a list), handle it differently
        if isinstance(results, dict):
            # For resources that return a single object directly
            registry.emit(
                "resource._handle_results:before",
                "Emitted for direct object response",
                args=[self],
                kwargs={"resource": self.name, "item": {**results}},
            )
            yield self.parse_to_model(results)
            return

        if isinstance(results, list):
            yield from self.handle_results(results)
            return

        raise ResponseParsingError(f"Expected {self.name} results to be list/dict, got {type(results)} -> {results}")

    def handle_results(self, results: list[dict[str, Any]]) -> Iterator[_BaseModel]:
        """
        Yield parsed models from a list of results.

        Processes a list of dictionaries into model instances, emitting signals
        for each item.

        Args:
            results: List of dictionaries from the API.

        Yields:
            Model instances created from the results.

        Raises:
            ResponseParsingError: If the results format is unexpected.

        """
        if not isinstance(results, list):
            raise ResponseParsingError(f"Expected {self.name} results to be a list, got {type(results)} -> {results}")

        for item in results:
            if not isinstance(item, dict):
                raise ResponseParsingError(f"Expected type of elements in results is dict, got {type(item)}")

            registry.emit(
                "resource._handle_results:before",
                "Emitted for each item in a list response",
                args=[self],
                kwargs={"resource": self.name, "item": {**item}},
            )
            yield self.parse_to_model(item)

    def __call__(self, *args: Any, **keywords: Any) -> _BaseQuerySet:
        """
        Make the resource callable to get a filtered QuerySet.

        This allows for a shorthand syntax when filtering resources.

        Args:
            *args: Unused positional arguments.
            **keywords: Filter parameters as field=value pairs.

        Returns:
            Filtered QuerySet.

        Examples:
            >>> # These are equivalent:
            >>> client.documents(title__contains='invoice')
            >>> client.documents.filter(title__contains='invoice')

        """
        return self.filter(**keywords)


class StandardResource(BaseResource[_StandardModel, _StandardQuerySet]):
    """
    Base class for API resources with standard ID-based operations.

    Extends BaseResource with implementations for get, update, and delete
    operations that work with models having an 'id' field.

    This class is used for most Paperless-NgX resources that follow the standard
    REST pattern with unique integer IDs.

    Args:
        client: PaperlessClient instance for making API requests.

    Examples:
        >>> from paperap import PaperlessClient
        >>> client = PaperlessClient()
        >>> resource = TagResource(client)
        >>> tag = resource.get(5)  # Get tag with ID 5
        >>> tag.name = "New Name"
        >>> resource.update(tag)   # Update the tag

    """

    @override
    def get(self, model_id: int, *args: Any, **kwargs: Any) -> _StandardModel:
        """
        Get a model within this resource by ID.

        Retrieves a specific model by its ID, emitting signals before and after
        the operation.

        Args:
            model_id: ID of the model to retrieve.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Retrieved model instance.

        Raises:
            ConfigurationError: If the detail endpoint is not defined.
            ObjectNotFoundError: If the model with the given ID does not exist.

        Examples:
            >>> document = client.documents.get(123)
            >>> print(document.title)

        """
        # Signal before getting resource
        signal_params = {"resource": self.name, "model_id": model_id}
        registry.emit("resource.get:before", "Emitted before getting a resource", args=[self], kwargs=signal_params)

        if not (url := self.get_endpoint("detail", resource=self.name, pk=model_id)):
            raise ConfigurationError(f"Get detail endpoint not defined for resource {self.name}")

        if not (response := self.client.request("GET", url)):
            raise ObjectNotFoundError(resource_name=self.name, model_id=model_id)

        # If the response doesn't have an ID, it's likely a 404
        if not response.get("id"):
            message = response.get("detail") or f"No ID found in {self.name} response"
            raise ObjectNotFoundError(message, resource_name=self.name, model_id=model_id)

        model = self.parse_to_model(response)

        # Signal after getting resource
        registry.emit(
            "resource.get:after",
            "Emitted after getting a single resource by id",
            args=[self],
            kwargs={**signal_params, "model": model},
        )

        return model

    @override
    def update(self, model: _StandardModel) -> _StandardModel:
        """
        Update a model in the API.

        Converts the model to a dictionary and sends it to the API for updating.

        Args:
            model: Model instance to update.

        Returns:
            Updated model instance.

        Examples:
            >>> tag = client.tags.get(5)
            >>> tag.name = "Updated Name"
            >>> updated_tag = client.tags.update(tag)

        """
        data = model.to_dict()
        data = self.transform_data_output(**data)

        # Save the model ID
        model_id = model.id

        # Remove ID from the data dict to avoid duplicating it in the call
        data.pop("id", None)

        return self.update_dict(model_id, **data)

    @override
    def delete(self, model: int | _StandardModel | list[int | _StandardModel]) -> ClientResponse:
        if isinstance(model, list):
            return self._delete_multiple(model)
        return self._delete_single(model)

    def _delete_multiple(self, models: list[int | _StandardModel]) -> ClientResponse:
        for model in models:
            _response = self._delete_single(model)

        return None  # TODO

    def _delete_single(self, model: int | _StandardModel) -> ClientResponse:
        """
        Delete a resource from the API.

        Sends a DELETE request to remove the resource, emitting signals before
        and after the operation.

        Args:
            model_id: ID of the resource or the model instance to delete.

        Raises:
            ValueError: If model_id is not provided.
            ConfigurationError: If the delete endpoint is not defined.

        Examples:
            >>> # Delete by ID
            >>> client.tags.delete(5)
            >>>
            >>> # Delete by model instance
            >>> tag = client.tags.get(5)
            >>> client.tags.delete(tag)

        """
        if not model:
            raise ValueError("model_id is required to delete a resource")
        if not isinstance(model, int):
            model = model.id

        # Signal before deleting resource
        signal_params = {"resource": self.name, "model_id": model}
        registry.emit("resource.delete:before", "Emitted before deleting a resource", args=[self], kwargs=signal_params)

        if not (url := self.get_endpoint("delete", resource=self.name, pk=model)):
            raise ConfigurationError(f"Delete endpoint not defined for resource {self.name}")

        result = self.client.request("DELETE", url)

        # Signal after deleting resource
        registry.emit("resource.delete:after", "Emitted after deleting a resource", args=[self], kwargs=signal_params)

        return result

    @override
    def update_dict(self, model_id: int, **data: dict[str, Any]) -> _StandardModel:
        """
        Update a resource using a dictionary of values.

        Sends a PUT request to update the resource with the provided data,
        emitting signals before and after the operation.

        Args:
            model_id: ID of the resource to update.
            **data: Field values to update.

        Returns:
            Updated model instance.

        Raises:
            ConfigurationError: If the update endpoint is not defined.
            ResourceNotFoundError: If the resource with the given ID is not found.

        Examples:
            >>> updated_tag = client.tags.update_dict(
            ...     5,
            ...     name="New Name",
            ...     color="#ff0000"
            ... )

        """
        # Signal before updating resource
        signal_params = {"resource": self.name, "model_id": model_id, "data": data}
        registry.emit("resource.update:before", "Emitted before updating a resource", kwargs=signal_params)

        if not (url := self.get_endpoint("update", resource=self.name, pk=model_id)):
            raise ConfigurationError(f"Update endpoint not defined for resource {self.name}")

        if not (response := self.client.request("PUT", url, data=data)):
            raise ResourceNotFoundError("Resource ${resource} not found after update.", resource_name=self.name)

        model = self.parse_to_model(response)

        # Signal after updating resource
        registry.emit(
            "resource.update:after",
            "Emitted after updating a resource",
            args=[self],
            kwargs={**signal_params, "model": model},
        )

        return model


class BaseResourceProtocol[_BaseModel: "BaseModel", _BaseQuerySet: "BaseQuerySet"](Protocol):
    model_class: type[_BaseModel]
    queryset_class: type[_BaseQuerySet]
    name: str
    endpoints: ClassVar[Endpoints]
    client: "PaperlessClient"

    def get_endpoint(self, name: str, **kwargs: Any) -> str | HttpUrl: ...
    def all(self) -> _BaseQuerySet: ...
    def filter(self, **kwargs: Any) -> _BaseQuerySet: ...
    def get(self, model_id: int, *args: Any, **kwargs: Any) -> _BaseModel: ...
    def create(self, **kwargs: Any) -> _BaseModel: ...
    def update(self, model: _BaseModel) -> _BaseModel: ...
    def update_dict(self, model_id: int, **data: dict[str, Any]) -> _BaseModel: ...
    def delete(self, model: int | _BaseModel | list[int | _BaseModel]) -> ClientResponse: ...
    def parse_to_model(self, item: dict[str, Any]) -> _BaseModel: ...
    def transform_data_input(self, **data: Any) -> dict[str, Any]: ...
    def transform_data_output(
        self,
        model: _BaseModel | None = None,
        exclude_unset: bool = True,
        **data: Any,
    ) -> dict[str, Any]: ...
    def create_model(self, **kwargs: Any) -> _BaseModel: ...
    def request_raw(
        self,
        url: str | Template | HttpUrl | None = None,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None: ...
    def handle_response(self, response: Any) -> Iterator[_BaseModel]: ...
    def handle_dict_response(self, **response: dict[str, Any]) -> Iterator[_BaseModel]: ...
    def handle_results(self, results: list[dict[str, Any]]) -> Iterator[_BaseModel]: ...
    def _bulk_operation(self, *args: Any, **kwargs: Any) -> Any: ...
    def __call__(self, *args: Any, **keywords: Any) -> _BaseQuerySet: ...


class BulkEditingMixin[_Model: "StandardModel"]:
    def _bulk_operation(
        self: BaseResourceProtocol,  # type: ignore
        ids: list[int],
        operation: str,
        **kwargs: Any,
    ) -> ClientResponse:
        """
        Perform a bulk operation on multiple objects through the generic bulk edit endpoint.

        This is a low-level method that handles communication with the bulk_edit_objects
        endpoint in Paperless-NGX.

        Args:
            ids: List of object IDs to operate on.
            operation: Operation to perform ('delete', 'set_permissions', etc.)
            **kwargs: Additional parameters for the operation.

        Returns:
            API response dictionary.

        Raises:
            ValueError: If the operation is not valid.

        """
        if operation not in ("set_permissions", "delete"):
            raise ValueError(f"Invalid operation '{operation}'. Must be 'set_permissions' or 'delete'")

        # Signal before bulk action
        signal_params = {
            "resource": self.name,
            "operation": operation,
            "ids": ids,
            **kwargs,
        }
        registry.emit(
            "resource.bulk_operation:before",
            "Emitted before bulk operation",
            args=[self],
            kwargs=signal_params,
        )

        data: dict[str, Any] = {
            "objects": ids,
            "object_type": self.name,
            "operation": operation,
            **kwargs,
        }

        # Use the special endpoint for bulk editing objects
        url = HttpUrl(f"{self.client.base_url}/api/bulk_edit_objects/")

        response = self.client.request("POST", url, data=data)

        # Signal after bulk action
        registry.emit(
            "resource.bulk_operation:after",
            "Emitted after bulk operation",
            args=[self],
            kwargs={**signal_params, "response": response},
        )

        return response

    def set_permissions(
        self: BaseResourceProtocol,  # type: ignore
        model_ids: int | list[int],
        permissions: dict[str, Any] | None = None,
        owner_id: int | None = None,
        merge: bool = False,
    ) -> ClientResponse:
        """
        Set permissions for one or multiple resources.

        Args:
            model_ids: Single ID or list of IDs to update permissions for.
            permissions: Permissions object defining user and group permissions.
            owner_id: Owner ID to assign to the resources.
            merge: Whether to merge with existing permissions (True) or replace them (False).

        Returns:
            API response dictionary.

        Examples:
            >>> # Set permissions for a single item
            >>> client.tags.set_permissions(5,
            ...     permissions={"view": {"users": [1]}},
            ...     owner_id=1
            ... )
            >>>
            >>> # Set permissions for multiple items
            >>> client.tags.set_permissions([1, 2, 3],
            ...     permissions={"view": {"users": [1, 2]}, "change": {"groups": [1]}},
            ...     owner_id=2,
            ...     merge=True
            ... )

        """
        # Create params dictionary
        params: dict[str, Any] = {"merge": merge}
        if permissions:
            params["permissions"] = permissions
        if owner_id is not None:
            params["owner"] = owner_id

        # Handle single ID
        if isinstance(model_ids, int):
            model_ids = [model_ids]

        return self._bulk_operation(ids=model_ids, operation="set_permissions", **params)  # type: ignore # allow protected access

    def _delete_multiple(self, models: list[int | _Model]) -> ClientResponse:
        return self._bulk_operation(ids=models, operation="delete")  # type: ignore # allow protected access
