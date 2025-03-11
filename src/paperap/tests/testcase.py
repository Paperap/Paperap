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
    DocumentQuerySet,
    DocumentType,
    DocumentTypeQuerySet,
    Correspondent,
    CorrespondentQuerySet,
    Tag,
    TagQuerySet,
    User,
    UserQuerySet,
    Group,
    GroupQuerySet,
    Profile,
    ProfileQuerySet,
    Task,
    TaskQuerySet,
    Workflow,
    WorkflowQuerySet,
    SavedView,
    SavedViewQuerySet,
    ShareLinks,
    ShareLinksQuerySet,
    UISettings,
    UISettingsQuerySet,
    StoragePath,
    StoragePathQuerySet,
    WorkflowAction,
    WorkflowActionQuerySet,
    WorkflowTrigger,
    WorkflowTriggerQuerySet,
)
from paperap.resources import (
    BaseResource,
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
_StandardQuerySet = TypeVar("_StandardQuerySet", bound="BaseQuerySet", default="BaseQuerySet[_StandardModel]")

class TestCase(unittest.TestCase, Generic[_StandardModel, _StandardResource, _StandardQuerySet]):
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
    env_data : dict[str, Any] = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123', 'PAPERLESS_SAVE_ON_WRITE': 'False'}

    # Data for the test
    model_data_unparsed : dict[str, Any]
    model_data_parsed : dict[str, Any]
    list_data : dict[str, Any]

    # Instances
    client : "PaperlessClient"
    resource : _StandardResource
    model : _StandardModel

    # Types (TODO only one of these should be needed)
    factory : type[PydanticFactory]
    resource_class : type[_StandardResource]
    model_type : type[_StandardModel] | None = None
    queryset_type : type[_StandardQuerySet] | None = None

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
            self.model = self.resource.parse_to_model(self.model_data_parsed)

    def bake_model(self, *args, **kwargs : Any) -> _StandardModel:
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
        return self.resource.parse_to_model(sample_data)

    def load_list(self, resource_name : str | None = None) -> list[_StandardModel]:
        """
        Load a list of model instances from sample data.

        Args:
            resource_name: The name of the resource to load data for.

        Returns:
            A list of new model instances created from the sample data.
        """
        sample_data = self.load_list_data(resource_name)
        return [self.resource.parse_to_model(item) for item in sample_data["results"]]

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
            resource_name = resource_name or self.resource.name
            filename = f"{resource_name}_item.json"
            model_data_parsed = load_sample_data(filename)
            self.model_data_parsed = self.resource.transform_data_output(**model_data_parsed)
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

    def assert_queryset_callback(
        self,
        *,
        queryset : _StandardQuerySet,
        callback : Callable[[_StandardModel], bool] | None = None,
        expected_count : int | None = None
    ):
        """
        Generic method to test queryset filtering.

        Args:
            queryset: The queryset to test
            callback: A callback function to test each model instance.
            expected_count: The expected result count of the queryset.
        """
        if expected_count is not None:
            self.assertEqual(queryset.count(), expected_count)

        count = 0
        for model in queryset:
            count += 1
            if self.model_type:
                self.assertIsInstance(model, self.model_type)
            else:
                self.assertIsInstance(model, StandardModel)

            if callback:
                self.assertTrue(callback(model), f"Condition failed for {model}")

            # Check multiple results, but avoid paging
            if count > 5:
                break

        if expected_count is not None:
            expected_iterations = min(expected_count, 6)
            self.assertEqual(count, expected_iterations, f"Documents iteration unexpected. Count: {expected_count} -> Expected {expected_iterations} iterations, got {count}.")

    def assert_queryset_callback_patched(
        self,
        *,
        queryset : _StandardQuerySet | Callable[..., _StandardQuerySet],
        sample_data : dict[str, Any],
        callback : Callable[[_StandardModel], bool] | None = None,
        expected_count : int | None = None,
    ):
        """
        Generic method to test queryset filtering.

        Args:
            queryset: The queryset to test, or a method which retrieves a queryset.
            sample_data: The sample data to use for the queryset.
            callback: A callback function to test each model instance.
            expected_count: The expected result count of the queryset.
        """
        # Setup defaults
        if expected_count is None:
            expected_count = int(sample_data['count'])

        with patch('paperap.client.PaperlessClient.request') as mock_request:
            mock_request.return_value = sample_data
            if not isinstance(queryset, Callable):
                qs = queryset
            else:
                qs = queryset()
                if self.queryset_type:
                    self.assertIsInstance(qs, self.queryset_type)
                else:
                    self.assertIsInstance(qs, BaseQuerySet)

            self.assertEqual(qs.count(), expected_count)

            self.assert_queryset_callback(
                queryset = qs,
                expected_count = expected_count,
                callback = callback
            )

class DocumentTest(TestCase["Document", "DocumentResource", "DocumentQuerySet"]):
    """
    A test case for the Document model and resource.
    """
    resource_class = DocumentResource
    model_type = Document
    queryset_type = DocumentQuerySet
    factory = DocumentFactory

class DocumentTypeTest(TestCase["DocumentType", "DocumentTypeResource", "DocumentTypeQuerySet"]):
    """
    A test case for the DocumentType model and resource.
    """
    resource_class = DocumentTypeResource
    model_type = DocumentType
    queryset_type = DocumentTypeQuerySet
    factory = DocumentTypeFactory

class CorrespondentTest(TestCase["Correspondent", "CorrespondentResource", "CorrespondentQuerySet"]):
    """
    A test case for the Correspondent model and resource.
    """
    resource_class = CorrespondentResource
    model_type = Correspondent
    queryset_type = CorrespondentQuerySet
    factory = CorrespondentFactory

class TagTest(TestCase["Tag", "TagResource", "TagQuerySet"]):
    """
    A test case for the Tag model and resource.
    """
    resource_class = TagResource
    model_type = Tag
    queryset_type = TagQuerySet
    factory = TagFactory

class UserTest(TestCase["User", "UserResource", "UserQuerySet"]):
    """
    A test case for the User model and resource.
    """
    resource_class = UserResource
    model_type = User
    queryset_type = UserQuerySet
    factory = UserFactory

class GroupTest(TestCase["Group", "GroupResource", "GroupQuerySet"]):
    """
    A test case for the Group model and resource.
    """
    resource_class = GroupResource
    model_type = Group
    queryset_type = GroupQuerySet
    factory = GroupFactory

class ProfileTest(TestCase["Profile", "ProfileResource", "ProfileQuerySet"]):
    """
    A test case for the Profile model and resource.
    """
    resource_class = ProfileResource
    model_type = Profile
    queryset_type = ProfileQuerySet
    factory = ProfileFactory

class TaskTest(TestCase["Task", "TaskResource", "TaskQuerySet"]):
    """
    A test case for the Task model and resource.
    """
    resource_class = TaskResource
    model_type = Task
    queryset_type = TaskQuerySet
    factory = TaskFactory

class WorkflowTest(TestCase["Workflow", "WorkflowResource", "WorkflowQuerySet"]):
    """
    A test case for the Workflow model and resource.
    """
    resource_class = WorkflowResource
    model_type = Workflow
    queryset_type = WorkflowQuerySet
    factory = WorkflowFactory

class SavedViewTest(TestCase["SavedView", "SavedViewResource", "SavedViewQuerySet"]):
    """
    A test case for the SavedView model and resource.
    """
    resource_class = SavedViewResource
    model_type = SavedView
    queryset_type = SavedViewQuerySet
    factory = SavedViewFactory

class ShareLinksTest(TestCase["ShareLinks", "ShareLinksResource", "ShareLinksQuerySet"]):
    """
    A test case for ShareLinks
    """
    resource_class = ShareLinksResource
    model_type = ShareLinks
    queryset_type = ShareLinksQuerySet
    factory = ShareLinksFactory

class UISettingsTest(TestCase["UISettings", "UISettingsResource", "UISettingsQuerySet"]):
    """
    A test case for the UISettings model and resource.
    """
    resource_class = UISettingsResource
    model_type = UISettings
    queryset_type = UISettingsQuerySet
    factory = UISettingsFactory

class StoragePathTest(TestCase["StoragePath", "StoragePathResource", "StoragePathQuerySet"]):
    """
    A test case for the StoragePath model and resource.
    """
    resource_class = StoragePathResource
    model_type = StoragePath
    queryset_type = StoragePathQuerySet
    factory = StoragePathFactory

class WorkflowActionTest(TestCase["WorkflowAction", "WorkflowActionResource", "WorkflowActionQuerySet"]):
    """
    A test case for the WorkflowAction model and resource.
    """
    resource_class = WorkflowActionResource
    model_type = WorkflowAction
    queryset_type = WorkflowActionQuerySet
    factory = WorkflowActionFactory

class WorkflowTriggerTest(TestCase["WorkflowTrigger", "WorkflowTriggerResource", "WorkflowTriggerQuerySet"]):
    """
    A test case for the WorkflowTrigger model and resource.
    """
    resource_class = WorkflowTriggerResource
    model_type = WorkflowTrigger
    queryset_type = WorkflowTrigger
    factory = WorkflowTriggerFactory
