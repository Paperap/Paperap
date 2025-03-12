"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    models.py
        Project: paperap
        Created: 2025-03-07
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-07     By Jess Mann

"""
from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, override

import factory
from factory.base import StubObject
from faker import Faker
from typing_extensions import TypeVar

from paperap.models import (StandardModel, Correspondent, CustomField, Document,
                            DocumentNote, DocumentType, Group, Profile, SavedView,
                            ShareLinks, StoragePath, Tag, Task, UISettings,
                            User, Workflow, WorkflowAction, WorkflowTrigger)
if TYPE_CHECKING:
    from paperap.resources import BaseResource

fake = Faker()

_StandardModel = TypeVar("_StandardModel", bound="StandardModel", default="StandardModel")

class PydanticFactory(factory.Factory[_StandardModel], Generic[_StandardModel]):
    """Base factory for Pydantic models."""
    class Meta: # type: ignore # pyright handles this wrong
        abstract = True

    @classmethod
    def get_resource(cls) -> "BaseResource":
        """
        Get the resource for the model.

        Returns:
            The resource for the model specified in this factory's Meta.model
        """
        return cls._meta.model._meta.resource # type: ignore # model is always defined on subclasses
    
    @classmethod
    def create_api_data(cls, **kwargs : Any) -> dict[str, Any]:
        """
        Create a model, then transform its fields into sample API data.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the model creation.

        Returns:
            dict: A dictionary of the model's fields.
        """
        _instance = cls.create(**kwargs)
        return cls.get_resource().transform_data_output(_instance, exclude_unset = False)

    @classmethod
    def to_dict(cls, **kwargs) -> dict[str, Any]:
        """
        Create a model, and return a dictionary of the model's fields.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the model creation.

        Returns:
            dict: A dictionary of the model's fields.
        """
        _instance = cls.create(**kwargs)
        return _instance.to_dict()

class CorrespondentFactory(PydanticFactory[Correspondent]):
    class Meta: # type: ignore # pyright handles this wrong
        model = Correspondent    

    slug = factory.LazyFunction(fake.slug)
    name = factory.Faker("name")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=100)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class CustomFieldFactory(PydanticFactory[CustomField]):
    class Meta: # type: ignore # pyright handles this wrong
        model = CustomField

    name = factory.Faker("word")
    data_type = factory.Faker("word")
    extra_data = factory.Dict({"key": fake.word(), "value": fake.word()})
    document_count = factory.Faker("random_int", min=0, max=100)

class DocumentNoteFactory(PydanticFactory[DocumentNote]):
    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentNote

    note = factory.Faker("sentence")
    created = factory.LazyFunction(datetime.now)
    deleted_at = None
    restored_at = None
    transaction_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    document = factory.Faker("random_int", min=1, max=1000)
    user = factory.Faker("random_int", min=1, max=1000)

class DocumentFactory(PydanticFactory[Document]):
    class Meta: # type: ignore # pyright handles this wrong
        model = Document

    added = factory.LazyFunction(datetime.now)
    archive_serial_number = factory.Faker("random_int", min=1, max=100000)
    archived_file_name = factory.Faker("file_name")
    content = factory.Faker("text")
    correspondent = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    created = factory.LazyFunction(datetime.now)
    created_date = factory.Maybe(factory.Faker("boolean"), factory.Faker("date"), None)
    updated = factory.LazyFunction(datetime.now)
    deleted_at = None
    document_type = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    is_shared_by_requester = factory.Faker("boolean")
    original_file_name = factory.Faker("file_name")
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    page_count = factory.Faker("random_int", min=1, max=500)
    storage_path = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    tag_ids = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    title = factory.Faker("sentence")
    user_can_change = factory.Faker("boolean")
    # notes is a list of DocumentNote instances
    notes = factory.LazyFunction(lambda: [DocumentNoteFactory.create() for _ in range(3)])

class DocumentTypeFactory(PydanticFactory[DocumentType]):
    class Meta: # type: ignore # pyright handles this wrong
        model = DocumentType

    name = factory.Faker("word")
    slug = factory.LazyFunction(fake.slug)
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=1000)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class TagFactory(PydanticFactory[Tag]):
    class Meta: # type: ignore # pyright handles this wrong
        model = Tag

    name = factory.Faker("word")
    slug = factory.LazyFunction(fake.slug)
    colour = factory.Faker("hex_color")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    is_inbox_tag = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class ProfileFactory(PydanticFactory[Profile]):
    class Meta: # type: ignore # pyright handles this wrong
        model = Profile

    email = factory.Faker("email")
    password = factory.Faker("password")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    auth_token = factory.Faker("uuid4")
    social_accounts = factory.List([factory.Faker("url") for _ in range(3)])
    has_usable_password = factory.Faker("boolean")

class UserFactory(PydanticFactory[User]):
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
    class Meta: # type: ignore # pyright handles this wrong
        model = StoragePath

    name = factory.Faker("word")
    slug = factory.LazyFunction(fake.slug)
    path = factory.Faker("file_path")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class SavedViewFactory(PydanticFactory[SavedView]):
    class Meta: # type: ignore # pyright handles this wrong
        model = SavedView

    name = factory.Faker("sentence", nb_words=3)
    show_on_dashboard = factory.Faker("boolean")
    show_in_sidebar = factory.Faker("boolean")
    sort_field = factory.Faker("word")
    sort_reverse = factory.Faker("boolean")
    filter_rules = factory.List([{"key": fake.word(), "value": fake.word()} for _ in range(3)])
    page_size = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=10, max=100), None)
    display_mode = factory.Faker("word")
    display_fields = factory.List([factory.Faker("word") for _ in range(5)])
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class ShareLinksFactory(PydanticFactory[ShareLinks]):
    class Meta: # type: ignore # pyright handles this wrong
        model = ShareLinks

    expiration = factory.Maybe(factory.Faker("boolean"), factory.Faker("future_datetime"), None)
    slug = factory.Faker("slug")
    document = factory.Faker("random_int", min=1, max=1000)
    created = factory.LazyFunction(datetime.now)
    file_version = factory.Faker("word")

class TaskFactory(PydanticFactory[Task]):
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
    class Meta: # type: ignore # pyright handles this wrong
        model = UISettings

    user = factory.Dict({"theme": "dark", "language": "en"})
    settings = factory.Dict({"dashboard_layout": "grid", "notification_settings": {"email": True}})
    permissions = factory.List([factory.Faker("word") for _ in range(5)])

class GroupFactory(PydanticFactory[Group]):
    class Meta: # type: ignore # pyright handles this wrong
        model = Group

    name = factory.Faker("word")
    permissions = factory.List([factory.Faker("word") for _ in range(5)])

class WorkflowTriggerFactory(PydanticFactory[WorkflowTrigger]):
    class Meta: # type: ignore # pyright handles this wrong
        model = WorkflowTrigger

    sources = factory.List([factory.Faker("word") for _ in range(3)])
    type = factory.Faker("random_int", min=1, max=10)
    filter_path = factory.Maybe(factory.Faker("boolean"), factory.Faker("file_path"), None)
    filter_filename = factory.Maybe(factory.Faker("boolean"), factory.Faker("file_name"), None)
    filter_mailrule = factory.Maybe(factory.Faker("boolean"), factory.Faker("word"), None)
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    match = factory.Faker("word")
    is_insensitive = factory.Faker("boolean")
    filter_has_tags = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    filter_has_correspondent = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    filter_has_document_type = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)

class WorkflowActionFactory(PydanticFactory[WorkflowAction]):
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
    class Meta: # type: ignore # pyright handles this wrong
        model = Workflow

    name = factory.Faker("sentence", nb_words=3)
    order = factory.Faker("random_int", min=1, max=100)
    enabled = factory.Faker("boolean")
    triggers = factory.List([factory.Dict({"type": fake.random_int(min=1, max=10), "match": fake.word()}) for _ in range(3)])
    actions = factory.List([factory.Dict({"type": fake.word(), "assign_tags": [fake.random_int(min=1, max=50)]}) for _ in range(3)])
