"""
Integration tests for document queryset bulk operations.
"""
import time
from typing import Any, List, Optional
import tempfile
import pytest

from paperap.client import PaperlessClient
from paperap.models.document import Document
from tests.lib.unittest import UnitTestCase, DocumentUnitTest
from tests.lib import factories


class TestDocumentQuerysetBulkOperations(DocumentUnitTest):
    """Test document queryset bulk operations functionality."""
    mock_env = False
    test_docs: list[Document] = []

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test class by retrieving needed documents."""
        super().setUpClass()
        # Get a client
        cls.client = PaperlessClient()

        # Get some existing documents for reference
        cls.all_documents = list(cls.client.documents().all())
        if not cls.all_documents:
            return  # Tests will be skipped if no documents exist

        # Get references to correspondent, document type, storage path for tests
        test_doc = cls.all_documents[0]
        cls.correspondent_id = None
        for doc in cls.all_documents:
            if hasattr(doc, 'correspondent') and doc.correspondent:
                cls.correspondent_id = doc.correspondent.id
                break

        cls.document_type_id = None
        for doc in cls.all_documents:
            if hasattr(doc, 'document_type') and doc.document_type:
                cls.document_type_id = doc.document_type.id
                break

        cls.storage_path_id = None
        for doc in cls.all_documents:
            if hasattr(doc, 'storage_path') and doc.storage_path:
                cls.storage_path_id = doc.storage_path.id
                break

        # Get a tag ID for tag operations
        cls.tag_id = None
        for doc in cls.all_documents:
            if hasattr(doc, 'tags') and doc.tags:
                cls.tag_id = doc.tags[0].id
                break
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                cls.tag_id = doc.tag_ids[0]
                break

    def setUp(self) -> None:
        """Set up each test."""
        super().setUp()
        if not self.all_documents:
            self.skipTest("No documents available for testing")

        # Skip if we need a tag but don't have one
        if not hasattr(self, 'tag_operations_checked'):
            self.__class__.tag_operations_checked = True
            if not self.tag_id:
                self.skipTest("No tags available for tag operations testing")

        # Clean up any test documents from previous test runs
        self._cleanup_test_documents()

    def tearDown(self) -> None:
        """Clean up after each test."""
        self._cleanup_test_documents()
        super().tearDown()

    def _cleanup_test_documents(self) -> None:
        """Delete any test documents created during tests."""
        try:
            test_docs = list(self.client.documents().title("BULK_TEST_DOC", exact=False))
            if test_docs:
                # Clean up using the resource directly to avoid creating a recursive situation
                doc_ids = [doc.id for doc in test_docs]
                if doc_ids:
                    self.client.documents.delete(doc_ids)
        except Exception as e:
            # Don't fail the test if cleanup fails
            print(f"Warning: Failed to clean up test documents: {e}")

    def _create_test_document(self) -> Document:
        """
        Create a test document by copying an existing one.

        This approach avoids requiring actual file uploads in the test.
        """
        source_doc = self.all_documents[0]

        # Create a copy with a test title
        doc_data = source_doc.to_dict(include_read_only=False)
        doc_data.pop('id', None)
        doc_data['title'] = "BULK_TEST_DOC"

        # Ensure we have minimal required fields
        if 'correspondent' in doc_data:
            doc_data.pop('correspondent', None)  # Let server handle relationship
        if 'document_type' in doc_data:
            doc_data.pop('document_type', None)  # Let server handle relationship

        # Create a txt file to upload as a new document
        new_doc = factories.DocumentFactory.upload_sync(self.client, **doc_data)

        # Keep track for cleanup
        self.__class__.test_docs.append(new_doc)

        return new_doc

    def _create_multiple_test_documents(self, count: int = 3) -> list[Document]:
        """Create multiple test documents."""
        docs = []
        for i in range(count):
            docs.append(self._create_test_document())
        return docs

    def test_modify_tags(self) -> None:
        """Test modify_tags operation."""
        if not self.tag_id:
            self.skipTest("No tags available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Verify documents don't have the tag
        for doc in docs:
            has_tag = False
            if hasattr(doc, 'tags') and doc.tags:
                has_tag = any(tag.id == self.tag_id for tag in doc.tags)
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                has_tag = self.tag_id in doc.tag_ids
            self.skipTest("Test document should not have the tag initially")

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.modify_tags(add_tags=[self.tag_id])

        # Refresh the documents and verify the tag was added
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            has_tag = False
            if hasattr(doc, 'tags') and doc.tags:
                has_tag = any(tag.id == self.tag_id for tag in doc.tags)
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                has_tag = self.tag_id in doc.tag_ids
            self.assertTrue(has_tag, "Tag should have been added to the document")

    def test_add_tag(self) -> None:
        """Test add_tag operation."""
        if not self.tag_id:
            self.skipTest("No tags available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.add_tag(self.tag_id)

        # Refresh the documents and verify the tag was added
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            has_tag = False
            if hasattr(doc, 'tags') and doc.tags:
                has_tag = any(tag.id == self.tag_id for tag in doc.tags)
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                has_tag = self.tag_id in doc.tag_ids
            self.assertTrue(has_tag, "Tag should have been added to the document")

    def test_remove_tag(self) -> None:
        """Test remove_tag operation."""
        if not self.tag_id:
            self.skipTest("No tags available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # First, add the tag to the documents
        self.client.documents.add_tag(doc_ids, self.tag_id)

        # Refresh the documents
        time.sleep(1)  # Give server time to process
        docs = list(self.client.documents().filter(id__in=doc_ids))

        # Verify documents have the tag
        for doc in docs:
            has_tag = False
            if hasattr(doc, 'tags') and doc.tags:
                has_tag = any(tag.id == self.tag_id for tag in doc.tags)
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                has_tag = self.tag_id in doc.tag_ids
            self.assertTrue(has_tag, "Test document should have the tag after adding it")

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.remove_tag(self.tag_id)

        # Refresh the documents and verify the tag was removed
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            has_tag = False
            if hasattr(doc, 'tags') and doc.tags:
                has_tag = any(tag.id == self.tag_id for tag in doc.tags)
            elif hasattr(doc, 'tag_ids') and doc.tag_ids:
                has_tag = self.tag_id in doc.tag_ids
            self.assertFalse(has_tag, "Tag should have been removed from the document")

    def test_set_correspondent(self) -> None:
        """Test set_correspondent operation."""
        if not self.correspondent_id:
            self.skipTest("No correspondent available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.update(correspondent = self.correspondent_id)

        # Refresh the documents and verify the correspondent was set
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            self.assertEqual(
                doc.correspondent.id if hasattr(doc, 'correspondent') and doc.correspondent else None,
                self.correspondent_id,
                "Correspondent should have been set on the document"
            )

    def test_set_document_type(self) -> None:
        """Test set_document_type operation."""
        if not self.document_type_id:
            self.skipTest("No document type available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.update(document_type = self.document_type_id)

        # Refresh the documents and verify the document type was set
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            self.assertEqual(
                doc.document_type.id if hasattr(doc, 'document_type') and doc.document_type else None,
                self.document_type_id,
                "Document type should have been set on the document"
            )

    def test_set_storage_path(self) -> None:
        """Test set_storage_path operation."""
        if not self.storage_path_id:
            self.skipTest("No storage path available for testing")

        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.update(storage_path = self.storage_path_id)

        # Refresh the documents and verify the storage path was set
        time.sleep(1)  # Give server time to process
        updated_docs = list(self.client.documents().filter(id__in=doc_ids))

        for doc in updated_docs:
            self.assertEqual(
                doc.storage_path.id if hasattr(doc, 'storage_path') and doc.storage_path else None,
                self.storage_path_id,
                "Storage path should have been set on the document"
            )

    @pytest.mark.skip(reason="Test requires actual document content to rotate")
    def test_rotate(self) -> None:
        """
        Test rotate operation.

        This test is skipped by default since rotation requires actual
        document content and not just metadata.
        """
        # Create test documents
        docs = self._create_multiple_test_documents(1)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.rotate(90)

        # Verification would require checking document content TODO

    @pytest.mark.skip(reason="Destructive test that would delete documents")
    def test_delete(self) -> None:
        """
        Test bulk_delete operation.

        This test is skipped by default to avoid accidentally deleting documents.
        """
        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.delete()

        # Verify documents are deleted
        time.sleep(1)  # Give server time to process
        remaining_docs = list(self.client.documents().filter(id__in=doc_ids))
        self.assertEqual(len(remaining_docs), 0, "Documents should have been deleted")

        # Clear the test_docs list since we've deleted them
        self.__class__.test_docs = []

    @pytest.mark.skip(reason="Destructive test that would merge documents")
    def test_merge(self) -> None:
        """
        Test merge operation.

        This test is skipped by default since merging is destructive and
        creates a new document.
        """
        # Create test documents
        docs = self._create_multiple_test_documents(2)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        result = queryset.merge()

        # Check the result
        self.assertTrue(result, "Merge operation should have submitted successfully")

    @pytest.mark.skip(reason="Reprocessing requires document content")
    def test_reprocess(self) -> None:
        """
        Test reprocess operation.

        This test is skipped by default since reprocessing requires actual
        document content and not just metadata.
        """
        # Create test documents
        docs = self._create_multiple_test_documents(1)
        doc_ids = [doc.id for doc in docs]

        # Apply the bulk operation using queryset
        queryset = self.client.documents().filter(id__in=doc_ids)
        queryset.reprocess()

        # TODO
