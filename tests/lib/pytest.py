
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, override

import pytest
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
from tests.lib.testcase import TestMixin

logger = logging.getLogger(__name__)

class PyTestCase[_StandardModel, _StandardResource, _StandardQuerySet](
    TestMixin[_StandardModel, _StandardResource, _StandardQuerySet]
):
    @pytest.fixture(autouse=True)
    def setUp(self, mocker) -> None:
        """
        Set up the test case by initializing the client, resource, and model data.
        """
        self.setup_references()
        self.setup_client(mocker)
        self.setup_resource()
        self.setup_model_data()
        self.setup_model()

    @override
    def setup_client(self, mocker : Any = None, **kwargs):
        """Set up the PaperlessClient instance, optionally mocking environment variables."""
        if not hasattr(self, "client") or not self.client:
            if self.mock_env:
                # Patch os.environ with pytest
                mocker.patch.dict(os.environ, self.env_data, clear=True)
                self.client = PaperlessClient()
            else:
                self.client = PaperlessClient()

    @override
    def validate_field(self, field_name: str, test_cases: list[tuple[Any, Any]]):
        """Validate that a model field processes data correctly."""
        for input_value, expected in test_cases:
            if isinstance(expected, type) and issubclass(expected, Exception):
                with pytest.raises(expected, match=f"Setting {self.model.__class__.__name__}.{field_name} failed"):
                    setattr(self.model, field_name, input_value)
            else:
                setattr(self.model, field_name, input_value)
                real_value = getattr(self.model, field_name)
                assert isinstance(real_value, type(expected)), f"Expected type {type(expected)}, got {type(real_value)}"
                assert real_value == expected, f"Expected {expected}, got {real_value}"

class CustomFieldPyTest(PyTestCase["CustomField", "CustomFieldResource", "CustomFieldQuerySet"]):

    """
    A test case for the CustomField model and resource.
    """

    resource_class = CustomFieldResource
    model_type = CustomField
    queryset_type = CustomFieldQuerySet
    #factory = PydanticFactory

class DocumentPyTest(PyTestCase["Document", "DocumentResource", "DocumentQuerySet"]):

    """
    A test case for the Document model and resource.
    """

    resource_class = DocumentResource
    model_type = Document
    queryset_type = DocumentQuerySet
    factory = DocumentFactory

class DocumentTypePyTest(PyTestCase["DocumentType", "DocumentTypeResource", "DocumentTypeQuerySet"]):

    """
    A test case for the DocumentType model and resource.
    """

    resource_class = DocumentTypeResource
    model_type = DocumentType
    queryset_type = DocumentTypeQuerySet
    factory = DocumentTypeFactory

class CorrespondentPyTest(PyTestCase["Correspondent", "CorrespondentResource", "CorrespondentQuerySet"]):

    """
    A test case for the Correspondent model and resource.
    """

    resource_class = CorrespondentResource
    model_type = Correspondent
    queryset_type = CorrespondentQuerySet
    factory = CorrespondentFactory

class TagPyTest(PyTestCase["Tag", "TagResource", "TagQuerySet"]):

    """
    A test case for the Tag model and resource.
    """

    resource_class = TagResource
    model_type = Tag
    queryset_type = TagQuerySet
    factory = TagFactory

class UserPyTest(PyTestCase["User", "UserResource", "UserQuerySet"]):

    """
    A test case for the User model and resource.
    """

    resource_class = UserResource
    model_type = User
    queryset_type = UserQuerySet
    factory = UserFactory

class GroupPyTest(PyTestCase["Group", "GroupResource", "GroupQuerySet"]):

    """
    A test case for the Group model and resource.
    """

    resource_class = GroupResource
    model_type = Group
    queryset_type = GroupQuerySet
    factory = GroupFactory

class ProfilePyTest(PyTestCase["Profile", "ProfileResource", "ProfileQuerySet"]):

    """
    A test case for the Profile model and resource.
    """

    resource_class = ProfileResource
    model_type = Profile
    queryset_type = ProfileQuerySet
    factory = ProfileFactory

class TaskPyTest(PyTestCase["Task", "TaskResource", "TaskQuerySet"]):

    """
    A test case for the Task model and resource.
    """

    resource_class = TaskResource
    model_type = Task
    queryset_type = TaskQuerySet
    factory = TaskFactory

class WorkflowPyTest(PyTestCase["Workflow", "WorkflowResource", "WorkflowQuerySet"]):

    """
    A test case for the Workflow model and resource.
    """

    resource_class = WorkflowResource
    model_type = Workflow
    queryset_type = WorkflowQuerySet
    factory = WorkflowFactory

class SavedViewPyTest(PyTestCase["SavedView", "SavedViewResource", "SavedViewQuerySet"]):

    """
    A test case for the SavedView model and resource.
    """

    resource_class = SavedViewResource
    model_type = SavedView
    queryset_type = SavedViewQuerySet
    factory = SavedViewFactory

class ShareLinksPyTest(PyTestCase["ShareLinks", "ShareLinksResource", "ShareLinksQuerySet"]):

    """
    A test case for ShareLinks
    """

    resource_class = ShareLinksResource
    model_type = ShareLinks
    queryset_type = ShareLinksQuerySet
    factory = ShareLinksFactory

class UISettingsPyTest(PyTestCase["UISettings", "UISettingsResource", "UISettingsQuerySet"]):

    """
    A test case for the UISettings model and resource.
    """

    resource_class = UISettingsResource
    model_type = UISettings
    queryset_type = UISettingsQuerySet
    factory = UISettingsFactory

class StoragePathPyTest(PyTestCase["StoragePath", "StoragePathResource", "StoragePathQuerySet"]):

    """
    A test case for the StoragePath model and resource.
    """

    resource_class = StoragePathResource
    model_type = StoragePath
    queryset_type = StoragePathQuerySet
    factory = StoragePathFactory

class WorkflowActionPyTest(PyTestCase["WorkflowAction", "WorkflowActionResource", "WorkflowActionQuerySet"]):

    """
    A test case for the WorkflowAction model and resource.
    """

    resource_class = WorkflowActionResource
    model_type = WorkflowAction
    queryset_type = WorkflowActionQuerySet
    factory = WorkflowActionFactory

class WorkflowTriggerPyTest(PyTestCase["WorkflowTrigger", "WorkflowTriggerResource", "WorkflowTriggerQuerySet"]):

    """
    A test case for the WorkflowTrigger model and resource.
    """

    resource_class = WorkflowTriggerResource
    model_type = WorkflowTrigger
    queryset_type = WorkflowTriggerQuerySet
    factory = WorkflowTriggerFactory
