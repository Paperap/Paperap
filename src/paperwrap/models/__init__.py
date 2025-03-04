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

from paperwrap.models.queryset import QuerySet
from paperwrap.models.base import PaperlessModel
from paperwrap.models.correspondent import Correspondent
from paperwrap.models.custom_field import CustomField
from paperwrap.models.document import Document
from paperwrap.models.document_type import DocumentType
from paperwrap.models.log import Log
from paperwrap.models.saved_view import SavedView
from paperwrap.models.storage_path import StoragePath
from paperwrap.models.tag import Tag
from paperwrap.models.task import Task
from paperwrap.models.ui_settings import UISettings
from paperwrap.models.user import Group, User
from paperwrap.models.workflow import Workflow, WorkflowAction, WorkflowTrigger

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
