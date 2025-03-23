
from __future__ import annotations

import json
import logging
import os
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, override
from unittest.mock import MagicMock, patch

from pydantic import ValidationError
from typing_extensions import TypeAlias, TypeVar

from paperap.client import PaperlessClient
from paperap.exceptions import PaperapError
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

_StandardModel = TypeVar("_StandardModel", bound=StandardModel, default=StandardModel)
_StandardResource = TypeVar("_StandardResource", bound=StandardResource, default=StandardResource)
_StandardQuerySet = TypeVar("_StandardQuerySet", bound=StandardQuerySet, default=StandardQuerySet)

class UnitTestConfigurationError(PaperapError):

    """Raised when there is a configuration error in the testing setup."""

    pass

class UnitTestCase(
    unittest.TestCase,
    TestMixin[_StandardModel, _StandardResource, _StandardQuerySet]
):
    @override
    def setUp(self) -> None:
        """
        Set up the test case by initializing the client, resource, and model data.
        """
        self._reset_attributes()

    @override
    def setup_client(self, **kwargs) -> None:
        """
        Set up the PaperlessClient instance, optionally mocking environment variables.
        """
        if self.mock_env:
            with patch.dict(os.environ, self.env_data, clear=True):
                self.client = PaperlessClient()
        else:
            self.client = PaperlessClient()

    @override
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
        self._meta.save_on_write = False
        for (input_value, expected) in test_cases:
            with self.subTest(field=field_name, input_value=input_value):
                if type(expected) is type and issubclass(expected, Exception):
                    with self.assertRaises(expected, msg=f"Setting {self.model.__class__.__name__} field {field_name} failed with input {input_value}"):
                        setattr(self.model, field_name, input_value)
                else:
                    setattr(self.model, field_name, input_value)
                    real_value = getattr(self.model, field_name)
                    self.assertIsInstance(real_value, type(expected), f"Setting {self.model.__class__.__name__} field {field_name} failed with input {input_value}, expected {expected}")
                    self.assertEqual(
                        real_value,
                        expected,
                        f"Setting {self.model.__class__.__name__} field {field_name} failed with input {input_value}"
                    )

    def assert_queryset_callback(
        self,
        *,
        queryset : StandardQuerySet[_StandardModel],
        callback : Callable[[_StandardModel], bool] | None = None,
        expected_count : int | None = None
    ) -> None:
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
        queryset : StandardQuerySet[_StandardModel] | Callable[..., StandardQuerySet[_StandardModel]],
        sample_data : dict[str, Any],
        callback : Callable[[_StandardModel], bool] | None = None,
        expected_count : int | None = None,
    ) -> None:
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

class CustomFieldUnitTest(UnitTestCase["CustomField", "CustomFieldResource", "CustomFieldQuerySet"]):

    """
    A test case for the CustomField model and resource.
    """

    resource_class = CustomFieldResource
    model_type = CustomField
    queryset_type = CustomFieldQuerySet
    #factory = PydanticFactory

class DocumentUnitTest(UnitTestCase["Document", "DocumentResource", "DocumentQuerySet"]):

    """
    A test case for the Document model and resource.
    """

    resource_class = DocumentResource
    model_type = Document
    queryset_type = DocumentQuerySet
    factory = DocumentFactory

class DocumentTypeUnitTest(UnitTestCase["DocumentType", "DocumentTypeResource", "DocumentTypeQuerySet"]):

    """
    A test case for the DocumentType model and resource.
    """

    resource_class = DocumentTypeResource
    model_type = DocumentType
    queryset_type = DocumentTypeQuerySet
    factory = DocumentTypeFactory

class CorrespondentUnitTest(UnitTestCase["Correspondent", "CorrespondentResource", "CorrespondentQuerySet"]):

    """
    A test case for the Correspondent model and resource.
    """

    resource_class = CorrespondentResource
    model_type = Correspondent
    queryset_type = CorrespondentQuerySet
    factory = CorrespondentFactory

class TagUnitTest(UnitTestCase["Tag", "TagResource", "TagQuerySet"]):

    """
    A test case for the Tag model and resource.
    """

    resource_class = TagResource
    model_type = Tag
    queryset_type = TagQuerySet
    factory = TagFactory

class UserUnitTest(UnitTestCase["User", "UserResource", "UserQuerySet"]):

    """
    A test case for the User model and resource.
    """

    resource_class = UserResource
    model_type = User
    queryset_type = UserQuerySet
    factory = UserFactory

class GroupUnitTest(UnitTestCase["Group", "GroupResource", "GroupQuerySet"]):

    """
    A test case for the Group model and resource.
    """

    resource_class = GroupResource
    model_type = Group
    queryset_type = GroupQuerySet
    factory = GroupFactory

class ProfileUnitTest(UnitTestCase["Profile", "ProfileResource", "ProfileQuerySet"]):

    """
    A test case for the Profile model and resource.
    """

    resource_class = ProfileResource
    model_type = Profile
    queryset_type = ProfileQuerySet
    factory = ProfileFactory

class TaskUnitTest(UnitTestCase["Task", "TaskResource", "TaskQuerySet"]):

    """
    A test case for the Task model and resource.
    """

    resource_class = TaskResource
    model_type = Task
    queryset_type = TaskQuerySet
    factory = TaskFactory

class WorkflowUnitTest(UnitTestCase["Workflow", "WorkflowResource", "WorkflowQuerySet"]):

    """
    A test case for the Workflow model and resource.
    """

    resource_class = WorkflowResource
    model_type = Workflow
    queryset_type = WorkflowQuerySet
    factory = WorkflowFactory

class SavedViewUnitTest(UnitTestCase["SavedView", "SavedViewResource", "SavedViewQuerySet"]):

    """
    A test case for the SavedView model and resource.
    """

    resource_class = SavedViewResource
    model_type = SavedView
    queryset_type = SavedViewQuerySet
    factory = SavedViewFactory

class ShareLinksUnitTest(UnitTestCase["ShareLinks", "ShareLinksResource", "ShareLinksQuerySet"]):

    """
    A test case for ShareLinks
    """

    resource_class = ShareLinksResource
    model_type = ShareLinks
    queryset_type = ShareLinksQuerySet
    factory = ShareLinksFactory

class UISettingsUnitTest(UnitTestCase["UISettings", "UISettingsResource", "UISettingsQuerySet"]):

    """
    A test case for the UISettings model and resource.
    """

    resource_class = UISettingsResource
    model_type = UISettings
    queryset_type = UISettingsQuerySet
    factory = UISettingsFactory

class StoragePathUnitTest(UnitTestCase["StoragePath", "StoragePathResource", "StoragePathQuerySet"]):

    """
    A test case for the StoragePath model and resource.
    """

    resource_class = StoragePathResource
    model_type = StoragePath
    queryset_type = StoragePathQuerySet
    factory = StoragePathFactory

class WorkflowActionUnitTest(UnitTestCase["WorkflowAction", "WorkflowActionResource", "WorkflowActionQuerySet"]):

    """
    A test case for the WorkflowAction model and resource.
    """

    resource_class = WorkflowActionResource
    model_type = WorkflowAction
    queryset_type = WorkflowActionQuerySet
    factory = WorkflowActionFactory

class WorkflowTriggerUnitTest(UnitTestCase["WorkflowTrigger", "WorkflowTriggerResource", "WorkflowTriggerQuerySet"]):

    """
    A test case for the WorkflowTrigger model and resource.
    """

    resource_class = WorkflowTriggerResource
    model_type = WorkflowTrigger
    queryset_type = WorkflowTriggerQuerySet
    factory = WorkflowTriggerFactory
