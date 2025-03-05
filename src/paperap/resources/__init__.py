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

from __future__ import annotations

from paperap.resources.base import PaperlessResource, StandardResource
from paperap.resources.correspondents import CorrespondentResource
from paperap.resources.custom_fields import CustomFieldResource
from paperap.resources.document_types import DocumentTypeResource
from paperap.resources.documents import DocumentResource
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
    "UserResource",
    "GroupResource",
    "TaskResource",
    "SavedViewResource",
    "UISettingsResource",
    "WorkflowResource",
    "WorkflowTriggerResource",
    "WorkflowActionResource",
]
