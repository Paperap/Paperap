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

from paperap.models.abstract import PaperlessModel, QuerySet, Parser
from paperap.models.correspondent import Correspondent
from paperap.models.custom_field import CustomField
from paperap.models.document import Document
from paperap.models.document_type import DocumentType
from paperap.models.profile import Profile
from paperap.models.saved_view import SavedView
from paperap.models.share_links import ShareLinks
from paperap.models.storage_path import StoragePath
from paperap.models.tag import Tag
from paperap.models.task import Task
from paperap.models.ui_settings import UISettings
from paperap.models.user import Group, User
from paperap.models.workflow import Workflow, WorkflowAction, WorkflowTrigger

__all__ = [
    "PaperlessModel",
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
]
