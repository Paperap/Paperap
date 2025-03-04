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
from paperwrap.resources.base import PaperlessResource
from paperwrap.resources.correspondents import CorrespondentResource
from paperwrap.resources.custom_fields import CustomFieldResource
from paperwrap.resources.document_types import DocumentTypeResource
from paperwrap.resources.documents import DocumentResource
from paperwrap.resources.logs import LogResource
from paperwrap.resources.mail_accounts import MailAccountsResource
from paperwrap.resources.mail_rules import MailRulesResource
from paperwrap.resources.search import SearchResource
from paperwrap.resources.share_links import ShareLinksResource
from paperwrap.resources.profile import ProfileResource
from paperwrap.resources.saved_views import SavedViewResource
from paperwrap.resources.storage_paths import StoragePathResource
from paperwrap.resources.tags import TagResource
from paperwrap.resources.tasks import TaskResource
from paperwrap.resources.ui_settings import UISettingsResource
from paperwrap.resources.users import GroupResource, UserResource
from paperwrap.resources.workflows import (WorkflowActionResource,
                                               WorkflowResource,
                                               WorkflowTriggerResource)

__all__ = [
    "DocumentResource", "CorrespondentResource", "TagResource", 
    "DocumentTypeResource", "StoragePathResource", "CustomFieldResource",
    "LogResource", "UserResource", "GroupResource", "TaskResource", 
    "SavedViewResource", "UISettingsResource", "WorkflowResource",
    "WorkflowTriggerResource", "WorkflowActionResource",
]
