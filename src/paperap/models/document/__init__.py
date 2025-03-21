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

from paperap.models.document.download import DownloadedDocument, DownloadedDocumentQuerySet
from paperap.models.document.metadata import DocumentMetadata, DocumentMetadataQuerySet, MetadataElement
from paperap.models.document.model import CustomFieldValues, Document, DocumentNote
from paperap.models.document.queryset import DocumentNoteQuerySet, DocumentQuerySet
from paperap.models.document.suggestions import DocumentSuggestions, DocumentSuggestionsQuerySet
