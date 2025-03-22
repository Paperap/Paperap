"""




----------------------------------------------------------------------------

METADATA:

File:    base.py
        Project: paperap
Created: 2025-03-21
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-21     By Jess Mann

"""


from __future__ import annotations

import copy
import logging
from abc import ABC, ABCMeta
from string import Template
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, Iterator, overload, override

from pydantic import HttpUrl, field_validator
from typing_extensions import TypeVar

from paperap.const import URLS, Endpoints
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

    Args:
        client: The PaperlessClient instance.
        endpoint: The API endpoint for this resource.
        model_class: The model class for this resource.

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
        Initialize the subclass.

        Args:
            **kwargs: Arbitrary keyword arguments

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
        return self.model_class._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    @classmethod
    def _validate_endpoints(cls, value: Any) -> Endpoints:
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

    def get_endpoint(self, name: str, **kwargs: Any) -> HttpUrl:
        if not (template := self.endpoints.get(name, None)):
            raise ConfigurationError(f"Endpoint {name} not defined for resource {self.name}")

        if "resource" not in kwargs:
            kwargs["resource"] = self.name

        url = template.safe_substitute(**kwargs)

        if not url.startswith('http'):
            url = f'{self.client.base_url}{url.lstrip("/")}'

        return HttpUrl(url)

    def all(self) -> _BaseQuerySet:
        """
        Return a QuerySet representing all objects of this resource type.

        Returns:
            A QuerySet for this resource

        """
        return self.queryset_class(self)  # type: ignore # _meta.queryset is always the right queryset type

    def filter(self, **kwargs: Any) -> _BaseQuerySet:
        """
        Return a QuerySet filtered by the given parameters.

        Args:
            **kwargs: Filter parameters

        Returns:
            A filtered QuerySet

        """
        return self.all().filter(**kwargs)

    def get(self, *args: Any, **kwargs: Any) -> _BaseModel:
        """
        Get a model by ID.

        Raises NotImplementedError. Subclasses may implement this.

        Raises:
            NotImplementedError: Unless implemented by a subclass.

        Returns:
            The model retrieved.

        """
        raise NotImplementedError("get method not available for resources without an id")

    def create(self, **kwargs: Any) -> _BaseModel:
        """
        Create a new resource.

        Args:
            data: Resource data.

        Returns:
            The created resource.

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

        Args:
            resource: The resource to update.

        Returns:
            The updated resource.

        """
        raise NotImplementedError("update method not available for resources without an id")

    def update_dict(self, *args: Any, **kwargs: Any) -> _BaseModel:
        """
        Update a resource.

        Subclasses may implement this.
        """
        raise NotImplementedError("update_dict method not available for resources without an id")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Delete a resource.

        Args:
            model_id: ID of the resource.

        """
        raise NotImplementedError("delete method not available for resources without an id")

    def parse_to_model(self, item: dict[str, Any]) -> _BaseModel:
        """
        Parse an item dictionary into a model instance, handling date parsing.

        Args:
            item: The item dictionary.

        Returns:
            The parsed model instance.

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

        Args:
            data: The data to transform.

        Returns:
            The transformed data.

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
        self, model: _BaseModel | None = None, exclude_unset: bool = True, **data: Any
    ) -> dict[str, Any]:
        """
        Transform data before sending it to the API.

        Args:
            model: The model to transform.
            exclude_unset: If model is provided, exclude unset fields when calling to_dict()
            data: The data to transform.

        Returns:
            The transformed data.

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
        Create a new model instance.

        Args:
            **kwargs: Model field values

        Returns:
            A new model instance.

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
    ) -> dict[str, Any] | None:
        """
        Make an HTTP request to the API, and return the raw json response.

        Args:
            method: The HTTP method to use
            url: The full URL to request
            params: Query parameters
            data: Request body data

        Returns:
            The JSON-decoded response from the API

        """
        if not url and not (url := self.get_endpoint("list", resource=self.name)):
            raise ConfigurationError(f"List endpoint not defined for resource {self.name}")

        if isinstance(url, Template):
            url = url.safe_substitute(resource=self.name)

        response = self.client.request(method, url, params=params, data=data)
        return response

    def handle_response(self, **response: Any) -> Iterator[_BaseModel]:
        """
        Handle a response from the API and yield results.

        Override in subclasses to implement custom response logic.
        """
        registry.emit(
            "resource._handle_response:before",
            "Emitted before listing resources",
            return_type=dict[str, Any],
            args=[self],
            kwargs={"response": response, "resource": self.name},
        )
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

        Override in subclasses to implement custom result handling.
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
        Make the resource callable to get a BaseQuerySet.

        This allows usage like: client.documents(title__contains='invoice')

        Args:
            *args: Unused
            **keywords: Filter parameters

        Returns:
            A filtered QuerySet

        """
        return self.filter(**keywords)


class StandardResource(BaseResource[_StandardModel, _StandardQuerySet]):
    """
    Base class for API resources.

    Args:
        client: The PaperlessClient instance.
        endpoint: The API endpoint for this resource.
        model_class: The model class for this resource.

    """

    @override
    def get(self, model_id: int, *args: Any, **kwargs: Any) -> _StandardModel:
        """
        Get a model within this resource by ID.

        Args:
            model_id: ID of the model to retrieve.

        Returns:
            The model retrieved

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
        Update a model.

        Args:
            model: The model to update.

        Returns:
            The updated model.

        """
        data = model.to_dict()
        data = self.transform_data_output(**data)
        return self.update_dict(model.id, **data)

    @override
    def delete(self, model_id: int | _StandardModel) -> None:
        """
        Delete a resource.

        Args:
            model_id: ID of the resource.

        """
        if not model_id:
            raise ValueError("model_id is required to delete a resource")
        if not isinstance(model_id, int):
            model_id = model_id.id

        # Signal before deleting resource
        signal_params = {"resource": self.name, "model_id": model_id}
        registry.emit("resource.delete:before", "Emitted before deleting a resource", args=[self], kwargs=signal_params)

        if not (url := self.get_endpoint("delete", resource=self.name, pk=model_id)):
            raise ConfigurationError(f"Delete endpoint not defined for resource {self.name}")

        self.client.request("DELETE", url)

        # Signal after deleting resource
        registry.emit("resource.delete:after", "Emitted after deleting a resource", args=[self], kwargs=signal_params)

    @override
    def update_dict(self, model_id: int, **data: dict[str, Any]) -> _StandardModel:
        """
        Update a resource.

        Args:
            model_id: ID of the resource.
            data: Resource data.

        Raises:
            ResourceNotFoundError: If the resource with the given id is not found

        Returns:
            The updated resource.

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

class BulkEditing:

    def bulk_edit_objects(
        self : BaseResource, # type: ignore
        object_type: str,
        ids: list[int],
        operation: str,
        permissions: dict[str, Any] = None,
        owner_id: int = None,
        merge: bool = False
    ) -> dict[str, Any]:
        """
        Bulk edit non-document objects (tags, correspondents, document types, storage paths).

        Args:
            object_type: Type of objects to edit ('tags', 'correspondents', 'document_types', 'storage_paths')
            ids: List of object IDs to edit
            operation: Operation to perform ('set_permissions' or 'delete')
            permissions: Permissions object for 'set_permissions' operation
            owner_id: Owner ID to assign
            merge: Whether to merge permissions with existing ones (True) or replace them (False)

        Returns:
            The API response

        Raises:
            ValueError: If operation is not valid
            ConfigurationError: If the bulk edit endpoint is not defined

        """
        if operation not in ('set_permissions', 'delete'):
            raise ValueError(f"Invalid operation '{operation}'. Must be 'set_permissions' or 'delete'")

        # Signal before bulk action
        signal_params = {
            "object_type": object_type,
            "operation": operation,
            "ids": ids,
            "permissions": permissions,
            "owner_id": owner_id,
            "merge": merge
        }
        registry.emit(
            "resource.bulk_edit_objects:before",
            "Emitted before bulk edit objects",
            args=[self],
            kwargs=signal_params,
        )

        data : dict[str, Any] = {
            "objects": ids,
            "object_type": object_type,
            "operation": operation,
            "merge": merge
        }

        if permissions:
            data["permissions"] = permissions
        if owner_id is not None:
            data["owner"] = owner_id

        # Use the special endpoint for bulk editing objects
        url = HttpUrl(f"{self.client.base_url}/api/bulk_edit_objects/")

        response = self.client.request("POST", url, data=data)

        # Signal after bulk action
        registry.emit(
            "resource.bulk_edit_objects:after",
            "Emitted after bulk edit objects",
            args=[self],
            kwargs={**signal_params, "response": response},
        )

        return response or {}
