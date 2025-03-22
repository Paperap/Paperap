"""
----------------------------------------------------------------------------

   METADATA:

       File:    const.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum, IntEnum, StrEnum
from string import Template
from typing import (
    Any,
    Iterator,
    Literal,
    NotRequired,
    Protocol,
    Required,
    Self,
    TypeAlias,
    TypedDict,
    override,
    runtime_checkable,
)

import pydantic
from pydantic import ConfigDict, Field

logger = logging.getLogger(__name__)


class StrEnumWithUnknown(StrEnum):
    @override
    @classmethod
    def _missing_(cls, value: object) -> str:
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN # type: ignore # subclasses will define unknown


class IntEnumWithUnknown(IntEnum):
    @override
    @classmethod
    def _missing_(cls, value: object) -> int:
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN # type: ignore # subclasses will define unknown


class ConstModel(pydantic.BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        use_enum_values=True,
        validate_default=True,
        validate_assignment=True,
    )

    @override
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            # Ensure the dictionary keys match the model fields
            expected_keys = set(self.model_fields.keys())
            if set(other.keys()) != expected_keys:
                return False
            return all(getattr(self, key) == other.get(key) for key in expected_keys)

        # This check probably isn't necessary before calling super (TODO?)
        if isinstance(other, self.__class__):
            # Compare all fields of the model
            return self.model_dump() == other.model_dump()

        return super().__eq__(other)


class URLS:
    # May be deprecated in the future. Used for reference currently.
    index: Template = Template("/api/")
    token: Template = Template("/api/token/")
    list: Template = Template("/api/${resource}/")
    detail: Template = Template("/api/${resource}/${pk}/")
    create: Template = Template("/api/${resource}/")
    update: Template = Template("/api/${resource}/${pk}/")
    delete: Template = Template("/api/${resource}/${pk}/")
    meta: Template = Template("/api/document/${pk}/metadata/")
    next_asn: Template = Template("/api/document/next_asn/")
    notes: Template = Template("/api/document/${pk}/notes/")
    post: Template = Template("/api/documents/post_document/")
    single: Template = Template("/api/document/${pk}/")
    suggestions: Template = Template("/api/${resource}/${pk}/suggestions/")
    preview: Template = Template("/api/${resource}/${pk}/preview/")
    thumbnail: Template = Template("/api/${resource}/${pk}/thumb/")
    download: Template = Template("/api/${resource}/${pk}/download/")


CommonEndpoints: TypeAlias = Literal["list", "detail", "create", "update", "delete"]
Endpoints: TypeAlias = dict[CommonEndpoints | str, Template]


class FilteringStrategies(StrEnum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    ALLOW_ALL = "allow_all"
    ALLOW_NONE = "allow_none"


class ModelStatus(StrEnum):
    INITIALIZING = "initializing"
    UPDATING = "updating"
    SAVING = "saving"
    READY = "ready"
    ERROR = "error"


class CustomFieldTypes(StrEnumWithUnknown):
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    MONETARY = "monetary"
    DATE = "date"
    URL = "url"
    DOCUMENT_LINK = "documentlink"
    UNKNOWN = "unknown"


class CustomFieldValues(ConstModel):
    field: int
    value: Any


class CustomFieldTypedDict(TypedDict):
    field: int
    value: Any


# Possibly not used after refactoring
class DocumentMetadataType(ConstModel):
    namespace: str | None = None
    prefix: str | None = None
    key: str | None = None
    value: str | None = None


class DocumentSearchHitType(ConstModel):
    score: float | None = None
    highlights: str | None = None
    note_highlights: str | None = None
    rank: int | None = None


class MatchingAlgorithmType(IntEnumWithUnknown):
    NONE = 0
    ANY = 1
    ALL = 2
    LITERAL = 3
    REGEX = 4
    FUZZY = 5
    AUTO = 6
    UNKNOWN = -1

    @override
    @classmethod
    def _missing_(cls, value: object) -> "Literal[MatchingAlgorithmType.UNKNOWN]":
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN


class PermissionSetType(ConstModel):
    users: list[int] = Field(default_factory=list)
    groups: list[int] = Field(default_factory=list)


class PermissionTableType(ConstModel):
    view: PermissionSetType = Field(default_factory=PermissionSetType)
    change: PermissionSetType = Field(default_factory=PermissionSetType)


class RetrieveFileMode(StrEnum):
    DOWNLOAD = "download"
    PREVIEW = "preview"
    THUMBNAIL = "thumb"


class SavedViewFilterRuleType(ConstModel):
    rule_type: int
    value: str | None = None
    saved_view: int | None = None


class ShareLinkFileVersionType(StrEnumWithUnknown):
    ARCHIVE = "archive"
    ORIGINAL = "original"
    UNKNOWN = "unknown"

    @override
    @classmethod
    def _missing_(cls, value: object) -> "Literal[ShareLinkFileVersionType.UNKNOWN]":
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN


class StatusType(StrEnumWithUnknown):
    OK = "OK"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    @override
    @classmethod
    def _missing_(cls, value: object) -> "Literal[StatusType.UNKNOWN]":
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN


class StatusDatabaseMigrationStatusType(ConstModel):
    latest_migration: str | None = None
    unapplied_migrations: list[str] = Field(default_factory=list)


class StatusDatabaseType(ConstModel):
    type: str | None = None
    url: str | None = None
    status: StatusType | None = None
    error: str | None = None
    migration_status: StatusDatabaseMigrationStatusType | None = None


class StatusStorageType(ConstModel):
    total: int | None = None
    available: int | None = None


class StatusTasksType(ConstModel):
    redis_url: str | None = None
    redis_status: StatusType | None = None
    redis_error: str | None = None
    celery_status: StatusType | None = None
    index_status: StatusType | None = None
    index_last_modified: datetime | None = None
    index_error: str | None = None
    classifier_status: StatusType | None = None
    classifier_last_trained: datetime | None = None
    classifier_error: str | None = None


class TaskStatusType(StrEnumWithUnknown):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class TaskTypeType(StrEnumWithUnknown):
    AUTO = "auto_task"
    SCHEDULED_TASK = "scheduled_task"
    MANUAL_TASK = "manual_task"
    UNKNOWN = "unknown"


class WorkflowActionType(IntEnumWithUnknown):
    ASSIGNMENT = 1
    REMOVAL = 2
    EMAIL = 3
    WEBHOOK = 4
    UNKNOWN = -1


class WorkflowTriggerType(IntEnumWithUnknown):
    CONSUMPTION = 1
    DOCUMENT_ADDED = 2
    DOCUMENT_UPDATED = 3
    UNKNOWN = -1


class WorkflowTriggerSourceType(IntEnumWithUnknown):
    CONSUME_FOLDER = 1
    API_UPLOAD = 2
    MAIL_FETCH = 3
    UNKNOWN = -1


class WorkflowTriggerMatchingType(IntEnumWithUnknown):
    NONE = 0
    ANY = 1
    ALL = 2
    LITERAL = 3
    REGEX = 4
    FUZZY = 5
    UNKNOWN = -1


class ScheduleDateFieldType(StrEnumWithUnknown):
    ADDED = "added"
    CREATED = "created"
    MODIFIED = "modified"
    CUSTOM_FIELD = "custom_field"
    UNKNOWN = "unknown"


class WorkflowTriggerScheduleDateFieldType(StrEnumWithUnknown):
    ADDED = "added"
    CREATED = "created"
    MODIFIED = "modified"
    CUSTOM_FIELD = "custom_field"
    UNKNOWN = "unknown"


class SavedViewDisplayModeType(StrEnumWithUnknown):
    TABLE = "table"
    SMALL_CARDS = "smallCards"
    LARGE_CARDS = "largeCards"
    UNKNOWN = "unknown"


class SavedViewDisplayFieldType(StrEnumWithUnknown):
    TITLE = "title"
    CREATED = "created"
    ADDED = "added"
    TAGS = "tag"
    CORRESPONDENT = "correspondent"
    DOCUMENT_TYPE = "documenttype"
    STORAGE_PATH = "storagepath"
    NOTES = "note"
    OWNER = "owner"
    SHARED = "shared"
    ASN = "asn"
    PAGE_COUNT = "pagecount"
    CUSTOM_FIELD = "custom_field_%d"
    UNKNOWN = "unknown"


class DocumentStorageType(StrEnumWithUnknown):
    UNENCRYPTED = "unencrypted"
    GPG = "gpg"
    UNKNOWN = "unknown"


class TaskNameType(StrEnumWithUnknown):
    CONSUME_FILE = "consume_file"
    TRAIN_CLASSIFIER = "train_classifier"
    CHECK_SANITY = "check_sanity"
    INDEX_OPTIMIZE = "index_optimize"
    UNKNOWN = "unknown"
