"""




----------------------------------------------------------------------------

   METADATA:

       File:    base.py
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

from abc import ABC, ABCMeta
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Iterator, Optional
from typing_extensions import TypeVar
from yarl import URL
from string import Template
import logging
from paperap.const import URLS, Endpoints
from paperap.models.abstract.parser import Parser
from paperap.exceptions import ObjectNotFoundError, ResourceNotFoundError, ConfigurationError
from paperap.signals import SignalRegistry

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.models.abstract import StandardModel, PaperlessModel, QuerySet, StandardQuerySet

_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel", covariant=True)
_StandardModel = TypeVar("_StandardModel", bound="StandardModel", covariant=True, default="StandardModel")
_QuerySet = TypeVar("_QuerySet", bound="QuerySet", covariant=True, default="QuerySet[_PaperlessModel]")
_StandardQuerySet = TypeVar(
    "_StandardQuerySet", bound="StandardQuerySet", covariant=True, default="StandardQuerySet[_StandardModel]"
)

logger = logging.getLogger(__name__)


class PaperlessResource(ABC, Generic[_PaperlessModel, _QuerySet]):
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
        for key, value in self.endpoints.items():
            self.endpoints[key] = Template(value.safe_substitute(resource=self.name))  # type: ignore # endpoints is always dict[str, Template]

        # Ensure the model has a link back to this resource
        self.model_class._meta.resource = self

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Skip processing for the base class itself. TODO: This is a hack
        if cls.__name__ in ["PaperlessResource", "StandardResource"]:
            return

        # model_class is required
        if not (model_class := getattr(cls, "model_class", None)):
            raise ConfigurationError(f"model_class must be defined in {cls.__name__}")

        # Set parser
        parser_type = model_class._meta.parser
        cls.parser = parser_type(model_class)

        # API Endpoint must be defined
        if not hasattr(cls, "endpoints"):
            cls.endpoints = {
                "list": URLS.list,
                "detail": URLS.detail,
                "create": URLS.create,
                "update": URLS.update,
                "delete": URLS.delete,
            }

    def all(self) -> _QuerySet:
        """
        Return a QuerySet representing all objects of this resource type.

        Returns:
            A QuerySet for this resource
        """
        return self.model_class._meta.queryset(self)  # type: ignore # _meta.queryset is always the right queryset type

    def filter(self, **kwargs) -> _QuerySet:
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
        Get a model by ID.

        Raises NotImplementedError. Subclasses may implement this.

        Args:
            resource_id: ID of the model to retrieve.

        Raises:
            NotImplementedError: Unless implemented by a subclass.

        Returns:
            The model retrieved.
        """
        raise NotImplementedError("get method not available for paperless resources without an id")

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
        SignalRegistry.emit("resource.create:before", "Emitted before creating a resource", kwargs=signal_params)

        if not (template := self.endpoints.get("create")):
            raise ConfigurationError(f"Create endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name)
        if not (response := self.client.request("POST", url, data=data)):
            raise ResourceNotFoundError("Resource {resource} not found after create.", resource_type=self.name)

        model = self.parse_to_model(response)

        # Signal after creating resource
        SignalRegistry.emit(
            "resource.create:after",
            "Emitted after creating a resource",
            args=[self],
            kwargs={"model": model, **signal_params},
        )

        return model

    def update(self, resource_id: int, data: dict[str, Any]) -> _PaperlessModel:
        """
        Update a resource.

        Args:
            resource_id: ID of the resource.
            data: Resource data.

        Raises:
            ResourceNotFoundError: If the resource with the given id is not found

        Returns:
            The updated resource.
        """
        # Signal before updating resource
        signal_params = {"resource": self.name, "resource_id": resource_id, "data": data}
        SignalRegistry.emit("resource.update:before", "Emitted before updating a resource", kwargs=signal_params)

        if not (template := self.endpoints.get("update")):
            raise ConfigurationError(f"Update endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name, pk=resource_id)
        if not (response := self.client.request("PUT", url, data=data)):
            raise ResourceNotFoundError("Resource {resource} not found after update.", resource_type=self.name)

        model = self.parse_to_model(response)

        # Signal after updating resource
        SignalRegistry.emit(
            "resource.update:after",
            "Emitted after updating a resource",
            args=[self],
            kwargs={**signal_params, "model": model},
        )

        return model

    def delete(self, resource_id: int) -> None:
        """
        Delete a resource.

        Args:
            resource_id: ID of the resource.
        """
        # Signal before deleting resource
        signal_params = {"resource": self.name, "resource_id": resource_id}
        SignalRegistry.emit(
            "resource.delete:before", "Emitted before deleting a resource", args=[self], kwargs=signal_params
        )

        if not (template := self.endpoints.get("delete")):
            raise ConfigurationError(f"Delete endpoint not defined for resource {self.name}")

        url = template.safe_substitute(resource=self.name, pk=resource_id)
        self.client.request("DELETE", url)

        # Signal after deleting resource
        SignalRegistry.emit(
            "resource.delete:after", "Emitted after deleting a resource", args=[self], kwargs=signal_params
        )

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

    def create_model(self, **kwargs) -> _PaperlessModel:
        return self.model_class(**kwargs, resource=self)

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
                raise ConfigurationError(f"List endpoint not defined for resource {self.name}")

        if isinstance(url, Template):
            url = url.safe_substitute(resource=self.name)

        response = self.client.request(method, url, params=params, data=data)
        return response

    def _handle_response(self, response: dict[str, Any]) -> Iterator[_PaperlessModel]:
        """
        Handle a response from the API and yield results.

        Override in subclasses to implement custom response logic.
        """
        SignalRegistry.emit(
            "resource._handle_response:before",
            "Emitted before listing resources",
            return_type=dict[str, Any],
            args=[self],
            kwargs={"response": response, "resource": self.name},
        )
        if not (results := response.get("results", response)):
            return 0

        # Signal after receiving response
        SignalRegistry.emit(
            "resource._handle_response:after",
            "Emitted after list response, before processing",
            args=[self],
            kwargs={"response": response, "resource": self.name, "results": results},
        )

        yield from self._handle_results(results)

    def _handle_results(self, results: list[dict[str, Any]]) -> Iterator[_PaperlessModel]:
        """
        Yield parsed models from a list of results.

        Override in subclasses to implement custom result handling.
        """
        for item in results:
            SignalRegistry.emit(
                "resource._handle_results:before",
                "Emitted for each item in a list response",
                args=[self],
                kwargs={"resource": self.name, "item": item},
            )
            yield self.parse_to_model(item)

    def __call__(self, *args, **keywords) -> _QuerySet:
        """
        Make the resource callable to get a QuerySet.

        This allows usage like: client.documents(title__contains='invoice')

        Args:
            **keywords: Filter parameters

        Returns:
            A filtered QuerySet
        """
        return self.filter(**keywords)


class StandardResource(
    PaperlessResource[_StandardModel, _StandardQuerySet], Generic[_StandardModel, _StandardQuerySet]
):
    """
    Base class for API resources.

    Args:
        client: The PaperlessClient instance.
        endpoint: The API endpoint for this resource.
        model_class: The model class for this resource.
    """

    # The model class for this resource.
    model_class: type[_StandardModel]

    def get(self, resource_id: int) -> _StandardModel:
        """
        Get a model within this resource by ID.

        Args:
            resource_id: ID of the model to retrieve.

        Returns:
            The model retrieved
        """
        # Signal before getting resource
        signal_params = {"resource": self.name, "resource_id": resource_id}
        SignalRegistry.emit(
            "resource.get:before", "Emitted before getting a resource", args=[self], kwargs=signal_params
        )

        if not (template := self.endpoints.get("detail")):
            raise ConfigurationError(f"Get detail endpoint not defined for resource {self.name}")

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
        SignalRegistry.emit(
            "resource.get:after",
            "Emitted after getting a single resource by id",
            args=[self],
            kwargs={**signal_params, "model": model},
        )

        return model
