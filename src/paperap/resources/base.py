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
            url = f'{self.client.base_url}{url}'

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

    def bulk_action(self, action: str, ids: list[int], **kwargs: Any) -> dict[str, Any]:
        """
        Perform a bulk action on multiple resources.

        Args:
            action: The action to perform (e.g., "delete", "update", etc.)
            ids: List of resource IDs to perform the action on
            **kwargs: Additional parameters for the action

        Returns:
            The API response

        Raises:
            ConfigurationError: If the bulk endpoint is not defined

        """
        # Signal before bulk action
        signal_params = {"resource": self.name, "action": action, "ids": ids, "kwargs": kwargs}
        registry.emit("resource.bulk_action:before", "Emitted before bulk action", args=[self], kwargs=signal_params)

        # Prepare the data for the bulk action
        data = {"method": action, "documents": ids, "parameters": kwargs}

        if not (url := self.get_endpoint("bulk_edit", resource=self.name)):
            raise ConfigurationError(f"Bulk edit endpoint not defined for resource {self.name}")

        response = self.client.request("POST", url, data=data)

        # Signal after bulk action
        registry.emit(
            "resource.bulk_action:after",
            "Emitted after bulk action",
            args=[self],
            kwargs={**signal_params, "response": response},
        )

        return response or {}

    def bulk_delete(self, ids: list[int]) -> dict[str, Any]:
        """
        Delete multiple resources at once.

        Args:
            ids: List of resource IDs to delete

        Returns:
            The API response

        """
        return self.bulk_action("delete", ids)

    def bulk_update(self, ids: list[int], **kwargs: Any) -> dict[str, Any]:
        """
        Update multiple resources at once.

        This is a generic method that transforms the data before sending.
        For document-specific operations, use the specialized methods.

        Args:
            ids: List of resource IDs to update
            **kwargs: Fields to update on all resources

        Returns:
            The API response

        """
        # Transform the data before sending
        data = self.transform_data_output(**kwargs)
        return self.bulk_action("update", ids, **data)
        
    def bulk_reprocess(self, ids: list[int]) -> dict[str, Any]:
        """
        Reprocess multiple documents.

        Args:
            ids: List of document IDs to reprocess

        Returns:
            The API response
        """
        return self.bulk_action("reprocess", ids)
        
    def bulk_merge(
        self, ids: list[int], metadata_document_id: int = None, delete_originals: bool = False
    ) -> dict[str, Any]:
        """
        Merge multiple documents.

        Args:
            ids: List of document IDs to merge
            metadata_document_id: Apply metadata from this document to the merged document
            delete_originals: Whether to delete the original documents after merging

        Returns:
            The API response

        """
        params = {}
        if metadata_document_id is not None:
            params["metadata_document_id"] = metadata_document_id
        if delete_originals:
            params["delete_originals"] = True
            
        return self.bulk_action("merge", ids, **params)
        
    def bulk_split(self, document_id: int, pages: list[int], delete_originals: bool = False) -> dict[str, Any]:
        """
        Split a document.

        Args:
            document_id: Document ID to split
            pages: List of pages to split
            delete_originals: Whether to delete the original document after splitting

        Returns:
            The API response

        """
        params = {"pages": pages}
        if delete_originals:
            params["delete_originals"] = True
            
        return self.bulk_action("split", [document_id], **params)
        
    def bulk_rotate(self, ids: list[int], degrees: int) -> dict[str, Any]:
        """
        Rotate documents.

        Args:
            ids: List of document IDs to rotate
            degrees: Degrees to rotate (must be 90, 180, or 270)

        Returns:
            The API response

        """
        if degrees not in (90, 180, 270):
            raise ValueError("Degrees must be 90, 180, or 270")
            
        return self.bulk_action("rotate", ids, degrees=degrees)
        
    def bulk_delete_pages(self, document_id: int, pages: list[int]) -> dict[str, Any]:
        """
        Delete pages from a document.

        Args:
            document_id: Document ID
            pages: List of page numbers to delete

        Returns:
            The API response

        """
        return self.bulk_action("delete_pages", [document_id], pages=pages)
        
    def bulk_modify_custom_fields(
        self, ids: list[int], add_custom_fields: dict[int, Any] = None, remove_custom_fields: list[int] = None
    ) -> dict[str, Any]:
        """
        Modify custom fields on multiple documents.

        Args:
            ids: List of document IDs to update
            add_custom_fields: Dictionary of custom field ID to value pairs to add
            remove_custom_fields: List of custom field IDs to remove

        Returns:
            The API response

        """
        params = {}
        if add_custom_fields:
            params["add_custom_fields"] = add_custom_fields
        if remove_custom_fields:
            params["remove_custom_fields"] = remove_custom_fields
            
        return self.bulk_action("modify_custom_fields", ids, **params)

    def bulk_modify_tags(self, ids: list[int], add_tags: list[int] = None, remove_tags: list[int] = None) -> dict[str, Any]:
        """
        Modify tags on multiple documents.

        Args:
            ids: List of document IDs to update
            add_tags: List of tag IDs to add
            remove_tags: List of tag IDs to remove

        Returns:
            The API response

        """
        params = {}
        if add_tags:
            params["add_tags"] = add_tags
        if remove_tags:
            params["remove_tags"] = remove_tags
        
        return self.bulk_action("modify_tags", ids, **params)

    def bulk_add_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Add a tag to multiple documents.

        Args:
            ids: List of document IDs to update
            tag_id: Tag ID to add

        Returns:
            The API response

        """
        return self.bulk_action("add_tag", ids, tag=tag_id)

    def bulk_remove_tag(self, ids: list[int], tag_id: int) -> dict[str, Any]:
        """
        Remove a tag from multiple documents.

        Args:
            ids: List of document IDs to update
            tag_id: Tag ID to remove

        Returns:
            The API response

        """
        return self.bulk_action("remove_tag", ids, tag=tag_id)

    def bulk_set_correspondent(self, ids: list[int], correspondent_id: int) -> dict[str, Any]:
        """
        Set correspondent for multiple documents.

        Args:
            ids: List of document IDs to update
            correspondent_id: Correspondent ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_correspondent", ids, correspondent=correspondent_id)

    def bulk_set_document_type(self, ids: list[int], document_type_id: int) -> dict[str, Any]:
        """
        Set document type for multiple documents.

        Args:
            ids: List of document IDs to update
            document_type_id: Document type ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_document_type", ids, document_type=document_type_id)

    def bulk_set_storage_path(self, ids: list[int], storage_path_id: int) -> dict[str, Any]:
        """
        Set storage path for multiple documents.

        Args:
            ids: List of document IDs to update
            storage_path_id: Storage path ID to assign

        Returns:
            The API response

        """
        return self.bulk_action("set_storage_path", ids, storage_path=storage_path_id)

    def bulk_set_permissions(
        self, ids: list[int], permissions: dict[str, Any] = None, owner_id: int = None, merge: bool = False
    ) -> dict[str, Any]:
        """
        Set permissions for multiple documents.

        Args:
            ids: List of document IDs to update
            permissions: Permissions object
            owner_id: Owner ID to assign
            merge: Whether to merge with existing permissions (True) or replace them (False)

        Returns:
            The API response

        """
        params = {"merge": merge}
        if permissions:
            params["set_permissions"] = permissions
        if owner_id is not None:
            params["owner"] = owner_id
        
        return self.bulk_action("set_permissions", ids, **params)

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

    def bulk_edit_objects(
        self, 
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
            
        data = {
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
        
        return response or {}

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
