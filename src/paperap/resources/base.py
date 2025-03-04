"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    base.py                                                                                              *
*        Project: resources                                                                                            *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Iterator, Optional
from typing_extensions import TypeVar
from yarl import URL
from string import Template
import logging
from paperap.const import URLS, Endpoints
from paperap.parser import Parser
from paperap.exceptions import ObjectNotFoundError, ResourceNotFoundError
from paperap.signals import (
    pre_list,
    post_list_response,
    post_list_item,
    post_list,
    pre_get,
    post_get,
    pre_create,
    post_create,
    pre_update,
    post_update,
    pre_delete,
    post_delete,
)
from paperap.models.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.models.base import PaperlessModel

_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel", covariant=True)

logger = logging.getLogger(__name__)


class PaperlessResourceMeta(ABC.__class__, Generic[_PaperlessModel]):
    """
    Metaclass for PaperlessResource.

    This metaclass ensures that all subclasses of PaperlessModel have a parser attribute,
    and sets default values for name and name_verbose if they are not provided.
    It also enforces that an api_endpoint is defined for each subclass.
    """

    def __new__(cls, name, bases, dct):
        """
        Create a new class with a parser attribute and default metadata.
        Ensure that all PaperlessModel subclasses have a parser attribute.

        Args:
            name: The name of the new class.
            bases: The base classes of the new class.
            dct: The class dictionary.

        Returns:
            The newly created class.
        """
        # Not sure why pyright is complaining about this
        new_class: type["PaperlessResource[_PaperlessModel]"] = super().__new__(cls, name, bases, dct)  # type: ignore

        # if classname is PaperlessResource, don't do anything
        if name == "PaperlessResource":
            return new_class

        # model_class is required
        if not (model_class := getattr(new_class, "model_class")):
            raise ValueError(f"model_class must be defined in {new_class.__name__}")

        # Set parser
        parser_type = model_class._meta.parser
        new_class.parser = parser_type(model_class)

        # API Endpoint must be defined
        if not hasattr(new_class, "endpoints"):
            new_class.endpoints = {
                "list": URLS.list,
                "detail": URLS.detail,
                "create": URLS.create,
                "update": URLS.update,
                "delete": URLS.delete,
            }

        return new_class


class PaperlessResource(ABC, Generic[_PaperlessModel], metaclass=PaperlessResourceMeta):
    """
    Base class for API resources.

    Args:
        client: The PaperlessClient instance.
        endpoint: The API endpoint for this resource.
        model_class: The model class for this resource.
    """

    # The model class for this resource.
    model_class: type[_PaperlessModel]
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
    # A class which parses api data into appropriate types
    # this will usually not need to be overridden
    parser: ClassVar[Parser]

    def __init__(self, client: "PaperlessClient"):
        self.client = client
        if not hasattr(self, "name"):
            self.name = f"{self.model_class._meta.name.lower()}s"

        # Allow templating
        key: str
        value: Template
        for key, value in self.endpoints.items():  # type: ignore # Endpoints is dict[str, Template]
            self.endpoints[key] = Template(value.safe_substitute(resource=self.name))

    def all(self) -> QuerySet[_PaperlessModel]:
        """
        Return a QuerySet representing all objects of this resource type.

        Returns:
            A QuerySet for this resource
        """
        return QuerySet(self)

    def filter(self, **kwargs) -> QuerySet[_PaperlessModel]:
        """
        Return a QuerySet filtered by the given parameters.

        Args:
            **kwargs: Filter parameters

        Returns:
            A filtered QuerySet
        """
        return self.all().filter(**kwargs)

    def get(self, resource_id: int) -> _PaperlessModel:
        """
        Get a resource by ID.

        Args:
            resource_id: ID of the resource.

        Returns:
            The resource.
        """
        # Signal before getting resource
        signal_params = {"resource": self.name, "resource_id": resource_id}
        pre_get.emit(self, **signal_params)

        if not (template := self.endpoints.get("detail")):
            raise ValueError(f"Get detail endpoint not defined for resource {self.name}")

        # Provide template substitutions for endpoints
        url = template.safe_substitute(resource=self.name, pk=resource_id)

        if not (response := self.client.request("GET", url)):
            raise ObjectNotFoundError(resource_type=self.name, resource_id=resource_id)

        # If the response doesn't have an ID, it's likely a 404
        if not response.get("id"):
            message = response.get("detail") or f"No ID found in {self.name} response"
            raise ObjectNotFoundError(message, resource_type=self.name, resource_id=resource_id)

        model = self.parse_to_model(response)

        # Signal after getting resource
        post_get.emit(self, model=model, **signal_params)

        return model

    def create(self, data: dict[str, Any]) -> _PaperlessModel:
        """
        Create a new resource.

        Args:
            data: Resource data.

        Returns:
            The created resource.
        """
        # Signal before creating resource
        signal_params = {"resource": self.name, "data": data}
        pre_create.emit(self, **signal_params)

        if not (template := self.endpoints.get("create")):
            raise ValueError(f"Create endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name)
        if not (response := self.client.request("POST", url, data=data)):
            raise ResourceNotFoundError("Resource {resource} not found after create.", resource_type=self.name)

        model = self.parse_to_model(response)

        # Signal after creating resource
        post_create.emit(self, model=model, **signal_params)

        return model

    def update(self, resource_id: int, data: dict[str, Any]) -> _PaperlessModel:
        """
        Update a resource.

        Args:
            resource_id: ID of the resource.
            data: Resource data.

        Returns:
            The updated resource.
        """
        # Signal before updating resource
        signal_params = {"resource": self.name, "resource_id": resource_id, "data": data}
        pre_update.emit(self, **signal_params)

        if not (template := self.endpoints.get("update")):
            raise ValueError(f"Update endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name)
        if not (response := self.client.request("PUT", url, data=data)):
            raise ResourceNotFoundError("Resource {resource} not found after update.", resource_type=self.name)

        model = self.parse_to_model(response)

        # Signal after updating resource
        post_update.emit(self, model=model, **signal_params)

        return model

    def delete(self, resource_id: int) -> None:
        """
        Delete a resource.

        Args:
            resource_id: ID of the resource.
        """
        # Signal before deleting resource
        signal_params = {"resource": self.name, "resource_id": resource_id}
        pre_delete.emit(self, **signal_params)

        if not (template := self.endpoints.get("delete")):
            raise ValueError(f"Delete endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name, pk=resource_id)
        self.client.request("DELETE", url)

        # Signal after deleting resource
        post_delete.emit(self, **signal_params)

    def parse_to_model(self, item: dict[str, Any]) -> _PaperlessModel:
        """
        Parse an item dictionary into a model instance, handling date parsing.

        Args:
            item: The item dictionary.

        Returns:
            The parsed model instance.
        """
        parsed_data = self.parser.parse_data(item)
        return self.model_class.from_dict(parsed_data, self)

    def _request_raw(
        self,
        url: str | Template | URL | None = None,
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
        if not url:
            if not (url := self.endpoints.get("list")):
                raise ValueError(f"List endpoint not defined for resource {self.name}")

        if isinstance(url, Template):
            url = url.safe_substitute(resource=self.name)

        response = self.client.request(method, url, params=params, data=data)
        return response

    def _handle_response(self, response: dict[str, Any]) -> Iterator[_PaperlessModel]:
        """
        Handle a response from the API and yield results.

        Override in subclasses to implement custom response logic.
        """
        if not (results := response.get("results", response)):
            raise NotImplementedError("No results found in response")

        # Signal after receiving response
        post_list_response.emit(self, response=response, resource=self.name, results=results)

        yield from self._handle_results(results)

    def _handle_results(self, results: list[dict[str, Any]]) -> Iterator[_PaperlessModel]:
        """
        Yield parsed models from a list of results.

        Override in subclasses to implement custom result handling.
        """
        for item in results:
            post_list_item.emit(self, resource=self.name, item=item)
            yield self.parse_to_model(item)

    def __call__(self, *args, **keywords) -> QuerySet[_PaperlessModel]:
        """
        Make the resource callable to get a QuerySet.

        This allows usage like: client.documents(title__contains='invoice')

        Args:
            **keywords: Filter parameters

        Returns:
            A filtered QuerySet
        """
        return self.filter(**keywords)
