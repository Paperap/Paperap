"""
Document metadata and filtering parameters for Paperless-NgX documents.

This module defines the supported filtering parameters for document queries
in the Paperless-NgX API. These parameters can be used with the DocumentQuerySet
to filter documents based on various criteria.
"""

SUPPORTED_FILTERING_PARAMS = {
    # Document ID filters
    "id__in",  # Filter by multiple document IDs
    "id",  # Filter by exact document ID
    # Title filters (case-insensitive)
    "title__istartswith",  # Title starts with the given text
    "title__iendswith",  # Title ends with the given text
    "title__icontains",  # Title contains the given text
    "title__iexact",  # Title exactly matches the given text
    # Content filters (case-insensitive)
    "content__istartswith",  # Content starts with the given text
    "content__iendswith",  # Content ends with the given text
    "content__icontains",  # Content contains the given text
    "content__iexact",  # Content exactly matches the given text
    "content__contains",  # Content contains the given text (case-sensitive)
    # Archive serial number filters
    "archive_serial_number",  # Exact match on archive serial number
    "archive_serial_number__gt",  # Archive serial number greater than
    "archive_serial_number__gte",  # Archive serial number greater than or equal
    "archive_serial_number__lt",  # Archive serial number less than
    "archive_serial_number__lte",  # Archive serial number less than or equal
    "archive_serial_number__isnull",  # Archive serial number is null or not
    # Correspondent filters
    "correspondent__isnull",  # Correspondent is null or not
    "correspondent__id__in",  # Correspondent ID is in the given list
    "correspondent__id",  # Correspondent has the given ID
    "correspondent__name__istartswith",  # Correspondent name starts with
    "correspondent__name__iendswith",  # Correspondent name ends with
    "correspondent__name__icontains",  # Correspondent name contains
    "correspondent__name__iexact",  # Correspondent name exactly matches
    "correspondent__slug__iexact",  # Correspondent slug exactly matches
    "correspondent__id__none",  # Documents with no correspondent
    # Created date filters
    "created__year",  # Created in the given year
    "created__month",  # Created in the given month
    "created__day",  # Created on the given day
    "created__date__gt",  # Created after the given date
    "created__gt",  # Created after the given datetime
    "created__date__lt",  # Created before the given date
    "created__lt",  # Created before the given datetime
    # Added date filters
    "added__year",  # Added in the given year
    "added__month",  # Added in the given month
    "added__day",  # Added on the given day
    "added__date__gt",  # Added after the given date
    "added__gt",  # Added after the given datetime
    "added__date__lt",  # Added before the given date
    "added__lt",  # Added before the given datetime
    # Original filename filters
    "original_filename__istartswith",  # Original filename starts with
    "original_filename__iendswith",  # Original filename ends with
    "original_filename__icontains",  # Original filename contains
    "original_filename__iexact",  # Original filename exactly matches
    # Checksum filters
    "checksum__istartswith",  # Checksum starts with
    "checksum__iendswith",  # Checksum ends with
    "checksum__icontains",  # Checksum contains
    "checksum__iexact",  # Checksum exactly matches
    # Tag filters
    "tags__id__in",  # Tag ID is in the given list
    "tags__id",  # Tag has the given ID
    "tags__name__istartswith",  # Tag name starts with
    "tags__name__iendswith",  # Tag name ends with
    "tags__name__icontains",  # Tag name contains
    "tags__name__iexact",  # Tag name exactly matches
    "tags__id__all",  # Document has all the given tag IDs
    "tags__id__none",  # Document has none of the given tag IDs
    "is_tagged",  # Document has at least one tag
    # Document type filters
    "document_type__isnull",  # Document type is null or not
    "document_type__id__in",  # Document type ID is in the given list
    "document_type__id",  # Document type has the given ID
    "document_type__name__istartswith",  # Document type name starts with
    "document_type__name__iendswith",  # Document type name ends with
    "document_type__name__icontains",  # Document type name contains
    "document_type__name__iexact",  # Document type name exactly matches
    "document_type__id__none",  # Documents with no document type
    # Storage path filters
    "storage_path__isnull",  # Storage path is null or not
    "storage_path__id__in",  # Storage path ID is in the given list
    "storage_path__id",  # Storage path has the given ID
    "storage_path__name__istartswith",  # Storage path name starts with
    "storage_path__name__iendswith",  # Storage path name ends with
    "storage_path__name__icontains",  # Storage path name contains
    "storage_path__name__iexact",  # Storage path name exactly matches
    "storage_path__id__none",  # Documents with no storage path
    # Owner filters
    "owner__isnull",  # Owner is null or not
    "owner__id__in",  # Owner ID is in the given list
    "owner__id",  # Owner has the given ID
    "owner__id__none",  # Documents with no owner
    # Special filters
    "is_in_inbox",  # Document is in the inbox
    "title_content",  # Search in both title and content
    # Custom fields filters
    "custom_fields__icontains",  # Custom field contains the given text
    "custom_fields__id__all",  # Document has all the given custom field IDs
    "custom_fields__id__none",  # Document has none of the given custom field IDs
    "custom_fields__id__in",  # Custom field ID is in the given list
    "custom_field_query",  # Complex custom field query
    "has_custom_fields",  # Document has at least one custom field
    # Sharing filters
    "shared_by__id",  # Document shared by user with given ID
    "shared_by__id__in",  # Document shared by users with IDs in the given list
}
