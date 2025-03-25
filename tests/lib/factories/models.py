

from __future__ import annotations

import logging
import secrets
from abc import ABC
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, override
import json
import time
import tempfile
import uuid
import factory
from factory.base import StubObject
from faker import Faker
from typing_extensions import TypeVar

from paperap.const import CustomFieldTypes
from paperap.models import (
    Correspondent,
    CustomField,
    Document,
    DocumentMetadata,
    DocumentNote,
    DocumentSuggestions,
    DocumentType,
    DownloadedDocument,
    Group,
    MetadataElement,
    Profile,
    SavedView,
    ShareLinks,
    StandardModel,
    StoragePath,
    Tag,
    Task,
    UISettings,
    User,
    Workflow,
    WorkflowAction,
    WorkflowTrigger,
)
from paperap.client import PaperlessClient

if TYPE_CHECKING:
    from paperap.resources import BaseResource

fake = Faker()

logger = logging.getLogger(__name__)

class PydanticFactory[_StandardModel](factory.Factory[_StandardModel]):
    """Base factory for Pydantic models."""
    id : int = factory.Faker("random_int", min=1, max=1000)

    class Meta: # type: ignore # pyright handles this wrong
        abstract = True

    @classmethod
    def get_resource(cls) -> "BaseResource":
        """
        Get the resource for the model.

        Returns:
            The resource for the model specified in this factory's Meta.model

        """
        return cls._meta.model._resource # type: ignore # model is always defined on subclasses

    @classmethod
    def create_api_data(cls, exclude_unset : bool = False, **kwargs : Any) -> dict[str, Any]:
        """
        Create a model, then transform its fields into sample API data.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the model creation.

        Returns:
            dict: A dictionary of the model's fields.

        """
        _instance = cls.build(**kwargs)
        return cls.get_resource().transform_data_output(_instance, exclude_unset = exclude_unset)

    @classmethod
    def to_dict(cls, exclude_unset : bool = False, **kwargs) -> dict[str, Any]:
        """
        Create a model, and return a dictionary of the model's fields.

        Args:
            exclude_unset (bool): Whether to exclude fields that are unset.
            **kwargs: Arbitrary keyword arguments to pass to the model creation.

        Returns:
            dict: A dictionary of the model's fields.

        """
        _instance = cls.create(**kwargs)
        return _instance.to_dict(exclude_unset=exclude_unset)

    @classmethod
    @override
    def create(cls, _relationships : bool = True, **kwargs: Any) -> _StandardModel:
        """
        Create a model with the given attributes.

        Args:
            _relationships: If False, all relationship fields will be omitted.
            **kwargs: Arbitrary keyword arguments to pass to the model creation.

        Returns:
            A model instance.
        """
        if not _relationships:
            kwargs = cls._omit_relationship_fields(kwargs)

        # Call the parent create method with the updated kwargs
        return super().create(**kwargs)

    @classmethod
    def _omit_relationship_fields(cls, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Omit all fields that represent a relationship to another model.
        Subclasses should override the _RELATIONSHIPS attribute to specify which fields are relationships.
        By default, if _RELATIONSHIPS is not defined, returns kwargs unchanged.
        """
        relationship_fields = getattr(cls, "_RELATIONSHIPS", set())
        for field in relationship_fields:
            kwargs.pop(field, None)
        return kwargs


class CorrespondentFactory(PydanticFactory[Correspondent]):
    _RELATIONSHIPS = {"owner"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Correspondent

    slug = factory.LazyFunction(fake.slug)
    name = factory.Sequence(lambda n: f"Correspondent-{n}-{fake.word()}")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=-1, max=6)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=100)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class CustomFieldFactory(PydanticFactory[CustomField]):
    _RELATIONSHIPS = {"extra_data"}

    class Meta: # type: ignore # pyright handles this wrong
        model = CustomField

    name = factory.Faker("word")
    data_type = "string"
    extra_data = factory.Dict({"key": fake.word(), "value": fake.word()})
    document_count = factory.Faker("random_int", min=0, max=100)

class DocumentNoteFactory(PydanticFactory[DocumentNote]):
    _RELATIONSHIPS = {"document", "user", "transaction_id"}

    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentNote

    note = factory.Faker("sentence")
    created = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    deleted_at = None
    restored_at = None
    transaction_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    document = factory.Faker("random_int", min=1, max=1000)
    user = factory.Faker("random_int", min=1, max=1000)

class DocumentFactory(PydanticFactory[Document]):
    _RELATIONSHIPS = {
        "correspondent_id", "document_type_id", "owner", "storage_path_id",
        "tag_ids", "notes", "custom_field_dicts"
    }

    class Meta: # type: ignore # pyright handles this wrong
        model = Document

    @classmethod
    def upload_sync(cls, client: "PaperlessClient", file_path: Path | None = None, wait: bool = True, **kwargs) -> Document:
        """
        Upload a document and wait for it to complete.

        Args:
            client: PaperlessClient instance
            file_path: Path to the file to upload (optional - will generate a text file if None)
            wait: Whether to wait for the upload to complete
            **kwargs: Additional document attributes to set after upload

        Returns:
            The created Document instance

        Raises:
            ValueError: If the document upload fails
        """
        # Generate a temp file if none provided
        if file_path is None:
            with tempfile.TemporaryDirectory() as temp_dir:
                unique_id = str(uuid.uuid4())
                temp_file_path = Path(temp_dir) / f"generated_doc_{unique_id}.txt"
                with open(temp_file_path, "w") as f:
                    f.write(f"Generated test document {unique_id}\n\n")
                    f.write(fake.paragraph(nb_sentences=5))
                file_path = temp_file_path
                return client.documents.upload_sync(file_path)

        return client.documents.upload_sync(file_path)

    @classmethod
    def upload_async(cls, client: "PaperlessClient", file_path: Path | None = None, **kwargs) -> str:
        """
        Upload a document asynchronously and return the task ID.

        Args:
            client: PaperlessClient instance
            file_path: Path to the file to upload (optional - will generate a text file if None)
            **kwargs: Additional metadata for the document

        Returns:
            Task ID for the upload
        """
        import tempfile
        import uuid

        # Generate a temp file if none provided
        temp_dir = None
        if file_path is None:
            temp_dir = tempfile.TemporaryDirectory()
            unique_id = str(uuid.uuid4())
            temp_file_path = Path(temp_dir.name) / f"generated_doc_{unique_id}.txt"
            with open(temp_file_path, "w") as f:
                f.write(f"Generated test document {unique_id}\n\n")
                f.write(fake.paragraph(nb_sentences=5))
            file_path = temp_file_path

        try:
            # Upload the document
            task_id = client.documents.upload_async(file_path, **kwargs)
            logger.debug(f"Started async upload of {file_path.name} with task ID {task_id}")
            return task_id
        finally:
            # Clean up temporary directory if we created one
            if temp_dir:
                temp_dir.cleanup()

    @classmethod
    def upload(cls, client: Any, file_path: Path | None = None, wait: bool = True, **kwargs) -> Document:
        """
        Legacy method for compatibility - use upload_sync instead.

        Args:
            client: PaperlessClient instance
            file_path: Path to the file to upload (optional - will generate a text file if None)
            wait: Whether to wait for the upload to complete
            **kwargs: Additional document attributes to set after upload

        Returns:
            The created Document instance if wait=True, otherwise a placeholder
        """
        logger.warning("DocumentFactory.upload() is deprecated. Use upload_sync() instead.")
        return cls.upload_sync(client, file_path, wait, **kwargs)

    added = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    archive_serial_number = factory.Faker("random_int", min=1, max=100000)
    archive_checksum = factory.Faker("sha256")
    archive_filename = factory.Faker("file_name")
    archived_file_name = factory.Faker("file_name")
    checksum = factory.Faker("sha256")
    content = factory.Faker("text")
    correspondent_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    created = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    created_date = factory.Maybe(factory.Faker("boolean"), factory.Faker("date"), None)
    custom_field_dicts = factory.List([{"field": fake.random_int(min=1, max=50), "value": fake.word()} for _ in range(3)])
    deleted_at = None
    document_type_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    filename = factory.Faker("file_name")
    is_shared_by_requester = factory.Faker("boolean")
    original_filename = factory.Faker("file_name")
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    page_count = factory.Faker("random_int", min=1, max=500)
    storage_path_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    storage_type = factory.Faker("random_element", elements=["pdf", "image", "text"])
    tag_ids = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    title = factory.Faker("sentence")
    user_can_change = factory.Faker("boolean")
    # notes is a list of DocumentNote instances
    notes = factory.LazyFunction(lambda: [DocumentNoteFactory.create() for _ in range(3)])

class DocumentTypeFactory(PydanticFactory[DocumentType]):
    _RELATIONSHIPS = {"owner"}

    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentType

    name = factory.Sequence(lambda n: f"DocType-{n}-{fake.word()}")
    slug = factory.LazyFunction(fake.slug)
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=-1, max=6)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=1000)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class TagFactory(PydanticFactory[Tag]):
    _RELATIONSHIPS = {"owner"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Tag

    name = factory.Sequence(lambda n: f"Tag-{n}-{fake.word()}")
    slug = factory.LazyFunction(fake.slug)
    colour = factory.Faker("hex_color")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=-1, max=6)
    is_insensitive = factory.Faker("boolean")
    is_inbox_tag = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class ProfileFactory(PydanticFactory[Profile]):
    _RELATIONSHIPS = {"social_accounts"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Profile

    email = factory.Faker("email")
    password = factory.Faker("password")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    auth_token = factory.LazyFunction(lambda: secrets.token_hex(20))
    social_accounts = factory.List([factory.Faker("url") for _ in range(3)])
    has_usable_password = factory.Faker("boolean")

class UserFactory(PydanticFactory[User]):
    _RELATIONSHIPS = {"groups", "user_permissions", "inherited_permissions"}

    class Meta: # type: ignore # pyright handles this wrong
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = factory.Faker("password")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    date_joined = factory.Faker("iso8601")
    is_staff = factory.Faker("boolean")
    is_active = factory.Faker("boolean")
    is_superuser = factory.Faker("boolean")
    groups = factory.List([factory.Faker("random_int", min=1, max=10) for _ in range(3)])
    user_permissions = factory.List([factory.Faker("word") for _ in range(5)])
    inherited_permissions = factory.List([factory.Faker("word") for _ in range(5)])

class StoragePathFactory(PydanticFactory[StoragePath]):
    _RELATIONSHIPS = {"owner"}

    class Meta: # type: ignore # pyright handles this wrong
        model = StoragePath

    name = factory.Sequence(lambda n: f"StoragePath-{n}-{fake.word()}")
    slug = factory.LazyFunction(fake.slug)
    path = factory.Faker("file_path")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=-1, max=6)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class SavedViewFactory(PydanticFactory[SavedView]):
    _RELATIONSHIPS = {"filter_rules", "owner", "display_fields"}

    class Meta: # type: ignore # pyright handles this wrong
        model = SavedView

    name = factory.Sequence(lambda n: f"SavedView-{n}-{fake.word()}")
    show_on_dashboard = factory.Faker("boolean")
    show_in_sidebar = factory.Faker("boolean")
    sort_field = factory.Faker("word")
    sort_reverse = factory.Faker("boolean")
    filter_rules = factory.List([factory.Dict({"rule_type": factory.Faker("random_int", min=1, max=3), "value": fake.word(), "saved_view": factory.Faker("random_int", min=1, max=100)}) for _ in range(3)])
    page_size = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=10, max=100), None)
    display_mode = None
    display_fields = factory.List([factory.Faker("word") for _ in range(5)])
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class ShareLinksFactory(PydanticFactory[ShareLinks]):
    _RELATIONSHIPS = {"document"}

    class Meta: # type: ignore # pyright handles this wrong
        model = ShareLinks

    expiration = factory.Maybe(factory.Faker("boolean"), factory.Faker("future_datetime"), None)
    slug = factory.Faker("slug")
    document = factory.Faker("random_int", min=1, max=1000)
    created = factory.LazyFunction(datetime.now)
    file_version = "original"

class TaskFactory(PydanticFactory[Task]):
    _RELATIONSHIPS = {"related_document"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Task

    task_id = factory.Faker("uuid4")
    task_file_name = factory.Faker("file_name")
    date_done = factory.Maybe(factory.Faker("boolean"), factory.Faker("iso8601"), None)
    type = factory.Maybe(factory.Faker("boolean"), factory.Faker("word"), None)
    status = factory.Faker("random_element", elements=["pending", "completed", "failed"])
    result = factory.Maybe(factory.Faker("boolean"), factory.Faker("sentence"), None)
    acknowledged = factory.Faker("boolean")
    related_document = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=1000), None)

class UISettingsFactory(PydanticFactory[UISettings]):
    _RELATIONSHIPS = {"user", "settings", "permissions"}

    class Meta: # type: ignore # pyright handles this wrong
        model = UISettings

    user = {
        "id": 3,
        "username": "Jess",
        "is_staff": True,
        "is_superuser": True,
        "groups": []
    },
    settings = {
        "update_checking": {
            "backend_setting": "default"
        },
        "trash_delay": 30,
        "app_title": None,
        "app_logo": None,
        "auditlog_enabled": True,
        "email_enabled": False
    }
    permissions = [
        "delete_logentry",
        "delete_paperlesstask",
        "delete_note",
        "add_group",
        "change_mailrule",
        "view_authenticator",
        "add_taskresult",
        "add_savedviewfilterrule",
        "change_chordcounter",
        "view_taskresult",
        "add_tag",
        "add_processedmail",
        "delete_group",
        "change_storagepath",
        "delete_socialapp",
        "view_group",
        "change_workflowactionwebhook",
        "add_workflowrun",
        "delete_savedviewfilterrule",
        "delete_chordcounter",
        "change_groupobjectpermission",
        "view_processedmail",
        "change_groupresult",
        "change_tokenproxy",
        "delete_contenttype",
        "change_workflowactionemail",
        "view_customfield",
        "view_emailaddress",
        "delete_token",
        "add_emailconfirmation",
        "change_workflowaction",
        "add_note",
        "delete_processedmail",
        "delete_emailconfirmation",
        "delete_socialtoken",
        "add_savedview",
        "view_socialapp",
        "delete_emailaddress",
        "view_paperlesstask",
        "delete_correspondent",
        "change_mailaccount",
        "add_uisettings",
        "view_customfieldinstance",
        "add_logentry",
        "delete_customfield",
        "change_emailconfirmation",
        "add_workflow",
        "view_savedview",
        "add_contenttype",
        "change_documenttype",
        "change_note",
        "change_workflowtrigger",
        "view_tag",
        "change_socialaccount",
        "change_tag",
        "view_workflowtrigger",
        "change_applicationconfiguration",
        "view_groupobjectpermission",
        "add_customfield",
        "add_socialaccount",
        "change_logentry",
        "delete_tokenproxy",
        "change_user",
        "delete_permission",
        "delete_storagepath",
        "view_mailrule",
        "view_workflowaction",
        "delete_taskresult",
        "change_emailaddress",
        "delete_groupresult",
        "add_sharelink",
        "view_permission",
        "delete_mailaccount",
        "view_userobjectpermission",
        "add_tokenproxy",
        "view_log",
        "delete_log",
        "change_userobjectpermission",
        "change_correspondent",
        "add_permission",
        "add_socialapp",
        "delete_workflow",
        "view_chordcounter",
        "view_workflowactionwebhook",
        "add_applicationconfiguration",
        "change_token",
        "delete_sharelink",
        "change_session",
        "delete_mailrule",
        "view_groupresult",
        "delete_session",
        "add_user",
        "view_tokenproxy",
        "add_workflowtrigger",
        "add_chordcounter",
        "delete_applicationconfiguration",
        "add_token",
        "add_paperlesstask",
        "view_logentry",
        "view_storagepath",
        "add_session",
        "delete_workflowaction",
        "view_user",
        "view_document",
        "view_workflow",
        "change_workflow",
        "delete_tag",
        "add_mailaccount",
        "view_socialaccount",
        "change_authenticator",
        "change_socialtoken",
        "view_logentry",
        "add_document",
        "delete_authenticator",
        "change_uisettings",
        "delete_document",
        "add_mailrule",
        "add_customfieldinstance",
        "add_workflowactionemail",
        "delete_groupobjectpermission",
        "change_permission",
        "delete_workflowtrigger",
        "change_savedviewfilterrule",
        "view_correspondent",
        "change_socialapp",
        "view_savedviewfilterrule",
        "delete_workflowrun",
        "view_contenttype",
        "delete_uisettings",
        "change_customfield",
        "view_workflowactionemail",
        "delete_workflowactionwebhook",
        "delete_workflowactionemail",
        "change_workflowrun",
        "view_session",
        "add_groupresult",
        "delete_logentry",
        "delete_socialaccount",
        "view_documenttype",
        "add_storagepath",
        "view_note",
        "add_workflowaction",
        "add_log",
        "view_sharelink",
        "view_workflowrun",
        "delete_userobjectpermission",
        "add_authenticator",
        "change_sharelink",
        "view_mailaccount",
        "view_applicationconfiguration",
        "change_log",
        "add_logentry",
        "change_taskresult",
        "add_groupobjectpermission",
        "view_uisettings",
        "add_userobjectpermission",
        "change_savedview",
        "change_paperlesstask",
        "delete_documenttype",
        "delete_savedview",
        "view_emailconfirmation",
        "change_logentry",
        "change_customfieldinstance",
        "add_workflowactionwebhook",
        "view_socialtoken",
        "change_group",
        "add_socialtoken",
        "change_contenttype",
        "change_document",
        "delete_user",
        "add_documenttype",
        "add_emailaddress",
        "delete_customfieldinstance",
        "add_correspondent",
        "view_token",
        "change_processedmail"
    ]

class MetadataElementFactory(PydanticFactory[MetadataElement]):
    _RELATIONSHIPS = set()

    class Meta: # type: ignore # pyright handles this wrong
        model = MetadataElement

    key = factory.Faker("word")
    value = factory.Faker("sentence")

class DocumentMetadataFactory(PydanticFactory[DocumentMetadata]):
    _RELATIONSHIPS = {"original_metadata", "archive_metadata"}

    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentMetadata

    original_checksum = factory.Faker("sha256")
    original_size = factory.Faker("random_int", min=1000, max=10000000)
    original_mime_type = factory.Faker("mime_type")
    media_filename = factory.Faker("file_name")
    has_archive_version = factory.Faker("boolean")
    original_metadata = factory.List([MetadataElementFactory.build() for _ in range(3)])
    archive_checksum = factory.Faker("sha256")
    archive_media_filename = factory.Faker("file_name")
    original_filename = factory.Faker("file_name")
    lang = factory.Faker("language_code")
    archive_size = factory.Faker("random_int", min=1000, max=10000000)
    archive_metadata = factory.List([MetadataElementFactory.build() for _ in range(3)])

class DocumentSuggestionsFactory(PydanticFactory[DocumentSuggestions]):
    _RELATIONSHIPS = {"correspondents", "tags", "document_types", "storage_paths", "dates"}

    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentSuggestions

    correspondents = factory.List([factory.Faker("random_int", min=1, max=100) for _ in range(3)])
    tags = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    document_types = factory.List([factory.Faker("random_int", min=1, max=100) for _ in range(3)])
    storage_paths = factory.List([factory.Faker("random_int", min=1, max=100) for _ in range(3)])
    dates = factory.List([factory.Faker("date_object") for _ in range(3)])

class DownloadedDocumentFactory(PydanticFactory[DownloadedDocument]):
    class Meta: # type: ignore # pyright handles this wrong
        model = DownloadedDocument

    mode = factory.Faker("random_element", elements=["download", "preview", "thumbnail"])
    original = factory.Faker("boolean")
    content = factory.LazyFunction(lambda: bytes(fake.binary(length=1024)))
    content_type = factory.Faker("mime_type")
    disposition_filename = factory.Faker("file_name")
    disposition_type = factory.Faker("random_element", elements=["inline", "attachment"])

class GroupFactory(PydanticFactory[Group]):
    _RELATIONSHIPS = {"permissions"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Group

    name = factory.Faker("word")
    permissions = factory.List([factory.Faker("word") for _ in range(5)])

class WorkflowTriggerFactory(PydanticFactory[WorkflowTrigger]):
    _RELATIONSHIPS = {
        "sources", "filter_has_tags", "filter_has_correspondent", "filter_has_document_type"
    }

    class Meta: # type: ignore # pyright handles this wrong
        model = WorkflowTrigger

    sources = factory.List([factory.Faker("word") for _ in range(3)])
    type = factory.Faker("random_int", min=1, max=10)
    filter_path = factory.Maybe(factory.Faker("boolean"), factory.Faker("file_path"), None)
    filter_filename = factory.Maybe(factory.Faker("boolean"), factory.Faker("file_name"), None)
    filter_mailrule = factory.Maybe(factory.Faker("boolean"), factory.Faker("word"), None)
    matching_algorithm = factory.Faker("random_int", min=-1, max=6)
    match = factory.Faker("word")
    is_insensitive = factory.Faker("boolean")
    filter_has_tags = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    filter_has_correspondent = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    filter_has_document_type = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)

class WorkflowActionFactory(PydanticFactory[WorkflowAction]):
    _RELATIONSHIPS = {
        "assign_tags", "assign_correspondent", "assign_document_type",
        "assign_storage_path", "assign_owner", "assign_view_users",
        "assign_view_groups"
    }

    class Meta: # type: ignore # pyright handles this wrong
        model = WorkflowAction

    type = factory.Faker("word")
    assign_title = factory.Maybe(factory.Faker("boolean"), factory.Faker("sentence"), None)
    assign_tags = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(3)])
    assign_correspondent = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    assign_document_type = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    assign_storage_path = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    assign_owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    assign_view_users = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(3)])
    assign_view_groups = factory.List([factory.Faker("random_int", min=1, max=10) for _ in range(3)])
    remove_all_tags = factory.Faker("boolean")
    remove_all_custom_fields = factory.Faker("boolean")

class WorkflowFactory(PydanticFactory[Workflow]):
    _RELATIONSHIPS = {"triggers", "actions"}

    class Meta: # type: ignore # pyright handles this wrong
        model = Workflow

    name = factory.Sequence(lambda n: f"Workflow-{n}-{fake.word()}")
    order = factory.Faker("random_int", min=1, max=100)
    enabled = factory.Faker("boolean")
    triggers = factory.List([factory.Dict({"type": fake.random_int(min=1, max=10), "match": fake.word()}) for _ in range(3)])
    actions = factory.List([factory.Dict({"type": fake.word(), "assign_tags": [fake.random_int(min=1, max=50)]}) for _ in range(3)])
