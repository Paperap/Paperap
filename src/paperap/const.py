"""
Constants and base types for the Paperap library.

This module defines enumerations, constants, and base types used throughout
the Paperap library for interacting with Paperless-ngx. It includes status
enums, model configurations, URL templates, and type definitions that provide
a foundation for the API client.
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
    """
    String enumeration that handles unknown values gracefully.

    This base class extends StrEnum to automatically handle unknown values by
    returning a designated UNKNOWN value instead of raising an exception.
    Subclasses must define an UNKNOWN member.

    Example:
        >>> class Status(StrEnumWithUnknown):
        ...     ACTIVE = "active"
        ...     INACTIVE = "inactive"
        ...     UNKNOWN = "unknown"
        >>> Status("active")
        <Status.ACTIVE: 'active'>
        >>> Status("nonexistent")
        <Status.UNKNOWN: 'unknown'>

    """

    @override
    @classmethod
    def _missing_(cls, value: object) -> str:
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN  # type: ignore # subclasses will define unknown


class IntEnumWithUnknown(IntEnum):
    """
    Integer enumeration that handles unknown values gracefully.

    This base class extends IntEnum to automatically handle unknown values by
    returning a designated UNKNOWN value instead of raising an exception.
    Subclasses must define an UNKNOWN member.

    Example:
        >>> class Priority(IntEnumWithUnknown):
        ...     HIGH = 3
        ...     MEDIUM = 2
        ...     LOW = 1
        ...     UNKNOWN = -1
        >>> Priority(2)
        <Priority.MEDIUM: 2>
        >>> Priority(99)
        <Priority.UNKNOWN: -1>

    """

    @override
    @classmethod
    def _missing_(cls, value: object) -> int:
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN  # type: ignore # subclasses will define unknown


class ConstModel(pydantic.BaseModel):
    """
    Base model for constant data structures with strict validation.

    This model provides consistent configuration for all constant data structures
    in the application, with strict validation and comparison capabilities.
    It enforces validation on assignment and defaults, and provides custom
    equality comparison with dictionaries.

    Attributes:
        model_config: Pydantic configuration dictionary that enforces strict validation.

    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        use_enum_values=True,
        validate_default=True,
        validate_assignment=True,
    )

    @override
    def __eq__(self, other: Any) -> bool:
        """
        Compare this model with another object for equality.

        Supports comparison with dictionaries by checking that all fields match,
        and with other ConstModel instances by comparing their serialized forms.

        Args:
            other: The object to compare with this model.

        Returns:
            bool: True if the objects are equal, False otherwise.

        """
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
    """
    URL templates for Paperless-ngx API endpoints.

    This class provides string templates for all API endpoints used by the client.
    Templates can be formatted with parameters like ${resource} and ${pk} to
    generate specific endpoint URLs.

    Note:
        This class may be deprecated in the future. It is currently used for reference.

    Attributes:
        index: API root endpoint.
        token: Authentication token endpoint.
        list: List endpoint for a resource type.
        detail: Detail endpoint for a specific resource.
        create: Creation endpoint for a resource type.
        update: Update endpoint for a specific resource.
        delete: Deletion endpoint for a specific resource.
        meta: Document metadata endpoint.
        next_asn: Endpoint to get the next available ASN.
        notes: Document notes endpoint.
        post: Document upload endpoint.
        single: Single document endpoint.
        suggestions: Suggestions endpoint for a resource.
        preview: Document preview endpoint.
        thumbnail: Document thumbnail endpoint.
        download: Document download endpoint.

    """

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


# Type aliases for API endpoints and responses
CommonEndpoints: TypeAlias = Literal["list", "detail", "create", "update", "delete"]
"""Type alias for common API endpoint names."""

Endpoints: TypeAlias = dict[CommonEndpoints | str, Template]
"""Type alias for a dictionary mapping endpoint names to URL templates."""

type ClientResponse = dict[str, Any] | list[dict[str, Any]] | None
"""Type alias for API response data structures."""


class FilteringStrategies(StrEnum):
    """
    Enumeration of filtering strategies for API queries.

    These strategies determine how field filtering is applied when querying resources.

    Attributes:
        WHITELIST: Only allow filtering on explicitly listed fields.
        BLACKLIST: Allow filtering on all fields except those explicitly listed.
        ALLOW_ALL: Allow filtering on all fields.
        ALLOW_NONE: Disallow filtering on all fields.

    """

    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    ALLOW_ALL = "allow_all"
    ALLOW_NONE = "allow_none"


class ModelStatus(StrEnum):
    """
    Enumeration of possible model states during lifecycle operations.

    These states track the current operation being performed on a model instance.

    Attributes:
        INITIALIZING: Model is being initialized with data.
        UPDATING: Model is being updated with new data.
        SAVING: Model is being saved to the server.
        READY: Model is ready for use.
        ERROR: An error occurred during a model operation.

    """

    INITIALIZING = "initializing"
    UPDATING = "updating"
    SAVING = "saving"
    READY = "ready"
    ERROR = "error"


class CustomFieldTypes(StrEnumWithUnknown):
    """
    Enumeration of supported custom field data types in Paperless-ngx.

    These types determine how custom field values are validated, stored, and displayed.

    Attributes:
        STRING: Text string value.
        BOOLEAN: Boolean (true/false) value.
        INTEGER: Whole number value.
        FLOAT: Decimal number value.
        MONETARY: Currency value.
        DATE: Date value.
        URL: Web URL value.
        DOCUMENT_LINK: Link to another document.
        UNKNOWN: Unknown field type (fallback).

    """

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
    """
    Model for custom field values associated with a document.

    Attributes:
        field: The ID of the custom field.
        value: The value of the custom field, which can be of any type
            depending on the field's data_type.

    """

    field: int
    value: Any


class CustomFieldTypedDict(TypedDict):
    """
    TypedDict for custom field values, used for type checking.

    This provides the same structure as CustomFieldValues but as a TypedDict
    for use in function signatures and type annotations.

    Attributes:
        field: The ID of the custom field.
        value: The value of the custom field.

    """

    field: int
    value: Any


# Possibly not used after refactoring
class DocumentMetadataType(ConstModel):
    """
    Model for document metadata extracted from files.

    This model represents metadata extracted from document files, such as
    PDF metadata, EXIF data, or other embedded information.

    Note:
        This class may not be used after refactoring.

    Attributes:
        namespace: The metadata namespace (e.g., "pdf", "exif").
        prefix: The metadata prefix.
        key: The metadata key name.
        value: The metadata value.

    """

    namespace: str | None = None
    prefix: str | None = None
    key: str | None = None
    value: str | None = None


class DocumentSearchHitType(ConstModel):
    """
    Model for search result hits with relevance information.

    This model represents a document search result with relevance scoring
    and highlighted text snippets showing where matches occurred.

    Attributes:
        score: The relevance score of the search hit.
        highlights: Highlighted text snippets from the document content.
        note_highlights: Highlighted text snippets from document notes.
        rank: The rank of this result in the overall search results.

    """

    score: float | None = None
    highlights: str | None = None
    note_highlights: str | None = None
    rank: int | None = None


class MatchingAlgorithmType(IntEnumWithUnknown):
    """
    Enumeration of matching algorithms used for document classification.

    These algorithms determine how Paperless-ngx matches documents to
    correspondents, document types, and tags during automatic classification.

    Attributes:
        NONE: No matching (manual assignment only).
        ANY: Match if any of the terms are found.
        ALL: Match only if all terms are found.
        LITERAL: Match the exact string.
        REGEX: Match using regular expressions.
        FUZZY: Match using fuzzy string matching.
        AUTO: Automatically select the best matching algorithm.
        UNKNOWN: Unknown algorithm type (fallback).

    """

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
    """
    Model for a set of user and group permissions.

    This model represents a collection of users and groups that have
    a specific permission on a resource.

    Attributes:
        users: List of user IDs with the permission.
        groups: List of group IDs with the permission.

    """

    users: list[int] = Field(default_factory=list)
    groups: list[int] = Field(default_factory=list)


class PermissionTableType(ConstModel):
    """
    Model for a complete permission table for a resource.

    This model represents all permissions for a resource, organized by
    permission type (view, change).

    Attributes:
        view: The set of users and groups with view permission.
        change: The set of users and groups with change permission.

    """

    view: PermissionSetType = Field(default_factory=PermissionSetType)
    change: PermissionSetType = Field(default_factory=PermissionSetType)


class RetrieveFileMode(StrEnum):
    """
    Enumeration of file retrieval modes.

    These modes determine how a document file is retrieved from the server.

    Attributes:
        DOWNLOAD: Download the full document file.
        PREVIEW: Get a preview version of the document.
        THUMBNAIL: Get a thumbnail image of the document.

    """

    DOWNLOAD = "download"
    PREVIEW = "preview"
    THUMBNAIL = "thumb"


class SavedViewFilterRuleType(ConstModel):
    """
    Model for a filter rule in a saved view.

    This model represents a single filtering rule that is part of a saved view,
    specifying how documents should be filtered.

    Attributes:
        rule_type: The type of filter rule (corresponds to FilterRuleType enum).
        value: The value to filter by.
        saved_view: The ID of the saved view this rule belongs to.

    """

    rule_type: int
    value: str | None = None
    saved_view: int | None = None


class ShareLinkFileVersionType(StrEnumWithUnknown):
    """
    Enumeration of file versions available for share links.

    These determine which version of a document is shared via a share link.

    Attributes:
        ARCHIVE: The archived version of the document (typically processed PDF).
        ORIGINAL: The original uploaded file.
        UNKNOWN: Unknown file version type (fallback).

    """

    ARCHIVE = "archive"
    ORIGINAL = "original"
    UNKNOWN = "unknown"

    @override
    @classmethod
    def _missing_(cls, value: object) -> "Literal[ShareLinkFileVersionType.UNKNOWN]":
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN


class StatusType(StrEnumWithUnknown):
    """
    Enumeration of general status values for system components.

    These status values indicate the operational state of various system components.

    Attributes:
        OK: The component is functioning normally.
        ERROR: The component has encountered an error.
        UNKNOWN: The component's status is unknown (fallback).

    """

    OK = "OK"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    @override
    @classmethod
    def _missing_(cls, value: object) -> "Literal[StatusType.UNKNOWN]":
        logger.debug("Handling unknown enum value", extra={"enum_class": cls.__name__, "value": value})
        return cls.UNKNOWN


class StatusDatabaseMigrationStatusType(ConstModel):
    """
    Model for database migration status information.

    This model represents the current state of database migrations in the system.

    Attributes:
        latest_migration: The name of the most recently applied migration.
        unapplied_migrations: List of migration names that have not been applied.

    """

    latest_migration: str | None = None
    unapplied_migrations: list[str] = Field(default_factory=list)


class StatusDatabaseType(ConstModel):
    """
    Model for database status information.

    This model represents the current status of the database system.

    Attributes:
        type: The type of database (e.g., "postgresql", "sqlite").
        url: The database connection URL.
        status: The operational status of the database.
        error: Error message if the database has encountered an error.
        migration_status: Information about database migrations.

    """

    type: str | None = None
    url: str | None = None
    status: StatusType | None = None
    error: str | None = None
    migration_status: StatusDatabaseMigrationStatusType | None = None


class StatusStorageType(ConstModel):
    """
    Model for storage status information.

    This model represents the current status of the storage system.

    Attributes:
        total: Total storage space in bytes.
        available: Available storage space in bytes.

    """

    total: int | None = None
    available: int | None = None


class StatusTasksType(ConstModel):
    """
    Model for task system status information.

    This model represents the current status of the task processing system,
    including Redis, Celery, indexing, and classification components.

    Attributes:
        redis_url: The Redis connection URL.
        redis_status: The operational status of Redis.
        redis_error: Error message if Redis has encountered an error.
        celery_status: The operational status of Celery.
        index_status: The operational status of the document index.
        index_last_modified: When the index was last modified.
        index_error: Error message if the index has encountered an error.
        classifier_status: The operational status of the document classifier.
        classifier_last_trained: When the classifier was last trained.
        classifier_error: Error message if the classifier has encountered an error.

    """

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
    """
    Enumeration of possible task statuses.

    These statuses represent the current state of a background task.

    Attributes:
        PENDING: Task is waiting to be executed.
        STARTED: Task has started execution.
        SUCCESS: Task has completed successfully.
        FAILURE: Task has failed.
        UNKNOWN: Task status is unknown (fallback).

    """

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class TaskTypeType(StrEnumWithUnknown):
    """
    Enumeration of task types.

    These types categorize tasks based on how they were initiated.

    Attributes:
        AUTO: Task was automatically triggered by the system.
        SCHEDULED_TASK: Task was scheduled to run at a specific time.
        MANUAL_TASK: Task was manually triggered by a user.
        UNKNOWN: Task type is unknown (fallback).

    """

    AUTO = "auto_task"
    SCHEDULED_TASK = "scheduled_task"
    MANUAL_TASK = "manual_task"
    UNKNOWN = "unknown"


class WorkflowActionType(IntEnumWithUnknown):
    """
    Enumeration of workflow action types.

    These types define what actions can be performed by a workflow.

    Attributes:
        ASSIGNMENT: Assign a value to a document field.
        REMOVAL: Remove a value from a document field.
        EMAIL: Send an email notification.
        WEBHOOK: Trigger a webhook.
        UNKNOWN: Unknown action type (fallback).

    """

    ASSIGNMENT = 1
    REMOVAL = 2
    EMAIL = 3
    WEBHOOK = 4
    UNKNOWN = -1


class WorkflowTriggerType(IntEnumWithUnknown):
    """
    Enumeration of workflow trigger types.

    These types define what events can trigger a workflow.

    Attributes:
        CONSUMPTION: Triggered when a document is consumed (processed).
        DOCUMENT_ADDED: Triggered when a document is added to the system.
        DOCUMENT_UPDATED: Triggered when a document is updated.
        UNKNOWN: Unknown trigger type (fallback).

    """

    CONSUMPTION = 1
    DOCUMENT_ADDED = 2
    DOCUMENT_UPDATED = 3
    UNKNOWN = -1


class WorkflowTriggerSourceType(IntEnumWithUnknown):
    """
    Enumeration of workflow trigger source types.

    These types define the source of documents that can trigger a workflow.

    Attributes:
        CONSUME_FOLDER: Documents from the consumption folder.
        API_UPLOAD: Documents uploaded via the API.
        MAIL_FETCH: Documents fetched from email.
        UNKNOWN: Unknown source type (fallback).

    """

    CONSUME_FOLDER = 1
    API_UPLOAD = 2
    MAIL_FETCH = 3
    UNKNOWN = -1


class WorkflowTriggerMatchingType(IntEnumWithUnknown):
    """
    Enumeration of workflow trigger matching algorithms.

    These algorithms determine how workflow triggers match documents.

    Attributes:
        NONE: No matching (triggers for all documents).
        ANY: Match if any of the terms are found.
        ALL: Match only if all terms are found.
        LITERAL: Match the exact string.
        REGEX: Match using regular expressions.
        FUZZY: Match using fuzzy string matching.
        UNKNOWN: Unknown matching type (fallback).

    """

    NONE = 0
    ANY = 1
    ALL = 2
    LITERAL = 3
    REGEX = 4
    FUZZY = 5
    UNKNOWN = -1


class ScheduleDateFieldType(StrEnumWithUnknown):
    """
    Enumeration of date fields that can be used for scheduling.

    These fields determine which document date is used for scheduling operations.

    Attributes:
        ADDED: The date the document was added to the system.
        CREATED: The date the document was created.
        MODIFIED: The date the document was last modified.
        CUSTOM_FIELD: A custom date field.
        UNKNOWN: Unknown date field type (fallback).

    """

    ADDED = "added"
    CREATED = "created"
    MODIFIED = "modified"
    CUSTOM_FIELD = "custom_field"
    UNKNOWN = "unknown"


class WorkflowTriggerScheduleDateFieldType(StrEnumWithUnknown):
    """
    Enumeration of date fields that can trigger scheduled workflows.

    These fields determine which document date is used for triggering
    scheduled workflows.

    Attributes:
        ADDED: The date the document was added to the system.
        CREATED: The date the document was created.
        MODIFIED: The date the document was last modified.
        CUSTOM_FIELD: A custom date field.
        UNKNOWN: Unknown date field type (fallback).

    """

    ADDED = "added"
    CREATED = "created"
    MODIFIED = "modified"
    CUSTOM_FIELD = "custom_field"
    UNKNOWN = "unknown"


class SavedViewDisplayModeType(StrEnumWithUnknown):
    """
    Enumeration of display modes for saved views.

    These modes determine how documents are displayed in a saved view.

    Attributes:
        TABLE: Display documents in a table format.
        SMALL_CARDS: Display documents as small cards.
        LARGE_CARDS: Display documents as large cards.
        UNKNOWN: Unknown display mode (fallback).

    """

    TABLE = "table"
    SMALL_CARDS = "smallCards"
    LARGE_CARDS = "largeCards"
    UNKNOWN = "unknown"


class SavedViewDisplayFieldType(StrEnumWithUnknown):
    """
    Enumeration of field types that can be displayed in saved views.

    These fields determine which document attributes are displayed in a saved view.

    Attributes:
        TITLE: Document title.
        CREATED: Document creation date.
        ADDED: Date the document was added to the system.
        TAGS: Document tags.
        CORRESPONDENT: Document correspondent.
        DOCUMENT_TYPE: Document type.
        STORAGE_PATH: Document storage path.
        NOTES: Document notes.
        OWNER: Document owner.
        SHARED: Whether the document is shared.
        ASN: Document archive serial number.
        PAGE_COUNT: Number of pages in the document.
        CUSTOM_FIELD: Custom field (format string with field ID).
        UNKNOWN: Unknown field type (fallback).

    """

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
    """
    Enumeration of document storage encryption types.

    These types determine how documents are encrypted in storage.

    Attributes:
        UNENCRYPTED: Documents are stored without encryption.
        GPG: Documents are encrypted using GPG.
        UNKNOWN: Unknown storage type (fallback).

    """

    UNENCRYPTED = "unencrypted"
    GPG = "gpg"
    UNKNOWN = "unknown"


class TaskNameType(StrEnumWithUnknown):
    """
    Enumeration of background task names.

    These names identify specific background tasks in the system.

    Attributes:
        CONSUME_FILE: Task for consuming and processing a document file.
        TRAIN_CLASSIFIER: Task for training the document classifier.
        CHECK_SANITY: Task for checking system sanity/integrity.
        INDEX_OPTIMIZE: Task for optimizing the document index.
        UNKNOWN: Unknown task name (fallback).

    """

    CONSUME_FILE = "consume_file"
    TRAIN_CLASSIFIER = "train_classifier"
    CHECK_SANITY = "check_sanity"
    INDEX_OPTIMIZE = "index_optimize"
    UNKNOWN = "unknown"


class EnrichmentConfig(pydantic.BaseModel):
    """
    Configuration for document enrichment services.

    Attributes:
        template_name: Name of the template to use
        template_dir: Optional custom directory for templates
        model: Model name for LLM services
        api_key: API key for LLM services
        api_url: Base URL for LLM services
        vision: Whether to use vision capabilities
        extract_images: Whether to extract images from documents
        max_images: Maximum number of images to extract
        max_tokens: Maximum tokens to generate in the response

    """

    template_name: str | None = None
    template_dir: str | None = None
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    api_url: str | None = None
    vision: bool = True
    extract_images: bool = True
    max_images: int = 2
    max_tokens: int = 500
