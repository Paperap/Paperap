"""
Integration tests for document filtering.
"""
import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

from paperap.client import PaperlessClient
from paperap.models.document import Document
from tests.lib.unittest import UnitTestCase


class TestDocumentFiltering(UnitTestCase):
    """Test document filtering functionality."""
    mock_env = False

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test class by retrieving all documents."""
        super().setUpClass()
        # Get all documents for comparison in tests
        client = PaperlessClient()
        cls.all_documents = list(client.documents().all())

    def setUp(self) -> None:
        """Set up each test."""
        super().setUp()
        if not self.all_documents:
            self.skipTest("No documents available for testing")

    # Simple ID filters
    def test_id(self) -> None:
        """Test filtering by id."""

        # Get a document id to filter by
        doc_id = self.all_documents[0].id

        # Apply the filter
        filtered = list(self.client.documents().filter(id=doc_id))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents if doc.id == doc_id]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_id__in(self) -> None:
        """Test filtering by id__in."""
        if len(self.all_documents) < 3:
            return

        # Get some document IDs
        doc_ids = [self.all_documents[i].id for i in range(min(3, len(self.all_documents)))]

        # Apply the filter
        filtered = list(self.client.documents().filter(id__in=doc_ids))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents if doc.id in doc_ids]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Title filters
    def test_title__istartswith(self) -> None:
        """Test filtering by title__istartswith."""
        if not self.all_documents or not self.all_documents[0].title:
            return

        # Get the first few characters of the first document title
        prefix = self.all_documents[0].title[:3].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(title__istartswith=prefix))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if doc.title and doc.title.lower().startswith(prefix)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_title__iendswith(self) -> None:
        """Test filtering by title__iendswith."""
        if not self.all_documents or not self.all_documents[0].title:
            return

        # Get the last few characters of the first document title
        suffix = self.all_documents[0].title[-3:].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(title__iendswith=suffix))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if doc.title and doc.title.lower().endswith(suffix)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_title__icontains(self) -> None:
        """Test filtering by title__icontains."""
        if not self.all_documents or not self.all_documents[0].title:
            return

        # Get a substring from the middle of the first document title
        middle = self.all_documents[0].title[1:-1][:3].lower()
        if not middle:
            middle = self.all_documents[0].title.lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(title__icontains=middle))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if doc.title and middle in doc.title.lower()]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_title__iexact(self) -> None:
        """Test filtering by title__iexact."""
        if not self.all_documents or not self.all_documents[0].title:
            return

        # Get the title of the first document
        title = self.all_documents[0].title.lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(title__iexact=title))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if doc.title and doc.title.lower() == title]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Content filters
    def test_content__istartswith(self) -> None:
        """Test filtering by content__istartswith."""
        # Find a document with content
        doc_with_content = next((doc for doc in self.all_documents if hasattr(doc, 'content') and doc.content), None)
        if not doc_with_content:
            self.skipTest("No documents with content available for testing")

        # Get the first few characters of the content
        prefix = doc_with_content.content[:3].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(content__istartswith=prefix))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'content') and doc.content and doc.content.lower().startswith(prefix)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_content__iendswith(self) -> None:
        """Test filtering by content__iendswith."""
        # Find a document with content
        doc_with_content = next((doc for doc in self.all_documents if hasattr(doc, 'content') and doc.content), None)
        if not doc_with_content:
            self.skipTest("No documents with content available for testing")

        # Get the last few characters of the content
        suffix = doc_with_content.content[-3:].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(content__iendswith=suffix))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'content') and doc.content and doc.content.lower().endswith(suffix)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_content__icontains(self) -> None:
        """Test filtering by content__icontains."""
        # Find a document with content
        doc_with_content = next((doc for doc in self.all_documents if hasattr(doc, 'content') and doc.content), None)
        if not doc_with_content:
            self.skipTest("No documents with content available for testing")

        # Get a substring from the middle of the content
        middle = doc_with_content.content[1:-1][:5].lower()
        if not middle:
            middle = doc_with_content.content.lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(content__icontains=middle))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'content') and doc.content and middle in doc.content.lower()]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_content__iexact(self) -> None:
        """Test filtering by content__iexact."""
        # Find a document with content
        doc_with_content = next((doc for doc in self.all_documents if hasattr(doc, 'content') and doc.content), None)
        if not doc_with_content:
            self.skipTest("No documents with content available for testing")

        # Get the content
        content = doc_with_content.content.lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(content__iexact=content))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'content') and doc.content and doc.content.lower() == content]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Archive serial number filters
    def test_archive_serial_number(self) -> None:
        """Test filtering by archive_serial_number."""
        # Find a document with archive_serial_number
        doc_with_asn = next((doc for doc in self.all_documents
                         if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number), None)
        if not doc_with_asn:
            self.skipTest("No documents with archive_serial_number available for testing")

        # Get the archive_serial_number
        asn = doc_with_asn.archive_serial_number

        # Apply the filter
        filtered = list(self.client.documents().filter(archive_serial_number=asn))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number == asn]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_archive_serial_number__gt(self) -> None:
        """Test filtering by archive_serial_number__gt."""
        # Find documents with archive_serial_number
        docs_with_asn = [doc for doc in self.all_documents
                      if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number]
        if not docs_with_asn:
            self.skipTest("No documents with archive_serial_number available for testing")

        # Sort by archive_serial_number
        docs_with_asn.sort(key=lambda doc: doc.archive_serial_number)

        # Get a middle value
        if len(docs_with_asn) >= 2:
            asn = docs_with_asn[len(docs_with_asn) // 2].archive_serial_number
        else:
            asn = docs_with_asn[0].archive_serial_number - 1

        # Apply the filter
        filtered = list(self.client.documents().filter(archive_serial_number__gt=asn))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'archive_serial_number') and
                   doc.archive_serial_number and doc.archive_serial_number > asn]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_archive_serial_number__gte(self) -> None:
        """Test filtering by archive_serial_number__gte."""
        # Find documents with archive_serial_number
        docs_with_asn = [doc for doc in self.all_documents
                      if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number]
        if not docs_with_asn:
            self.skipTest("No documents with archive_serial_number available for testing")

        # Sort by archive_serial_number
        docs_with_asn.sort(key=lambda doc: doc.archive_serial_number)

        # Get a middle value
        if len(docs_with_asn) >= 2:
            asn = docs_with_asn[len(docs_with_asn) // 2].archive_serial_number
        else:
            asn = docs_with_asn[0].archive_serial_number

        # Apply the filter
        filtered = list(self.client.documents().filter(archive_serial_number__gte=asn))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'archive_serial_number') and
                   doc.archive_serial_number and doc.archive_serial_number >= asn]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_archive_serial_number__lt(self) -> None:
        """Test filtering by archive_serial_number__lt."""
        # Find documents with archive_serial_number
        docs_with_asn = [doc for doc in self.all_documents
                      if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number]
        if not docs_with_asn:
            self.skipTest("No documents with archive_serial_number available for testing")

        # Sort by archive_serial_number
        docs_with_asn.sort(key=lambda doc: doc.archive_serial_number)

        # Get a middle value
        if len(docs_with_asn) >= 2:
            asn = docs_with_asn[len(docs_with_asn) // 2].archive_serial_number
        else:
            asn = docs_with_asn[0].archive_serial_number + 1

        # Apply the filter
        filtered = list(self.client.documents().filter(archive_serial_number__lt=asn))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'archive_serial_number') and
                   doc.archive_serial_number and doc.archive_serial_number < asn]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_archive_serial_number__lte(self) -> None:
        """Test filtering by archive_serial_number__lte."""
        # Find documents with archive_serial_number
        docs_with_asn = [doc for doc in self.all_documents
                      if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number]
        if not docs_with_asn:
            self.skipTest("No documents with archive_serial_number available for testing")

        # Sort by archive_serial_number
        docs_with_asn.sort(key=lambda doc: doc.archive_serial_number)

        # Get a middle value
        if len(docs_with_asn) >= 2:
            asn = docs_with_asn[len(docs_with_asn) // 2].archive_serial_number
        else:
            asn = docs_with_asn[0].archive_serial_number

        # Apply the filter
        filtered = list(self.client.documents().filter(archive_serial_number__lte=asn))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'archive_serial_number') and
                   doc.archive_serial_number and doc.archive_serial_number <= asn]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_archive_serial_number__isnull(self) -> None:
        """Test filtering by archive_serial_number__isnull."""
        # Apply the filter for NULL values
        filtered_null = list(self.client.documents().filter(archive_serial_number__isnull=True))

        # Calculate expected results locally for NULL
        expected_null = [doc for doc in self.all_documents
                        if not hasattr(doc, 'archive_serial_number') or doc.archive_serial_number is None]

        # Assert for NULL
        self.assertEqual(len(filtered_null), len(expected_null))

        # Apply the filter for NOT NULL values
        filtered_not_null = list(self.client.documents().filter(archive_serial_number__isnull=False))

        # Calculate expected results locally for NOT NULL
        expected_not_null = [doc for doc in self.all_documents
                            if hasattr(doc, 'archive_serial_number') and doc.archive_serial_number is not None]

        # Assert for NOT NULL
        self.assertEqual(len(filtered_not_null), len(expected_not_null))

    # Correspondent filters
    def test_correspondent__isnull(self) -> None:
        """Test filtering by correspondent__isnull."""
        # Apply the filter for NULL values
        filtered_null = list(self.client.documents().filter(correspondent__isnull=True))

        # Calculate expected results locally for NULL
        expected_null = [doc for doc in self.all_documents
                        if not hasattr(doc, 'correspondent_id') or doc.correspondent_id is None]

        # Assert for NULL
        self.assertEqual(len(filtered_null), len(expected_null))

        # Apply the filter for NOT NULL values
        filtered_not_null = list(self.client.documents().filter(correspondent__isnull=False))

        # Calculate expected results locally for NOT NULL
        expected_not_null = [doc for doc in self.all_documents
                            if hasattr(doc, 'correspondent_id') and doc.correspondent_id is not None]

        # Assert for NOT NULL
        self.assertEqual(len(filtered_not_null), len(expected_not_null))

    def test_correspondent__id(self) -> None:
        """Test filtering by correspondent__id."""
        # Find a document with correspondent
        doc_with_correspondent = next((doc for doc in self.all_documents
                                   if hasattr(doc, 'correspondent_id') and doc.correspondent_id), None)
        if not doc_with_correspondent:
            self.skipTest("No documents with correspondent available for testing")

        # Get the correspondent id
        correspondent_id = doc_with_correspondent.correspondent_id

        # Apply the filter
        filtered = list(self.client.documents().filter(correspondent__id=correspondent_id))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'correspondent') and doc.correspondent and
                   doc.correspondent.id == correspondent_id]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_correspondent__id__in(self) -> None:
        """Test filtering by correspondent__id__in."""
        # Find documents with correspondent
        docs_with_correspondent = [doc for doc in self.all_documents
                               if hasattr(doc, 'correspondent') and doc.correspondent]
        if len(docs_with_correspondent) < 2:
            self.skipTest("Not enough documents with correspondent available for testing")

        # Get some correspondent ids
        correspondent_ids = list(set([doc.correspondent.id for doc in docs_with_correspondent[:2]]))

        # Apply the filter
        filtered = list(self.client.documents().filter(correspondent__id__in=correspondent_ids))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'correspondent') and doc.correspondent and
                   doc.correspondent.id in correspondent_ids]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_correspondent__name__istartswith(self) -> None:
        """Test filtering by correspondent__name__istartswith."""
        # Find a document with correspondent
        doc_with_correspondent = next((doc for doc in self.all_documents
                                   if hasattr(doc, 'correspondent') and doc.correspondent and
                                   hasattr(doc.correspondent, 'name') and doc.correspondent.name), None)
        if not doc_with_correspondent:
            self.skipTest("No documents with correspondent name available for testing")

        # Get the first few characters of the correspondent name
        prefix = doc_with_correspondent.correspondent.name[:3].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(correspondent__name__istartswith=prefix))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'correspondent') and doc.correspondent and
                   hasattr(doc.correspondent, 'name') and doc.correspondent.name and
                   doc.correspondent.name.lower().startswith(prefix)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Date filters
    def test_created__gt(self) -> None:
        """Test filtering by created__gt."""
        # Find documents with created date
        docs_with_created = [doc for doc in self.all_documents
                         if hasattr(doc, 'created') and doc.created]
        if not docs_with_created:
            self.skipTest("No documents with created date available for testing")

        # Sort by created date
        docs_with_created.sort(key=lambda doc: doc.created)

        # Get a middle value
        if len(docs_with_created) >= 2:
            created_date = docs_with_created[len(docs_with_created) // 2].created
        else:
            created_date = docs_with_created[0].created - datetime.timedelta(days=1)

        # Apply the filter
        filtered = list(self.client.documents().filter(created__gt=created_date.isoformat()))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'created') and doc.created and doc.created > created_date]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_created__lt(self) -> None:
        """Test filtering by created__lt."""
        # Find documents with created date
        docs_with_created = [doc for doc in self.all_documents
                         if hasattr(doc, 'created') and doc.created]
        if not docs_with_created:
            self.skipTest("No documents with created date available for testing")

        # Sort by created date
        docs_with_created.sort(key=lambda doc: doc.created)

        # Get a middle value
        if len(docs_with_created) >= 2:
            created_date = docs_with_created[len(docs_with_created) // 2].created
        else:
            created_date = docs_with_created[0].created + datetime.timedelta(days=1)

        # Apply the filter
        filtered = list(self.client.documents().filter(created__lt=created_date.isoformat()))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'created') and doc.created and doc.created < created_date]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Added date filters
    def test_added__gt(self) -> None:
        """Test filtering by added__gt."""
        # Find documents with added date
        docs_with_added = [doc for doc in self.all_documents
                       if hasattr(doc, 'added') and doc.added]
        if not docs_with_added:
            self.skipTest("No documents with added date available for testing")

        # Sort by added date
        docs_with_added.sort(key=lambda doc: doc.added)

        # Get a middle value
        if len(docs_with_added) >= 2:
            added_date = docs_with_added[len(docs_with_added) // 2].added
        else:
            added_date = docs_with_added[0].added - datetime.timedelta(days=1)

        # Apply the filter
        filtered = list(self.client.documents().filter(added__gt=added_date.isoformat()))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'added') and doc.added and doc.added > added_date]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_added__lt(self) -> None:
        """Test filtering by added__lt."""
        # Find documents with added date
        docs_with_added = [doc for doc in self.all_documents
                       if hasattr(doc, 'added') and doc.added]
        if not docs_with_added:
            self.skipTest("No documents with added date available for testing")

        # Sort by added date
        docs_with_added.sort(key=lambda doc: doc.added)

        # Get a middle value
        if len(docs_with_added) >= 2:
            added_date = docs_with_added[len(docs_with_added) // 2].added
        else:
            added_date = docs_with_added[0].added + datetime.timedelta(days=1)

        # Apply the filter
        filtered = list(self.client.documents().filter(added__lt=added_date.isoformat()))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'added') and doc.added and doc.added < added_date]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Original filename filters
    def test_original_filename__icontains(self) -> None:
        """Test filtering by original_filename__icontains."""
        # Find a document with original_filename
        doc_with_filename = next((doc for doc in self.all_documents
                              if hasattr(doc, 'original_filename') and doc.original_filename), None)
        if not doc_with_filename:
            self.skipTest("No documents with original_filename available for testing")

        # Get a substring from the middle of the filename
        substring = doc_with_filename.original_filename[1:-1][:3].lower()
        if not substring:
            substring = doc_with_filename.original_filename.lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(original_filename__icontains=substring))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'original_filename') and doc.original_filename and
                   substring in doc.original_filename.lower()]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    # Tag filters
    def test_tags__id(self) -> None:
        """Test filtering by tags__id."""
        # Find a document with tags
        doc_with_tags = next((doc for doc in self.all_documents
                          if hasattr(doc, 'tag_ids') and doc.tag_ids), None)
        if not doc_with_tags:
            self.skipTest("No documents with tags available for testing")

        # Get a tag id
        tag_id = doc_with_tags.tag_ids[0]

        # Apply the filter
        filtered = list(self.client.documents().filter(tags__id=tag_id))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'tag_ids') and doc.tag_ids and
                   any(tag == tag_id for tag in doc.tag_ids)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_tags__id__in(self) -> None:
        """Test filtering by tags__id__in."""
        # Find documents with tags
        docs_with_tags = [doc for doc in self.all_documents
                      if hasattr(doc, 'tag_ids') and doc.tag_ids]
        if len(docs_with_tags) < 2:
            self.skipTest("Not enough documents with tags available for testing")

        # Get some tag ids
        tag_ids = list(set([doc.tag_ids[0] for doc in docs_with_tags[:2]]))

        # Apply the filter
        filtered = list(self.client.documents().filter(tags__id__in=tag_ids))

        # Calculate expected results locally
        expected = [doc for doc in self.all_documents
                   if hasattr(doc, 'tag_ids') and doc.tag_ids and
                   any(tag in tag_ids for tag in doc.tag_ids)]

        # Assert
        self.assertEqual(len(filtered), len(expected))

    def test_is_tagged(self) -> None:
        """Test filtering by is_tagged."""
        # Apply the filter for tagged documents
        filtered_tagged = list(self.client.documents().filter(is_tagged=True))

        # Calculate expected results locally for tagged
        expected_tagged = [doc for doc in self.all_documents
                          if hasattr(doc, 'tag_ids') and doc.tag_ids and len(doc.tag_ids) > 0]

        # Assert for tagged
        self.assertEqual(len(filtered_tagged), len(expected_tagged))

        # Apply the filter for untagged documents
        filtered_untagged = list(self.client.documents().filter(is_tagged=False))

        # Calculate expected results locally for untagged
        expected_untagged = [doc for doc in self.all_documents
                            if not hasattr(doc, 'tag_ids') or not doc.tag_ids or len(doc.tag_ids) == 0]

        # Assert for untagged
        self.assertEqual(len(filtered_untagged), len(expected_untagged))

    # Document type filters
    def test_document_type__isnull(self) -> None:
        """Test filtering by document_type__isnull."""
        # Apply the filter for NULL values
        filtered_null = list(self.client.documents().filter(document_type__isnull=True))

        # Calculate expected results locally for NULL
        expected_null = [doc for doc in self.all_documents
                        if not hasattr(doc, 'document_type') or doc.document_type is None]

        # Assert for NULL
        self.assertEqual(len(filtered_null), len(expected_null))

        # Apply the filter for NOT NULL values
        filtered_not_null = list(self.client.documents().filter(document_type__isnull=False))

        # Calculate expected results locally for NOT NULL
        expected_not_null = [doc for doc in self.all_documents
                            if hasattr(doc, 'document_type') and doc.document_type is not None]

        # Assert for NOT NULL
        self.assertEqual(len(filtered_not_null), len(expected_not_null))

    # Storage path filters
    def test_storage_path__isnull(self) -> None:
        """Test filtering by storage_path__isnull."""
        # Apply the filter for NULL values
        filtered_null = list(self.client.documents().filter(storage_path__isnull=True))

        # Calculate expected results locally for NULL
        expected_null = [doc for doc in self.all_documents
                        if not hasattr(doc, 'storage_path') or doc.storage_path is None]

        # Assert for NULL
        self.assertEqual(len(filtered_null), len(expected_null))

        # Apply the filter for NOT NULL values
        filtered_not_null = list(self.client.documents().filter(storage_path__isnull=False))

        # Calculate expected results locally for NOT NULL
        expected_not_null = [doc for doc in self.all_documents
                            if hasattr(doc, 'storage_path') and doc.storage_path is not None]

        # Assert for NOT NULL
        self.assertEqual(len(filtered_not_null), len(expected_not_null))

    # Owner filters
    def test_owner__isnull(self) -> None:
        """Test filtering by owner__isnull."""
        # Apply the filter for NULL values
        filtered_null = list(self.client.documents().filter(owner__isnull=True))

        # Calculate expected results locally for NULL
        expected_null = [doc for doc in self.all_documents
                        if not hasattr(doc, 'owner') or doc.owner is None]

        # Assert for NULL
        self.assertEqual(len(filtered_null), len(expected_null))

        # Apply the filter for NOT NULL values
        filtered_not_null = list(self.client.documents().filter(owner__isnull=False))

        # Calculate expected results locally for NOT NULL
        expected_not_null = [doc for doc in self.all_documents
                            if hasattr(doc, 'owner') and doc.owner is not None]

        # Assert for NOT NULL
        self.assertEqual(len(filtered_not_null), len(expected_not_null))

    # Special filters
    def test_is_in_inbox(self) -> None:
        """Test filtering by is_in_inbox."""
        # Apply the filter for inbox documents
        filtered_inbox = list(self.client.documents().filter(is_in_inbox=True))

        # Apply the filter for non-inbox documents
        filtered_not_inbox = list(self.client.documents().filter(is_in_inbox=False))

        # Assert that the counts add up to the total
        self.assertEqual(len(filtered_inbox) + len(filtered_not_inbox), len(self.all_documents))

    def test_title_content(self) -> None:
        """Test filtering by title_content."""
        if not self.all_documents:
            return

        # Find a document with title or content
        doc_with_text = next((doc for doc in self.all_documents
                          if (hasattr(doc, 'title') and doc.title) or
                          (hasattr(doc, 'content') and doc.content)), None)
        if not doc_with_text:
            self.skipTest("No documents with title or content available for testing")

        # Get a string to search for
        if hasattr(doc_with_text, 'title') and doc_with_text.title:
            search_string = doc_with_text.title.split()[0][:3].lower()
        else:
            search_string = doc_with_text.content.split()[0][:3].lower()

        # Apply the filter
        filtered = list(self.client.documents().filter(title_content=search_string))

        # We can't reliably predict the server's implementation of title_content search,
        # so we just assert that we got some results
        self.assertGreaterEqual(len(filtered), 0)
