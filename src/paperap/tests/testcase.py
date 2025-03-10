"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    testcase.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.4
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, override
from typing_extensions import TypeVar, TypeAlias
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from paperap.client import PaperlessClient
from paperap.tests.factories import (
    PydanticFactory,
    DocumentFactory,
    DocumentTypeFactory,
    CorrespondentFactory,
    TagFactory,
    UserFactory,
    GroupFactory,
    ProfileFactory,
    TaskFactory,
    WorkflowFactory,
    SavedViewFactory,
    ShareLinksFactory,
    UISettingsFactory,
    StoragePathFactory,
    WorkflowActionFactory,
    WorkflowTriggerFactory,
)
from paperap.models import (
    StandardModel,
    BaseQuerySet,
    Document,
    DocumentType,
    Correspondent,
    Tag,
    User,
    Group,
    Profile,
    Task,
    Workflow,
    SavedView,
    ShareLinks,
    UISettings,
    StoragePath,
    WorkflowAction,
    WorkflowTrigger,
)
from paperap.resources import (
    PaperlessResource,
    StandardResource,
    DocumentResource,
    DocumentTypeResource,
    CorrespondentResource,
    TagResource,
    UserResource,
    GroupResource,
    ProfileResource,
    TaskResource,
    WorkflowResource,
    SavedViewResource,
    ShareLinksResource,
    UISettingsResource,
    StoragePathResource,
    WorkflowActionResource,
    WorkflowTriggerResource
)

def load_sample_data(filename : str) -> dict[str, Any]:
    """
    Load sample data from a JSON file.

    Args:
        filename: The name of the file to load.

    Returns:
        A dictionary containing the sample data.
    """
    # Load sample response from tests/sample_data/{model}_{endpoint}.json
    sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
    with open(sample_data_filepath, "r", encoding="utf-8") as f:
        text = f.read()
        sample_data = json.loads(text)
    return sample_data

_StandardModel = TypeVar("_StandardModel", bound="StandardModel", default="StandardModel")
_StandardResource = TypeVar("_StandardResource", bound="StandardResource", default="StandardResource[_StandardModel]")

class TestCase(unittest.TestCase, Generic[_StandardModel, _StandardResource]):
    """
    A base test case class for testing Paperless NGX resources.

    Attributes:
        client: The PaperlessClient instance.
        mock_env: Whether to mock the environment variables.
        env_data: The environment data to use when mocking.
        resource: The resource being tested.
        resource_class: The class of the resource being tested.
        factory: The factory class for creating model instances.
        model_data: The data for creating a model instance.
        list_data: The data for creating a list of model instances.
    """
    client : "PaperlessClient"
    mock_env : bool = True
    env_data : dict[str, Any] = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123', 'PAPERLESS_SAVE_ON_WRITE': 'False'}
    resource : _StandardResource
    resource_class : type[_StandardResource]
    factory : type[PydanticFactory]
    model_data : dict[str, Any]
    list_data : dict[str, Any]

    @override
    def setUp(self):
        """
        Set up the test case by initializing the client, resource, and model data.
        """
        self.setup_client()
        self.setup_resource()
        self.setup_model_data()
        self.setup_model()

    def setup_client(self):
        """
        Set up the PaperlessClient instance, optionally mocking environment variables.
        """
        if not hasattr(self, "client") or not self.client:
            if self.mock_env:
                with patch.dict(os.environ, self.env_data, clear=True):
                    self.client = PaperlessClient()
            else:
                self.client = PaperlessClient()

    def setup_resource(self):
        """
        Set up the resource instance using the resource class.
        """
        if not getattr(self, "resource", None) and (resource_class := getattr(self, 'resource_class', None)):
            self.resource = resource_class(client=self.client) # pylint: disable=not-callable

    def setup_model_data(self):
        """
        Load model data if the resource is set.
        """
        if getattr(self, "resource", None):
            self.load_model_data()

    def setup_model(self):
        """
        Set up the model instance using the factory and model data.
        """
        if getattr(self, "resource", None) and getattr(self, "factory", None):
            self.model = self.create_model(**self.model_data)

    def create_model(self, *args, **kwargs : Any) -> _StandardModel:
        """
        Create a model instance using the factory.

        Args:
            *args: Positional arguments for the factory.
            **kwargs: Keyword arguments for the factory.

        Returns:
            A new model instance.
        """
        return self.factory.build(*args, **kwargs)

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
        return [self.create_model(*args, **kwargs) for _ in range(count)]

    def load_model(self, resource_name : str | None = None) -> _StandardModel:
        """
        Load a model instance from sample data.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A new model instance created from the sample data.
        """
        sample_data = self.load_model_data(resource_name)
        return self.create_model(**sample_data)

    def load_list(self, resource_name : str | None = None) -> list[_StandardModel]:
        """
        Load a list of model instances from sample data.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A list of new model instances created from the sample data.
        """
        sample_data = self.load_list_data(resource_name)
        return [self.create_model(**item) for item in sample_data["results"]]

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
        if not getattr(self, "model_data", None):
            resource_name = resource_name or self.resource.name
            filename = f"{resource_name}_item.json"
            model_data = load_sample_data(filename)
            self.model_data = self.resource.transform_data_output(model_data)
        return self.model_data

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

class DocumentTest(TestCase["Document", "DocumentResource"]):
    """
    A test case for the Document model and resource.
    """
    resource_class = DocumentResource
    factory = DocumentFactory

class DocumentTypeTest(TestCase["DocumentType", "DocumentTypeResource"]):
    """
    A test case for the DocumentType model and resource.
    """
    resource_class = DocumentTypeResource
    factory = DocumentTypeFactory

class CorrespondentTest(TestCase["Correspondent", "CorrespondentResource"]):
    """
    A test case for the Correspondent model and resource.
    """
    resource_class = CorrespondentResource
    factory = CorrespondentFactory

class TagTest(TestCase["Tag", "TagResource"]):
    """
    A test case for the Tag model and resource.
    """
    resource_class = TagResource
    factory = TagFactory

class UserTest(TestCase["User", "UserResource"]):
    """
    A test case for the User model and resource.
    """
    resource_class = UserResource
    factory = UserFactory

class GroupTest(TestCase["Group", "GroupResource"]):
    """
    A test case for the Group model and resource.
    """
    resource_class = GroupResource
    factory = GroupFactory

class ProfileTest(TestCase["Profile", "ProfileResource"]):
    """
    A test case for the Profile model and resource.
    """
    resource_class = ProfileResource
    factory = ProfileFactory

class TaskTest(TestCase["Task", "TaskResource"]):
    """
    A test case for the Task model and resource.
    """
    resource_class = TaskResource
    factory = TaskFactory

class WorkflowTest(TestCase["Workflow", "WorkflowResource"]):
    """
    A test case for the Workflow model and resource.
    """
    resource_class = WorkflowResource
    factory = WorkflowFactory

class SavedViewTest(TestCase["SavedView", "SavedViewResource"]):
    """
    A test case for the SavedView model and resource.
    """
    resource_class = SavedViewResource
    factory = SavedViewFactory

class ShareLinksTest(TestCase["ShareLinks", "ShareLinksResource"]):
    """
    A test case for ShareLinks
    """
    resource_class = ShareLinksResource
    factory = ShareLinksFactory

class UISettingsTest(TestCase["UISettings", "UISettingsResource"]):
    """
    A test case for the UISettings model and resource.
    """
    resource_class = UISettingsResource
    factory = UISettingsFactory

class StoragePathTest(TestCase["StoragePath", "StoragePathResource"]):
    """
    A test case for the StoragePath model and resource.
    """
    resource_class = StoragePathResource
    factory = StoragePathFactory

class WorkflowActionTest(TestCase["WorkflowAction", "WorkflowActionResource"]):
    """
    A test case for the WorkflowAction model and resource.
    """
    resource_class = WorkflowActionResource
    factory = WorkflowActionFactory

class WorkflowTriggerTest(TestCase["WorkflowTrigger", "WorkflowTriggerResource"]):
    """
    A test case for the WorkflowTrigger model and resource.
    """
    resource_class = WorkflowTriggerResource
    factory = WorkflowTriggerFactory
