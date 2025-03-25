
from __future__ import annotations

import logging
import os
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, override
from unittest.mock import MagicMock, patch

from pydantic import ValidationError
from typing_extensions import TypeAlias, TypeVar

from paperap.client import PaperlessClient
from paperap.models import (
    BaseQuerySet,
    Correspondent,
    CorrespondentQuerySet,
    CustomField,
    CustomFieldQuerySet,
    Document,
    DocumentQuerySet,
    DocumentType,
    DocumentTypeQuerySet,
    Group,
    GroupQuerySet,
    Profile,
    ProfileQuerySet,
    SavedView,
    SavedViewQuerySet,
    ShareLinks,
    ShareLinksQuerySet,
    StandardModel,
    StandardQuerySet,
    StoragePath,
    StoragePathQuerySet,
    Tag,
    TagQuerySet,
    Task,
    TaskQuerySet,
    UISettings,
    UISettingsQuerySet,
    User,
    UserQuerySet,
    Workflow,
    WorkflowAction,
    WorkflowActionQuerySet,
    WorkflowQuerySet,
    WorkflowTrigger,
    WorkflowTriggerQuerySet,
)
from paperap.resources import (
    BaseResource,
    CorrespondentResource,
    CustomFieldResource,
    DocumentResource,
    DocumentTypeResource,
    GroupResource,
    ProfileResource,
    SavedViewResource,
    ShareLinksResource,
    StandardResource,
    StoragePathResource,
    TagResource,
    TaskResource,
    UISettingsResource,
    UserResource,
    WorkflowActionResource,
    WorkflowResource,
    WorkflowTriggerResource,
)
from tests.lib.factories import (
    CorrespondentFactory,
    DocumentFactory,
    DocumentTypeFactory,
    GroupFactory,
    ProfileFactory,
    PydanticFactory,
    SavedViewFactory,
    ShareLinksFactory,
    StoragePathFactory,
    TagFactory,
    TaskFactory,
    UISettingsFactory,
    UserFactory,
    WorkflowActionFactory,
    WorkflowFactory,
    WorkflowTriggerFactory,
)
from tests.lib.utils import load_sample_data

_StandardModel = TypeVar("_StandardModel", bound=StandardModel, default=StandardModel)
_StandardResource = TypeVar("_StandardResource", bound=StandardResource, default=StandardResource)
_StandardQuerySet = TypeVar("_StandardQuerySet", bound=StandardQuerySet, default=StandardQuerySet)

logger = logging.getLogger(__name__)

class TestMixin(ABC, Generic[_StandardModel, _StandardResource, _StandardQuerySet]):

    """
    A base test case class for testing Paperless NGX resources.

    Attributes:
        client: The PaperlessClient instance.
        mock_env: Whether to mock the environment variables.
        env_data: The environment data to use when mocking.
        resource: The resource being tested.
        resource_class: The class of the resource being tested.
        factory: The factory class for creating model instances.
        model_data_parsed: The data for creating a model instance.
        list_data: The data for creating a list of model instances.

    """

    # Patching stuff
    mock_env : bool = True
    env_data : dict[str, Any] = {'PAPERLESS_BASE_URL': 'http://example.com', 'PAPERLESS_TOKEN': '40characterslong40characterslong40charac', 'PAPERLESS_SAVE_ON_WRITE': 'False'}
    save_on_write: bool | None = None

    # Data for the test
    sample_data_filename : str | None = None
    model_data_unparsed : dict[str, Any]
    model_data_parsed : dict[str, Any]
    list_data : dict[str, Any]

    # Instances
    client : "PaperlessClient"
    resource : _StandardResource
    model : _StandardModel

    # Types (TODO only one of these should be needed)
    factory : type[PydanticFactory[_StandardModel]]
    resource_class : type[_StandardResource]
    model_type : type[_StandardModel] | None = None
    queryset_type : type[_StandardQuerySet] | None = None

    @property
    def _meta(self) -> StandardModel.Meta:
        return self.model._meta # type: ignore # Allow private attribute access in tests

    def _reset_attributes(self) -> None:
        """
        Set up the test case by initializing the client, resource, and model data.
        """
        self.setup_references()
        self.setup_client()
        self.setup_resource()
        self.setup_model_data()
        self.setup_model()

    @abstractmethod
    def setup_client(self, **kwargs) -> None:
        raise NotImplementedError("Method must be implemented in subclasses.")

    @abstractmethod
    def validate_field(self, field_name : str, test_cases : list[tuple[Any, Any]]):
        """
        Validate that a field is parsed correctly with various types of data.

        Args:
            field_name: The name of the field to test.
            test_cases: A list of tuples with input values and expected results.

        Examples:
            test_cases = [
                (42,              42),
                ("42",            42),
                (None,            None),
                (0,               ValidationError),
                (Decimal('42.5'), ValidationError),
            ]
            self.validate_field("age", test_cases)

        """
        raise NotImplementedError("Method must be implemented in subclasses.")

    def setup_references(self) -> None:
        # Check if we have each attrib, and set all the others we can
        if hasattr(self, "modal_type"):
            self.resource = getattr(self, "resource", self.model_type._meta.resource) # type: ignore
            self.resource_class = getattr(self, "resource_class", self.resource.__class__) # type: ignore
            self.queryset_type = getattr(self, "queryset_type", self.model_type.resource.queryset_class) # type: ignore
        if hasattr(self, "model"):
            self.model_type = getattr(self, "model_type", self.model.__class__) # type: ignore
            self.resource = getattr(self, "resource", self.model.resource) # type: ignore
            self.resource_class = getattr(self, "resource_class", self.resource.__class__) # type: ignore
            self.queryset_type = getattr(self, "queryset_type", self.resource.queryset_class) # type: ignore
        '''
        if hasattr(self, "factory"):
            self.model_type = getattr(self, "model_type", self.factory._meta.model) # type: ignore
            self.resource = getattr(self, "resource", self.model_type._meta.resource) # type: ignore
            self.resource_class = getattr(self, "resource_class", self.resource.__class__) # type: ignore
            self.queryset_type = getattr(self, "queryset_type", self.model_type.resource.queryset_class) # type: ignore
        '''
        if hasattr(self, "resource"):
            self.resource_class = getattr(self, "resource_class", self.resource.__class__) # type: ignore
            self.model_type = getattr(self, "model_type", self.resource.model_class) # type: ignore
            self.queryset_type = getattr(self, "queryset_type", self.model_type.resource.queryset_class) # type: ignore

    def setup_resource(self) -> None:
        """
        Set up the resource instance using the resource class.
        """
        if not getattr(self, "resource", None) and (resource_class := getattr(self, 'resource_class', None)):
            self.resource = resource_class(client=self.client) # pylint: disable=not-callable

    def setup_model_data(self) -> None:
        """
        Load model data if the resource is set.
        """
        if getattr(self, "resource", None):
            unparsed = getattr(self, "model_data_unparsed", None)
            parsed = getattr(self, "model_data_parsed", None)

            if unparsed:
                self.model_data_parsed = parsed or self.resource.transform_data_output(**unparsed)
            else:
                self.load_model_data()

            # Reload it in case it changed
            parsed = getattr(self, "model_data_parsed", None)
            if not unparsed and parsed:
                self.model_data_unparsed = self.resource.transform_data_input(**parsed)

    def setup_model(self) -> None:
        """
        Set up the model instance using the factory and model data.
        """
        if getattr(self, "resource", None) and getattr(self, "model_data_unparsed", None):
            self.model = self.resource.parse_to_model(self.model_data_unparsed)

        if (model := getattr(self, 'model', None)) and self.save_on_write is not None:
            model._meta.save_on_write = self.save_on_write

    def bake_model(self, *args, **kwargs : Any) -> _StandardModel:
        """
        Create a model instance using the factory.

        Args:
            *args: Positional arguments for the factory.
            **kwargs: Keyword arguments for the factory.

        Returns:
            A new model instance.

        """
        return self.factory.create(*args, **kwargs)

    def create_list(self, count : int, *args, **kwargs : Any) -> list[_StandardModel]:
        """
        Create a list of model instances using the factory.

        Args:
            count: The number of instances to create.
            *args: Positional arguments for the factory.
            **kwargs: Keyword arguments for the factory.

        Returns:
            A list of new model instances.

        """
        return [self.bake_model(*args, **kwargs) for _ in range(count)]

    def load_model(self, resource_name : str | None = None) -> _StandardModel:
        """
        Load a model instance from sample data.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A new model instance created from the sample data.

        """
        sample_data = self.load_model_data(resource_name)
        model = self.resource.parse_to_model(sample_data)
        if self.save_on_write is not None:
            model._meta.save_on_write = self.save_on_write
        return model

    def load_list(self, resource_name : str | None = None) -> list[_StandardModel]:
        """
        Load a list of model instances from sample data.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A list of new model instances created from the sample data.

        """
        sample_data = self.load_list_data(resource_name)
        models = [self.resource.parse_to_model(item) for item in sample_data["results"]]
        if self.save_on_write is not None:
            for model in models:
                model._meta.save_on_write = self.save_on_write
        return models

    def _call_list_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel] | None = None, **kwargs : Any) -> BaseQuerySet[_StandardModel]:
        """
        Call the list method on a resource.

        Args:
            resource: The resource or resource class to call.
            **kwargs: Additional filter parameters.

        Returns:
            A BaseQuerySet of model instances.

        """
        if not resource:
            if not (resource := getattr(self,"resource", None)):
                raise ValueError("Resource not provided")

        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).filter(**kwargs)
        return resource.filter(**kwargs)

    def _call_get_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel], pk : int) -> _StandardModel:
        """
        Call the get method on a resource.

        Args:
            resource: The resource or resource class to call.
            pk: The primary key of the model instance to retrieve.

        Returns:
            The model instance with the specified primary key.

        """
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).get(pk)

        return resource.get(pk)

    def list_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel] | None = None, **kwargs : Any) -> BaseQuerySet[_StandardModel]:
        """
        List resources using sample data or by calling the resource.

        Args:
            resource: The resource or resource class to list.
            **kwargs: Additional filter parameters.

        Returns:
            A BaseQuerySet of model instances.

        """
        if not resource:
            if not (resource := getattr(self, "resource", None)):
                raise ValueError("Resource not provided")

        try:
            sample_data = self.load_list_data(resource.name)
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                qs = self._call_list_resource(resource, **kwargs)
                for _ in qs:
                    pass
                return qs

        except FileNotFoundError:
            return self._call_list_resource(resource, **kwargs)

    def get_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel], pk : int) -> _StandardModel:
        """
        Get a resource using sample data or by calling the resource.

        Args:
            resource: The resource or resource class to get.
            pk: The primary key of the model instance to retrieve.

        Returns:
            The model instance with the specified primary key.

        """
        try:
            sample_data = self.load_model_data()
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                return self._call_get_resource(resource, pk)
        except FileNotFoundError:
            return self._call_get_resource(resource, pk)

    def load_model_data(self, resource_name : str | None = None) -> dict[str, Any]:
        """
        Load model data from a sample data file.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A dictionary containing the model data.

        """
        if not getattr(self, "model_data_parsed", None):
            try:
                if self.sample_data_filename:
                    self.model_data_unparsed = load_sample_data(self.sample_data_filename)
                else:
                    resource_name = resource_name or self.resource.name
                    filename = f"{resource_name}_item.json"
                    self.model_data_unparsed  = load_sample_data(filename)
            except FileNotFoundError:
                logger.debug('Skipping loading model data from file')
                return {}

            if unparsed := getattr(self, 'model_data_unparsed', None):
                self.model_data_parsed = self.resource.transform_data_output(**self.model_data_unparsed)

        return self.model_data_parsed

    def load_list_data(self, resource_name : str | None = None) -> dict[str, Any]:
        """
        Load list data from a sample data file.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A dictionary containing the list data.

        """
        if not getattr(self, "list_data", None):
            resource_name = resource_name or self.resource.name
            filename = f"{resource_name}_list.json"
            self.list_data = load_sample_data(filename)
        return self.list_data
