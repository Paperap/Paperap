"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    testcase.py
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
import json
import os
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator
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
    QuerySet,
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
	# Load sample response from tests/sample_data/{model}_{endpoint}.json
	sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
	with open(sample_data_filepath, "r") as f:
		text = f.read()
		sample_data = json.loads(text)
	return sample_data

_StandardModel = TypeVar("_StandardModel", bound="StandardModel", default="StandardModel")
_StandardResource = TypeVar("_StandardResource", bound="StandardResource", default="StandardResource[_StandardModel]")

class TestCase(unittest.TestCase, Generic[_StandardModel, _StandardResource]):
    client : "PaperlessClient"
    mock_env : bool = True
    env_data : dict[str, Any] = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123', 'PAPERLESS_SAVE_ON_WRITE': 'False'}
    resource : _StandardResource
    resource_class : type[_StandardResource]
    factory : PydanticFactory
    model_data : dict[str, Any]
    list_data : dict[str, Any]

    def setUp(self):
        self.setup_client()
        self.setup_resource()
        self.setup_model_data()
        self.setup_model()

    def setup_client(self):
        if not hasattr(self, "client") or not self.client:
            if self.mock_env:
                with patch.dict(os.environ, self.env_data, clear=True):
                    self.client = PaperlessClient()
            else:
                self.client = PaperlessClient()

    def setup_resource(self):
        if not getattr(self, "resource", None) and (resource_class := getattr(self, 'resource_class', None)):
            self.resource = resource_class(client=self.client)

    def setup_model_data(self):
        if getattr(self, "resource", None):
            self.load_model_data()

    def setup_model(self):
        if getattr(self, "resource", None) and getattr(self, "factory", None):
            self.model = self.create_model(**self.model_data)

    def create_model(self, *args, **kwargs) -> _StandardModel:
        return self.factory(*args, **kwargs)

    def create_list(self, count : int, *args, **kwargs) -> list[_StandardModel]:
        return [self.create_model(*args, **kwargs) for _ in range(count)]

    def load_model(self, resource_name : str | None = None) -> _StandardModel:
        sample_data = self.load_model_data(resource_name)
        return self.create_model(**sample_data)

    def load_list(self, resource_name : str | None = None) -> list[_StandardModel]:
        sample_data = self.load_list_data(resource_name)
        return [self.create_model(**item) for item in sample_data["results"]]

    def _call_list_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel] | None = None, **kwargs) -> QuerySet[_StandardModel]:
        if not resource:
            if not (resource := getattr(self,"resource", None)):
                raise ValueError("Resource not provided")

        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).filter(**kwargs)
        return resource.filter(**kwargs)

    def _call_get_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel], id : int) -> _StandardModel:
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).get(id)

        return resource.get(id)

    def list_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel] | None = None, **kwargs) -> QuerySet[_StandardModel]:
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

    def get_resource(self, resource : type[StandardResource[_StandardModel]] | StandardResource[_StandardModel], id : int) -> _StandardModel:
        try:
            sample_data = self.load_model_data()
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                return self._call_get_resource(resource, id)
        except FileNotFoundError:
            return self._call_get_resource(resource, id)

    def load_model_data(self, resource_name : str | None = None) -> dict[str, Any]:
        if not getattr(self, "model_data", None):
            resource_name = resource_name or self.resource.name
            filename = f"{resource_name}_item.json"
            self.model_data = load_sample_data(filename)
        return self.model_data

    def load_list_data(self, resource_name : str | None = None) -> dict[str, Any]:
        if not getattr(self, "list_data", None):
            resource_name = resource_name or self.resource.name
            filename = f"{resource_name}_list.json"
            self.list_data = load_sample_data(filename)
        return self.list_data



class DocumentTest(TestCase["Document", "DocumentResource"]):
    resource_class = DocumentResource
    factory = DocumentFactory

class DocumentTypeTest(TestCase["DocumentType", "DocumentTypeResource"]):
    resource_class = DocumentTypeResource
    factory = DocumentTypeFactory

class CorrespondentTest(TestCase["Correspondent", "CorrespondentResource"]):
    resource_class = CorrespondentResource
    factory = CorrespondentFactory

class TagTest(TestCase["Tag", "TagResource"]):
    resource_class = TagResource
    factory = TagFactory

class UserTest(TestCase["User", "UserResource"]):
    resource_class = UserResource
    factory = UserFactory

class GroupTest(TestCase["Group", "GroupResource"]):
    resource_class = GroupResource
    factory = GroupFactory

class ProfileTest(TestCase["Profile", "ProfileResource"]):
    resource_class = ProfileResource
    factory = ProfileFactory

class TaskTest(TestCase["Task", "TaskResource"]):
    resource_class = TaskResource
    factory = TaskFactory

class WorkflowTest(TestCase["Workflow", "WorkflowResource"]):
    resource_class = WorkflowResource
    factory = WorkflowFactory

class SavedViewTest(TestCase["SavedView", "SavedViewResource"]):
    resource_class = SavedViewResource
    factory = SavedViewFactory

class ShareLinksTest(TestCase["ShareLinks", "ShareLinksResource"]):
    resource_class = ShareLinksResource
    factory = ShareLinksFactory

class UISettingsTest(TestCase["UISettings", "UISettingsResource"]):
    resource_class = UISettingsResource
    factory = UISettingsFactory

class StoragePathTest(TestCase["StoragePath", "StoragePathResource"]):
    resource_class = StoragePathResource
    factory = StoragePathFactory

class WorkflowActionTest(TestCase["WorkflowAction", "WorkflowActionResource"]):
    resource_class = WorkflowActionResource
    factory = WorkflowActionFactory

class WorkflowTriggerTest(TestCase["WorkflowTrigger", "WorkflowTriggerResource"]):
    resource_class = WorkflowTriggerResource
    factory = WorkflowTriggerFactory
