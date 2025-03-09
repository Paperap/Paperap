"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    models.py
        Project: paperap
        Created: 2025-03-07
        Version: 0.0.4
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-07     By Jess Mann

"""
from typing import Any, Generic
from typing_extensions import TypeVar
from abc import ABC
import factory
from faker import Faker
from datetime import datetime, timezone
from paperap.models import *

fake = Faker()

_PaperlessModel = TypeVar("_PaperlessModel", bound=PaperlessModel, default=PaperlessModel, covariant=True)

class PydanticFactory(factory.Factory):
    """Base factory for Pydantic models."""
    class Meta(factory.Factory.Meta, Generic[_PaperlessModel]):
        model : type[_PaperlessModel]

class CorrespondentFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Correspondent

    slug = factory.LazyFunction(lambda: fake.slug())
    name = factory.Faker("name")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=100)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")

class CustomFieldFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = CustomField

    name = factory.Faker("word")
    data_type = factory.Faker("word")
    extra_data = factory.Dict({"key": fake.word(), "value": fake.word()})
    document_count = factory.Faker("random_int", min=0, max=100)

class DocumentNoteFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = DocumentNote

    note = factory.Faker("sentence")
    created = factory.LazyFunction(datetime.now)
    deleted_at = None
    restored_at = None
    transaction_id = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    document = factory.Faker("random_int", min=1, max=1000)
    user = factory.Faker("random_int", min=1, max=1000)

class DocumentFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
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
    tags = factory.List([factory.Faker("random_int", min=1, max=50) for _ in range(5)])
    title = factory.Faker("sentence")
    user_can_change = factory.Faker("boolean")
    # notes is a list of DocumentNote instances
    notes = factory.LazyFunction(lambda: [DocumentNoteFactory() for _ in range(3)])

class DocumentTypeFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = DocumentType

    name = factory.Faker("word")
    slug = factory.LazyFunction(lambda: fake.slug())
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=1000)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")


class TagFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Tag

    name = factory.Faker("word")
    slug = factory.LazyFunction(lambda: fake.slug())
    colour = factory.Faker("hex_color")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    is_inbox_tag = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")


class ProfileFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Profile

    email = factory.Faker("email")
    password = factory.Faker("password")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    auth_token = factory.Faker("uuid4")
    social_accounts = factory.List([factory.Faker("url") for _ in range(3)])
    has_usable_password = factory.Faker("boolean")


class UserFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
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


class StoragePathFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = StoragePath

    name = factory.Faker("word")
    slug = factory.LazyFunction(lambda: fake.slug())
    path = factory.Faker("file_path")
    match = factory.Faker("word")
    matching_algorithm = factory.Faker("random_int", min=0, max=3)
    is_insensitive = factory.Faker("boolean")
    document_count = factory.Faker("random_int", min=0, max=500)
    owner = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=100), None)
    user_can_change = factory.Faker("boolean")


class SavedViewFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
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

class ShareLinksFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = ShareLinks

    expiration = factory.Maybe(factory.Faker("boolean"), factory.Faker("future_datetime"), None)
    slug = factory.Faker("slug")
    document = factory.Faker("random_int", min=1, max=1000)
    created = factory.LazyFunction(datetime.now)
    file_version = factory.Faker("word")

class TaskFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Task

    task_id = factory.Faker("uuid4")
    task_file_name = factory.Faker("file_name")
    date_done = factory.Maybe(factory.Faker("boolean"), factory.Faker("iso8601"), None)
    type = factory.Maybe(factory.Faker("boolean"), factory.Faker("word"), None)
    status = factory.Faker("random_element", elements=["pending", "completed", "failed"])
    result = factory.Maybe(factory.Faker("boolean"), factory.Faker("sentence"), None)
    acknowledged = factory.Faker("boolean")
    related_document = factory.Maybe(factory.Faker("boolean"), factory.Faker("random_int", min=1, max=1000), None)

class UISettingsFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = UISettings

    user = factory.Dict({"theme": "dark", "language": "en"})
    settings = factory.Dict({"dashboard_layout": "grid", "notification_settings": {"email": True}})
    permissions = factory.List([factory.Faker("word") for _ in range(5)])

class GroupFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Group

    name = factory.Faker("word")
    permissions = factory.List([factory.Faker("word") for _ in range(5)])

class WorkflowTriggerFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
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

class WorkflowActionFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
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

class WorkflowFactory(PydanticFactory):
    class Meta(PydanticFactory.Meta, Generic[_PaperlessModel]):
        model = Workflow

    name = factory.Faker("sentence", nb_words=3)
    order = factory.Faker("random_int", min=1, max=100)
    enabled = factory.Faker("boolean")
    triggers = factory.List([factory.Dict({"type": fake.random_int(min=1, max=10), "match": fake.word()}) for _ in range(3)])
    actions = factory.List([factory.Dict({"type": fake.word(), "assign_tags": [fake.random_int(min=1, max=50)]}) for _ in range(3)])
