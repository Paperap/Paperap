"""
----------------------------------------------------------------------------

   METADATA:

       File:    __init__.py
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

from paperap.models.abstract import BaseModel, BaseQuerySet, StandardModel, StandardQuerySet
from paperap.models.correspondent import Correspondent, CorrespondentQuerySet
from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.models.document import (
    CustomFieldValues,
    Document,
    DocumentMetadata,
    DocumentMetadataQuerySet,
    DocumentNote,
    DocumentNoteQuerySet,
    DocumentQuerySet,
    DocumentSuggestions,
    DocumentSuggestionsQuerySet,
    DownloadedDocument,
    DownloadedDocumentQuerySet,
    MetadataElement,
)
from paperap.models.document_type import DocumentType, DocumentTypeQuerySet
from paperap.models.profile import Profile, ProfileQuerySet
from paperap.models.saved_view import SavedView, SavedViewQuerySet
from paperap.models.share_links import ShareLinks, ShareLinksQuerySet
from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.models.tag import Tag, TagQuerySet
from paperap.models.task import Task, TaskQuerySet
from paperap.models.ui_settings import UISettings, UISettingsQuerySet
from paperap.models.user import Group, GroupQuerySet, User, UserQuerySet
from paperap.models.workflow import (
    Workflow,
    WorkflowAction,
    WorkflowActionQuerySet,
    WorkflowQuerySet,
    WorkflowRun,
    WorkflowTrigger,
    WorkflowTriggerQuerySet,
)

__all__ = [
    "BaseModel",
    "StandardModel",
    "DocumentNote",
    "Document",
    "Correspondent",
    "Tag",
    "DocumentType",
    "StoragePath",
    "CustomField",
    "User",
    "Group",
    "Task",
    "SavedView",
    "UISettings",
    "Workflow",
    "WorkflowTrigger",
    "WorkflowAction",
    "Profile",
    "ShareLinks",
    "BaseQuerySet",
    "StandardQuerySet",
    "DocumentQuerySet",
    "CorrespondentQuerySet",
    "TagQuerySet",
    "DocumentTypeQuerySet",
    "StoragePathQuerySet",
    "CustomFieldQuerySet",
    "UserQuerySet",
    "GroupQuerySet",
    "TaskQuerySet",
    "SavedViewQuerySet",
    "UISettingsQuerySet",
    "WorkflowQuerySet",
    "WorkflowTriggerQuerySet",
    "WorkflowActionQuerySet",
    "ProfileQuerySet",
    "ShareLinksQuerySet",
]
