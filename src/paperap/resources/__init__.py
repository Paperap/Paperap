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
*        Project: resources                                                                                            *
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

from paperap.resources.base import PaperlessResource
from paperap.resources.correspondents import CorrespondentResource
from paperap.resources.custom_fields import CustomFieldResource
from paperap.resources.document_types import DocumentTypeResource
from paperap.resources.documents import DocumentResource
from paperap.resources.logs import LogResource
from paperap.resources.mail_accounts import MailAccountsResource
from paperap.resources.mail_rules import MailRulesResource
from paperap.resources.search import SearchResource
from paperap.resources.share_links import ShareLinksResource
from paperap.resources.profile import ProfileResource
from paperap.resources.saved_views import SavedViewResource
from paperap.resources.storage_paths import StoragePathResource
from paperap.resources.tags import TagResource
from paperap.resources.tasks import TaskResource
from paperap.resources.ui_settings import UISettingsResource
from paperap.resources.users import GroupResource, UserResource
from paperap.resources.workflows import WorkflowActionResource, WorkflowResource, WorkflowTriggerResource

__all__ = [
    "DocumentResource",
    "CorrespondentResource",
    "TagResource",
    "DocumentTypeResource",
    "StoragePathResource",
    "CustomFieldResource",
    "LogResource",
    "UserResource",
    "GroupResource",
    "TaskResource",
    "SavedViewResource",
    "UISettingsResource",
    "WorkflowResource",
    "WorkflowTriggerResource",
    "WorkflowActionResource",
]
