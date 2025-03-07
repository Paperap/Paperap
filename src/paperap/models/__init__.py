"""




----------------------------------------------------------------------------

   METADATA:

       File:    __init__.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from paperap.models.abstract import PaperlessModel, StandardModel, QuerySet, StandardQuerySet, Parser
from paperap.models.correspondent import Correspondent, CorrespondentQuerySet
from paperap.models.custom_field import CustomField, CustomFieldQuerySet
from paperap.models.document import Document, DocumentQuerySet
from paperap.models.document_type import DocumentType, DocumentTypeQuerySet
from paperap.models.profile import Profile, ProfileQuerySet
from paperap.models.saved_view import SavedView, SavedViewQuerySet
from paperap.models.share_links import ShareLinks, ShareLinksQuerySet
from paperap.models.storage_path import StoragePath, StoragePathQuerySet
from paperap.models.tag import Tag, TagQuerySet
from paperap.models.task import Task, TaskQuerySet
from paperap.models.ui_settings import UISettings, UISettingsQuerySet
from paperap.models.user import Group, User, UserQuerySet, GroupQuerySet
from paperap.models.workflow import (
    Workflow,
    WorkflowAction,
    WorkflowTrigger,
    WorkflowQuerySet,
    WorkflowActionQuerySet,
    WorkflowTriggerQuerySet,
)

__all__ = [
    "PaperlessModel",
    "StandardModel",
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
    "QuerySet",
    "StandardQuerySet",
    "Parser",
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
