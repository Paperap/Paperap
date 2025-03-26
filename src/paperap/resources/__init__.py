

from paperap.resources.base import BaseResource, StandardResource
from paperap.resources.correspondents import CorrespondentResource
from paperap.resources.custom_fields import CustomFieldResource
from paperap.resources.document_download import DownloadedDocumentResource
from paperap.resources.document_metadata import DocumentMetadataResource
from paperap.resources.document_suggestions import DocumentSuggestionsResource
from paperap.resources.document_types import DocumentTypeResource
from paperap.resources.document_notes import DocumentNoteResource
from paperap.resources.documents import DocumentResource
from paperap.resources.profile import ProfileResource
from paperap.resources.saved_views import SavedViewResource
from paperap.resources.share_links import ShareLinksResource
from paperap.resources.storage_paths import StoragePathResource
from paperap.resources.tags import TagResource
from paperap.resources.tasks import TaskResource
from paperap.resources.ui_settings import UISettingsResource
from paperap.resources.users import GroupResource, UserResource
from paperap.resources.workflows import WorkflowActionResource, WorkflowResource, WorkflowTriggerResource

__all__ = [
    "DocumentNoteResource",
    "DocumentResource",
    "CorrespondentResource",
    "TagResource",
    "DocumentTypeResource",
    "DocumentMetadataResource",
    "DocumentSuggestionsResource",
    "DownloadedDocumentResource",
    "ProfileResource",
    "ShareLinksResource",
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
