"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    __init__.py                                                                                          *
*        Project: models                                                                                               *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from paperap.models.queryset import QuerySet
from paperap.models.base import PaperlessModel
from paperap.models.correspondent import Correspondent
from paperap.models.custom_field import CustomField
from paperap.models.document import Document
from paperap.models.document_type import DocumentType
from paperap.models.log import Log
from paperap.models.saved_view import SavedView
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
    "Log",
    "User",
    "Group",
    "Task",
    "SavedView",
    "UISettings",
    "Workflow",
    "WorkflowTrigger",
    "WorkflowAction",
]
