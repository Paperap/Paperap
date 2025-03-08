"""




----------------------------------------------------------------------------

   METADATA:

       File:    const.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from string import Template
from enum import StrEnum
from typing import TypedDict

from yarl import URL


class URLS:
    index: Template = Template("/api/")
    token: Template = Template("/api/token/")
    list: Template = Template("/api/${resource}/")
    detail: Template = Template("/api/${resource}/${pk}/")
    create: Template = Template("/api/${resource}/")
    update: Template = Template("/api/${resource}/${pk}/")
    delete: Template = Template("/api/${resource}/${pk}/")


class Endpoints(TypedDict, total=False):
    list: Template
    detail: Template
    create: Template
    update: Template
    delete: Template


class FilteringStrategies(StrEnum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    ALLOW_ALL = "allow_all"
    ALLOW_NONE = "allow_none"


class ModelStatus(StrEnum):
    INITIALIZING = "initializing"
    UPDATING = "updating"
    SAVING = "saving"
    READY = "ready"
    ERROR = "error"


# API endpoint paths
API_PATH: dict[str, str] = {
    # Document endpoints
    "documents": "/api/documents/",
    "documents_download": "/api/documents/${pk}/download/",
    "documents_meta": "/api/documents/${pk}/metadata/",
    "documents_next_asn": "/api/documents/next_asn/",
    "documents_notes": "/api/documents/${pk}/notes/",
    "documents_preview": "/api/documents/${pk}/preview/",
    "documents_thumbnail": "/api/documents/${pk}/thumb/",
    "documents_post": "/api/documents/post_document/",
    "documents_single": "/api/documents/${pk}/",
    "documents_suggestions": "/api/documents/${pk}/suggestions/",
}
