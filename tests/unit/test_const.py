

from __future__ import annotations

import unittest
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import pydantic

from paperap.const import (
    URLS,
    ConstModel,
    CustomFieldTypes,
    CustomFieldValues,
    DocumentMetadataType,
    DocumentSearchHitType,
    DocumentStorageType,
    FilteringStrategies,
    IntEnumWithUnknown,
    MatchingAlgorithmType,
    ModelStatus,
    PermissionSetType,
    PermissionTableType,
    RetrieveFileMode,
    SavedViewDisplayFieldType,
    SavedViewDisplayModeType,
    SavedViewFilterRuleType,
    ScheduleDateFieldType,
    ShareLinkFileVersionType,
    StatusDatabaseMigrationStatusType,
    StatusDatabaseType,
    StatusStorageType,
    StatusTasksType,
    StatusType,
    StrEnumWithUnknown,
    TaskNameType,
    TaskStatusType,
    TaskTypeType,
    WorkflowActionType,
    WorkflowTriggerMatchingType,
    WorkflowTriggerScheduleDateFieldType,
    WorkflowTriggerSourceType,
    WorkflowTriggerType,
)


class TestStrEnumWithUnknown(unittest.TestCase):
    """
    Test the StrEnumWithUnknown class.

    Written By claude
    """

    def test_valid_enum_value(self):
        """
        Test that valid enum values are correctly returned.

        Written By claude
        """
        self.assertEqual(StatusType.OK, "OK")
        self.assertEqual(StatusType.ERROR, "ERROR")

    def test_invalid_enum_value(self):
        """
        Test that invalid enum values return UNKNOWN.

        Written By claude
        """
        invalid_value = "INVALID_VALUE"
        self.assertEqual(StatusType(invalid_value), StatusType.UNKNOWN)
        self.assertEqual(StatusType(invalid_value), "UNKNOWN")

    def test_enum_comparison(self):
        """
        Test enum value comparison.

        Written By claude
        """
        self.assertEqual(StatusType.OK, "OK")
        self.assertNotEqual(StatusType.OK, "ERROR")
        self.assertTrue(StatusType.OK == "OK")
        self.assertFalse(StatusType.OK == "ERROR")


class TestIntEnumWithUnknown(unittest.TestCase):
    """
    Test the IntEnumWithUnknown class.

    Written By claude
    """

    def test_valid_enum_value(self):
        """
        Test that valid enum values are correctly returned.

        Written By claude
        """
        self.assertEqual(MatchingAlgorithmType.NONE, 0)
        self.assertEqual(MatchingAlgorithmType.ANY, 1)

    def test_invalid_enum_value(self):
        """
        Test that invalid enum values return UNKNOWN.

        Written By claude
        """
        invalid_value = 999
        self.assertEqual(MatchingAlgorithmType(invalid_value), MatchingAlgorithmType.UNKNOWN)
        self.assertEqual(MatchingAlgorithmType(invalid_value), -1)

    def test_enum_comparison(self):
        """
        Test enum value comparison.

        Written By claude
        """
        self.assertEqual(MatchingAlgorithmType.NONE, 0)
        self.assertNotEqual(MatchingAlgorithmType.NONE, 1)
        self.assertTrue(MatchingAlgorithmType.NONE == 0)
        self.assertFalse(MatchingAlgorithmType.NONE == 1)


class TestConstModel(unittest.TestCase):
    """
    Test the ConstModel class.

    Written By claude
    """

    class TestModel(ConstModel):
        """Test model for ConstModel tests."""
        name: str
        value: int
        optional: str | None = None

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        model = self.TestModel(name="test", value=42)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)
        self.assertIsNone(model.optional)

    def test_model_validation(self):
        """
        Test model validation.

        Written By claude
        """
        # Missing required field
        with self.assertRaises(pydantic.ValidationError):
            self.TestModel(name="test")

        # Wrong type
        with self.assertRaises(pydantic.ValidationError):
            self.TestModel(name="test", value="not an int")

    def test_model_equality_with_dict(self):
        """
        Test model equality comparison with dict.

        Written By claude
        """
        model = self.TestModel(name="test", value=42)

        # Equal dict
        equal_dict = {"name": "test", "value": 42, "optional": None}
        self.assertEqual(model, equal_dict)

        # Different value
        different_dict = {"name": "test", "value": 43, "optional": None}
        self.assertNotEqual(model, different_dict)

        # Missing key
        incomplete_dict = {"name": "test", "value": 42}
        self.assertNotEqual(model, incomplete_dict)

        # Extra key
        extra_dict = {"name": "test", "value": 42, "optional": None, "extra": "value"}
        self.assertNotEqual(model, extra_dict)

    def test_model_equality_with_model(self):
        """
        Test model equality comparison with another model.

        Written By claude
        """
        model1 = self.TestModel(name="test", value=42)
        model2 = self.TestModel(name="test", value=42)
        model3 = self.TestModel(name="different", value=42)

        self.assertEqual(model1, model2)
        self.assertNotEqual(model1, model3)

    def test_model_equality_with_other_types(self):
        """
        Test model equality comparison with other types.

        Written By claude
        """
        model = self.TestModel(name="test", value=42)

        self.assertNotEqual(model, "not a model")
        self.assertNotEqual(model, 42)
        self.assertNotEqual(model, None)


class TestURLs(unittest.TestCase):
    """
    Test the URLS class.

    Written By claude
    """

    def test_url_templates(self):
        """
        Test URL template substitution.

        Written By claude
        """
        self.assertEqual(URLS.index.substitute(), "/api/")
        self.assertEqual(URLS.token.substitute(), "/api/token/")

        self.assertEqual(
            URLS.list.substitute(resource="documents"),
            "/api/documents/"
        )

        self.assertEqual(
            URLS.detail.substitute(resource="documents", pk=123),
            "/api/documents/123/"
        )

        self.assertEqual(
            URLS.meta.substitute(pk=123),
            "/api/document/123/metadata/"
        )


class TestFilteringStrategies(unittest.TestCase):
    """
    Test the FilteringStrategies enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(FilteringStrategies.WHITELIST, "whitelist")
        self.assertEqual(FilteringStrategies.BLACKLIST, "blacklist")
        self.assertEqual(FilteringStrategies.ALLOW_ALL, "allow_all")
        self.assertEqual(FilteringStrategies.ALLOW_NONE, "allow_none")


class TestModelStatus(unittest.TestCase):
    """
    Test the ModelStatus enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(ModelStatus.INITIALIZING, "initializing")
        self.assertEqual(ModelStatus.UPDATING, "updating")
        self.assertEqual(ModelStatus.SAVING, "saving")
        self.assertEqual(ModelStatus.READY, "ready")
        self.assertEqual(ModelStatus.ERROR, "error")


class TestCustomFieldTypes(unittest.TestCase):
    """
    Test the CustomFieldTypes enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(CustomFieldTypes.STRING, "string")
        self.assertEqual(CustomFieldTypes.BOOLEAN, "boolean")
        self.assertEqual(CustomFieldTypes.INTEGER, "integer")
        self.assertEqual(CustomFieldTypes.FLOAT, "float")
        self.assertEqual(CustomFieldTypes.MONETARY, "monetary")
        self.assertEqual(CustomFieldTypes.DATE, "date")
        self.assertEqual(CustomFieldTypes.URL, "url")
        self.assertEqual(CustomFieldTypes.DOCUMENT_LINK, "documentlink")
        self.assertEqual(CustomFieldTypes.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(CustomFieldTypes("nonexistent"), CustomFieldTypes.UNKNOWN)


class TestCustomFieldValues(unittest.TestCase):
    """
    Test the CustomFieldValues model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        model = CustomFieldValues(field=1, value="test")
        self.assertEqual(model.field, 1)
        self.assertEqual(model.value, "test")

    def test_model_validation(self):
        """
        Test model validation.

        Written By claude
        """
        # Missing required field
        with self.assertRaises(pydantic.ValidationError):
            CustomFieldValues(field=1)


class TestDocumentMetadataType(unittest.TestCase):
    """
    Test the DocumentMetadataType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # All fields are optional
        model = DocumentMetadataType()
        self.assertIsNone(model.namespace)
        self.assertIsNone(model.prefix)
        self.assertIsNone(model.key)
        self.assertIsNone(model.value)

        # With values
        model = DocumentMetadataType(
            namespace="test_namespace",
            prefix="test_prefix",
            key="test_key",
            value="test_value"
        )
        self.assertEqual(model.namespace, "test_namespace")
        self.assertEqual(model.prefix, "test_prefix")
        self.assertEqual(model.key, "test_key")
        self.assertEqual(model.value, "test_value")


class TestDocumentSearchHitType(unittest.TestCase):
    """
    Test the DocumentSearchHitType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # All fields are optional
        model = DocumentSearchHitType()
        self.assertIsNone(model.score)
        self.assertIsNone(model.highlights)
        self.assertIsNone(model.note_highlights)
        self.assertIsNone(model.rank)

        # With values
        model = DocumentSearchHitType(
            score=0.95,
            highlights="<em>highlighted</em> text",
            note_highlights="<em>note</em> highlights",
            rank=1
        )
        self.assertEqual(model.score, 0.95)
        self.assertEqual(model.highlights, "<em>highlighted</em> text")
        self.assertEqual(model.note_highlights, "<em>note</em> highlights")
        self.assertEqual(model.rank, 1)


class TestMatchingAlgorithmType(unittest.TestCase):
    """
    Test the MatchingAlgorithmType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(MatchingAlgorithmType.NONE, 0)
        self.assertEqual(MatchingAlgorithmType.ANY, 1)
        self.assertEqual(MatchingAlgorithmType.ALL, 2)
        self.assertEqual(MatchingAlgorithmType.LITERAL, 3)
        self.assertEqual(MatchingAlgorithmType.REGEX, 4)
        self.assertEqual(MatchingAlgorithmType.FUZZY, 5)
        self.assertEqual(MatchingAlgorithmType.AUTO, 6)
        self.assertEqual(MatchingAlgorithmType.UNKNOWN, -1)

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(MatchingAlgorithmType(999), MatchingAlgorithmType.UNKNOWN)


class TestPermissionSetType(unittest.TestCase):
    """
    Test the PermissionSetType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # Default values
        model = PermissionSetType()
        self.assertEqual(model.users, [])
        self.assertEqual(model.groups, [])

        # With values
        model = PermissionSetType(users=[1, 2], groups=[3, 4])
        self.assertEqual(model.users, [1, 2])
        self.assertEqual(model.groups, [3, 4])


class TestPermissionTableType(unittest.TestCase):
    """
    Test the PermissionTableType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # Default values
        model = PermissionTableType()
        self.assertEqual(model.view, PermissionSetType())
        self.assertEqual(model.change, PermissionSetType())

        # With values
        view_set = PermissionSetType(users=[1, 2], groups=[3, 4])
        change_set = PermissionSetType(users=[5, 6], groups=[7, 8])
        model = PermissionTableType(view=view_set, change=change_set)

        self.assertEqual(model.view, view_set)
        self.assertEqual(model.change, change_set)
        self.assertEqual(model.view.users, [1, 2])
        self.assertEqual(model.view.groups, [3, 4])
        self.assertEqual(model.change.users, [5, 6])
        self.assertEqual(model.change.groups, [7, 8])


class TestRetrieveFileMode(unittest.TestCase):
    """
    Test the RetrieveFileMode enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(RetrieveFileMode.DOWNLOAD, "download")
        self.assertEqual(RetrieveFileMode.PREVIEW, "preview")
        self.assertEqual(RetrieveFileMode.THUMBNAIL, "thumb")


class TestSavedViewFilterRuleType(unittest.TestCase):
    """
    Test the SavedViewFilterRuleType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # Only rule_type is required
        model = SavedViewFilterRuleType(rule_type=1)
        self.assertEqual(model.rule_type, 1)
        self.assertIsNone(model.value)
        self.assertIsNone(model.saved_view)

        # With all values
        model = SavedViewFilterRuleType(rule_type=1, value="test", saved_view=2)
        self.assertEqual(model.rule_type, 1)
        self.assertEqual(model.value, "test")
        self.assertEqual(model.saved_view, 2)

    def test_model_validation(self):
        """
        Test model validation.

        Written By claude
        """
        # Missing required field
        with self.assertRaises(pydantic.ValidationError):
            SavedViewFilterRuleType()


class TestShareLinkFileVersionType(unittest.TestCase):
    """
    Test the ShareLinkFileVersionType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(ShareLinkFileVersionType.ARCHIVE, "archive")
        self.assertEqual(ShareLinkFileVersionType.ORIGINAL, "original")
        self.assertEqual(ShareLinkFileVersionType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(
            ShareLinkFileVersionType("nonexistent"),
            ShareLinkFileVersionType.UNKNOWN
        )


class TestStatusType(unittest.TestCase):
    """
    Test the StatusType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(StatusType.OK, "OK")
        self.assertEqual(StatusType.ERROR, "ERROR")
        self.assertEqual(StatusType.UNKNOWN, "UNKNOWN")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(StatusType("nonexistent"), StatusType.UNKNOWN)


class TestStatusDatabaseMigrationStatusType(unittest.TestCase):
    """
    Test the StatusDatabaseMigrationStatusType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # Default values
        model = StatusDatabaseMigrationStatusType()
        self.assertIsNone(model.latest_migration)
        self.assertEqual(model.unapplied_migrations, [])

        # With values
        model = StatusDatabaseMigrationStatusType(
            latest_migration="0001_initial",
            unapplied_migrations=["0002_auto", "0003_add_field"]
        )
        self.assertEqual(model.latest_migration, "0001_initial")
        self.assertEqual(model.unapplied_migrations, ["0002_auto", "0003_add_field"])


class TestStatusDatabaseType(unittest.TestCase):
    """
    Test the StatusDatabaseType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # All fields are optional
        model = StatusDatabaseType()
        self.assertIsNone(model.type)
        self.assertIsNone(model.url)
        self.assertIsNone(model.status)
        self.assertIsNone(model.error)
        self.assertIsNone(model.migration_status)

        # With values
        migration_status = StatusDatabaseMigrationStatusType(
            latest_migration="0001_initial",
            unapplied_migrations=["0002_auto"]
        )
        model = StatusDatabaseType(
            type="postgresql",
            url="postgres://user:pass@localhost/db",
            status=StatusType.OK,
            error=None,
            migration_status=migration_status
        )
        self.assertEqual(model.type, "postgresql")
        self.assertEqual(model.url, "postgres://user:pass@localhost/db")
        self.assertEqual(model.status, StatusType.OK)
        self.assertIsNone(model.error)
        self.assertEqual(model.migration_status, migration_status)


class TestStatusStorageType(unittest.TestCase):
    """
    Test the StatusStorageType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # All fields are optional
        model = StatusStorageType()
        self.assertIsNone(model.total)
        self.assertIsNone(model.available)

        # With values
        model = StatusStorageType(total=1000, available=500)
        self.assertEqual(model.total, 1000)
        self.assertEqual(model.available, 500)


class TestStatusTasksType(unittest.TestCase):
    """
    Test the StatusTasksType model.

    Written By claude
    """

    def test_model_creation(self):
        """
        Test creating a model instance.

        Written By claude
        """
        # All fields are optional
        model = StatusTasksType()
        self.assertIsNone(model.redis_url)
        self.assertIsNone(model.redis_status)
        self.assertIsNone(model.redis_error)
        self.assertIsNone(model.celery_status)
        self.assertIsNone(model.index_status)
        self.assertIsNone(model.index_last_modified)
        self.assertIsNone(model.index_error)
        self.assertIsNone(model.classifier_status)
        self.assertIsNone(model.classifier_last_trained)
        self.assertIsNone(model.classifier_error)

        # With values
        now = datetime.now()
        model = StatusTasksType(
            redis_url="redis://localhost:6379/0",
            redis_status=StatusType.OK,
            redis_error=None,
            celery_status=StatusType.OK,
            index_status=StatusType.OK,
            index_last_modified=now,
            index_error=None,
            classifier_status=StatusType.OK,
            classifier_last_trained=now,
            classifier_error=None
        )
        self.assertEqual(model.redis_url, "redis://localhost:6379/0")
        self.assertEqual(model.redis_status, StatusType.OK)
        self.assertIsNone(model.redis_error)
        self.assertEqual(model.celery_status, StatusType.OK)
        self.assertEqual(model.index_status, StatusType.OK)
        self.assertEqual(model.index_last_modified, now)
        self.assertIsNone(model.index_error)
        self.assertEqual(model.classifier_status, StatusType.OK)
        self.assertEqual(model.classifier_last_trained, now)
        self.assertIsNone(model.classifier_error)


class TestTaskStatusType(unittest.TestCase):
    """
    Test the TaskStatusType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(TaskStatusType.PENDING, "PENDING")
        self.assertEqual(TaskStatusType.STARTED, "STARTED")
        self.assertEqual(TaskStatusType.SUCCESS, "SUCCESS")
        self.assertEqual(TaskStatusType.FAILURE, "FAILURE")
        self.assertEqual(TaskStatusType.UNKNOWN, "UNKNOWN")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(TaskStatusType("nonexistent"), TaskStatusType.UNKNOWN)


class TestTaskTypeType(unittest.TestCase):
    """
    Test the TaskTypeType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(TaskTypeType.AUTO, "auto_task")
        self.assertEqual(TaskTypeType.SCHEDULED_TASK, "scheduled_task")
        self.assertEqual(TaskTypeType.MANUAL_TASK, "manual_task")
        self.assertEqual(TaskTypeType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(TaskTypeType("nonexistent"), TaskTypeType.UNKNOWN)


class TestWorkflowActionType(unittest.TestCase):
    """
    Test the WorkflowActionType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(WorkflowActionType.ASSIGNMENT, 1)
        self.assertEqual(WorkflowActionType.REMOVAL, 2)
        self.assertEqual(WorkflowActionType.EMAIL, 3)
        self.assertEqual(WorkflowActionType.WEBHOOK, 4)
        self.assertEqual(WorkflowActionType.UNKNOWN, -1)

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(WorkflowActionType(999), WorkflowActionType.UNKNOWN)


class TestWorkflowTriggerType(unittest.TestCase):
    """
    Test the WorkflowTriggerType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerType.CONSUMPTION, 1)
        self.assertEqual(WorkflowTriggerType.DOCUMENT_ADDED, 2)
        self.assertEqual(WorkflowTriggerType.DOCUMENT_UPDATED, 3)
        self.assertEqual(WorkflowTriggerType.UNKNOWN, -1)

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerType(999), WorkflowTriggerType.UNKNOWN)


class TestWorkflowTriggerSourceType(unittest.TestCase):
    """
    Test the WorkflowTriggerSourceType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerSourceType.CONSUME_FOLDER, 1)
        self.assertEqual(WorkflowTriggerSourceType.API_UPLOAD, 2)
        self.assertEqual(WorkflowTriggerSourceType.MAIL_FETCH, 3)
        self.assertEqual(WorkflowTriggerSourceType.UNKNOWN, -1)

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerSourceType(999), WorkflowTriggerSourceType.UNKNOWN)


class TestWorkflowTriggerMatchingType(unittest.TestCase):
    """
    Test the WorkflowTriggerMatchingType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerMatchingType.NONE, 0)
        self.assertEqual(WorkflowTriggerMatchingType.ANY, 1)
        self.assertEqual(WorkflowTriggerMatchingType.ALL, 2)
        self.assertEqual(WorkflowTriggerMatchingType.LITERAL, 3)
        self.assertEqual(WorkflowTriggerMatchingType.REGEX, 4)
        self.assertEqual(WorkflowTriggerMatchingType.FUZZY, 5)
        self.assertEqual(WorkflowTriggerMatchingType.UNKNOWN, -1)

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerMatchingType(999), WorkflowTriggerMatchingType.UNKNOWN)


class TestScheduleDateFieldType(unittest.TestCase):
    """
    Test the ScheduleDateFieldType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(ScheduleDateFieldType.ADDED, "added")
        self.assertEqual(ScheduleDateFieldType.CREATED, "created")
        self.assertEqual(ScheduleDateFieldType.MODIFIED, "modified")
        self.assertEqual(ScheduleDateFieldType.CUSTOM_FIELD, "custom_field")
        self.assertEqual(ScheduleDateFieldType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(ScheduleDateFieldType("nonexistent"), ScheduleDateFieldType.UNKNOWN)


class TestWorkflowTriggerScheduleDateFieldType(unittest.TestCase):
    """
    Test the WorkflowTriggerScheduleDateFieldType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(WorkflowTriggerScheduleDateFieldType.ADDED, "added")
        self.assertEqual(WorkflowTriggerScheduleDateFieldType.CREATED, "created")
        self.assertEqual(WorkflowTriggerScheduleDateFieldType.MODIFIED, "modified")
        self.assertEqual(WorkflowTriggerScheduleDateFieldType.CUSTOM_FIELD, "custom_field")
        self.assertEqual(WorkflowTriggerScheduleDateFieldType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(
            WorkflowTriggerScheduleDateFieldType("nonexistent"),
            WorkflowTriggerScheduleDateFieldType.UNKNOWN
        )


class TestSavedViewDisplayModeType(unittest.TestCase):
    """
    Test the SavedViewDisplayModeType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(SavedViewDisplayModeType.TABLE, "table")
        self.assertEqual(SavedViewDisplayModeType.SMALL_CARDS, "smallCards")
        self.assertEqual(SavedViewDisplayModeType.LARGE_CARDS, "largeCards")
        self.assertEqual(SavedViewDisplayModeType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(
            SavedViewDisplayModeType("nonexistent"),
            SavedViewDisplayModeType.UNKNOWN
        )


class TestSavedViewDisplayFieldType(unittest.TestCase):
    """
    Test the SavedViewDisplayFieldType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(SavedViewDisplayFieldType.TITLE, "title")
        self.assertEqual(SavedViewDisplayFieldType.CREATED, "created")
        self.assertEqual(SavedViewDisplayFieldType.ADDED, "added")
        self.assertEqual(SavedViewDisplayFieldType.TAGS, "tag")
        self.assertEqual(SavedViewDisplayFieldType.CORRESPONDENT, "correspondent")
        self.assertEqual(SavedViewDisplayFieldType.DOCUMENT_TYPE, "documenttype")
        self.assertEqual(SavedViewDisplayFieldType.STORAGE_PATH, "storagepath")
        self.assertEqual(SavedViewDisplayFieldType.NOTES, "note")
        self.assertEqual(SavedViewDisplayFieldType.OWNER, "owner")
        self.assertEqual(SavedViewDisplayFieldType.SHARED, "shared")
        self.assertEqual(SavedViewDisplayFieldType.ASN, "asn")
        self.assertEqual(SavedViewDisplayFieldType.PAGE_COUNT, "pagecount")
        self.assertEqual(SavedViewDisplayFieldType.CUSTOM_FIELD, "custom_field_%d")
        self.assertEqual(SavedViewDisplayFieldType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(
            SavedViewDisplayFieldType("nonexistent"),
            SavedViewDisplayFieldType.UNKNOWN
        )


class TestDocumentStorageType(unittest.TestCase):
    """
    Test the DocumentStorageType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(DocumentStorageType.UNENCRYPTED, "unencrypted")
        self.assertEqual(DocumentStorageType.GPG, "gpg")
        self.assertEqual(DocumentStorageType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(DocumentStorageType("nonexistent"), DocumentStorageType.UNKNOWN)


class TestTaskNameType(unittest.TestCase):
    """
    Test the TaskNameType enum.

    Written By claude
    """

    def test_enum_values(self):
        """
        Test enum values.

        Written By claude
        """
        self.assertEqual(TaskNameType.CONSUME_FILE, "consume_file")
        self.assertEqual(TaskNameType.TRAIN_CLASSIFIER, "train_classifier")
        self.assertEqual(TaskNameType.CHECK_SANITY, "check_sanity")
        self.assertEqual(TaskNameType.INDEX_OPTIMIZE, "index_optimize")
        self.assertEqual(TaskNameType.UNKNOWN, "unknown")

    def test_unknown_value(self):
        """
        Test handling of unknown values.

        Written By claude
        """
        self.assertEqual(TaskNameType("nonexistent"), TaskNameType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
