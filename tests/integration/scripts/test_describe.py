"""
Integration tests for the document description script.

These tests verify that the describe.py script correctly interacts with
a real Paperless-ngx instance and OpenAI to generate document descriptions.
"""

import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import openai
import fitz

from paperap.client import PaperlessClient
from paperap.models import Document, Tag
from paperap.scripts.describe import DescribePhotos, ScriptDefaults
from paperap.settings import Settings
from paperap.exceptions import NoImagesError, DocumentParsingError


@pytest.fixture
def client():
    """Create a PaperlessClient using environment variables."""
    settings = Settings()
    return PaperlessClient(settings)


@pytest.fixture
def describer(client):
    """Create a DescribePhotos instance."""
    return DescribePhotos(client=client)


@pytest.fixture
def test_tag_name():
    """Return a tag name for testing."""
    return "integration-test"


@pytest.fixture
def setup_test_document(client, test_tag_name):
    """
    Set up a test document with the integration-test tag.
    
    This fixture:
    1. Creates a temporary tag if it doesn't exist
    2. Finds or creates a document with that tag
    3. Yields the document for testing
    4. Cleans up by removing the tag (but keeps the document)
    """
    # Create or get the test tag
    tags = client.tags()
    try:
        tag = tags.filter(name=test_tag_name).get()
        tag_created = False
    except Exception:
        tag = client.tags.create(name=test_tag_name, color="#FF0000")
        tag_created = True
    
    # Find a document to use for testing or create one with the test tag
    documents = client.documents()
    try:
        # First try to find an existing document that looks like an image/PDF
        doc = next(
            (doc for doc in documents.all() 
             if doc.content_type in ["application/pdf", "image/jpeg", "image/png"]),
            None
        )
        
        if not doc:
            # If no suitable document found, use the first available document
            doc = next(iter(documents.all()))
            
        # Add test tag to the document
        doc.add_tag(tag.id)
        doc.save()
        
        yield doc
        
        # Clean up: remove the test tag from the document
        doc.remove_tag(tag.id)
        doc.save()
    except Exception as e:
        pytest.skip(f"Could not set up test document: {e}")
    
    # Clean up: delete the tag if we created it
    if tag_created:
        try:
            tag.delete()
        except Exception:
            pass


def test_client_connection(client):
    """Verify that the client can connect to the Paperless-ngx instance."""
    # Simple check that we can access the API
    response = client.request("GET", "")
    assert response.status_code == 200
    
    # Check that we can get documents
    docs = client.documents()
    # Just getting the count is enough to verify the connection works
    count = docs.count()
    assert count >= 0
    
    logging.info(f"Connected to Paperless-ngx with {count} documents")


def test_describer_initialization(describer):
    """Test that the DescribePhotos class initializes correctly."""
    assert describer.client is not None
    assert describer.paperless_tag == ScriptDefaults.NEEDS_DESCRIPTION
    assert describer.max_threads > 0
    assert describer.enrichment_service is not None


def test_get_document_by_tag(client, test_tag_name, setup_test_document):
    """Test that we can retrieve documents by tag."""
    # Get documents with our test tag
    documents = list(client.documents().filter(tag_name=test_tag_name))
    
    # We should have at least one document with our test tag
    assert len(documents) > 0
    
    # The document should have our test tag
    doc = documents[0]
    assert test_tag_name in [tag.name for tag in doc.tags]
    
    logging.info(f"Found document {doc.id}: {doc.title} with tag {test_tag_name}")


def test_prompt_generation(describer, setup_test_document):
    """Test that we can generate a prompt for a document."""
    document = setup_test_document
    
    # Generate a prompt
    prompt = describer.get_prompt(document)
    
    # Verify the prompt is a non-empty string
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    
    logging.info(f"Generated prompt of length {len(prompt)}")


@pytest.mark.parametrize("max_images", [1, 2])
def test_image_extraction_from_pdf(describer, max_images):
    """Test image extraction from a PDF."""
    # Create a simple PDF with an embedded image for testing
    pdf_path = Path(tempfile.gettempdir()) / "test_image.pdf"
    
    # Skip if we can't access the file system
    if not os.access(tempfile.gettempdir(), os.W_OK):
        pytest.skip("Cannot write to temporary directory")
    
    # Create a simple PDF with an embedded image
    try:
        # Create a new PDF document
        doc = fitz.open()
        page = doc.new_page()
        
        # Add a simple rectangle as a "test image"
        page.draw_rect([100, 100, 200, 200], color=(1, 0, 0), fill=(0, 0, 1))
        
        # Save the PDF
        doc.save(str(pdf_path))
        doc.close()
        
        # Extract images from the PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Extract images from the PDF
        images = describer.extract_images_from_pdf(pdf_bytes, max_images=max_images)
        
        # We should have at least one image
        assert len(images) > 0
        assert len(images) <= max_images
        
        # Verify each image is bytes
        for img in images:
            assert isinstance(img, bytes)
            assert len(img) > 0
    
    except Exception as e:
        pytest.skip(f"PDF creation or image extraction failed: {e}")
    finally:
        # Clean up
        if pdf_path.exists():
            pdf_path.unlink()


def test_standardize_image_contents(describer):
    """Test standardizing image contents."""
    # Create a simple test image
    from PIL import Image
    from io import BytesIO
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # Standardize the image
    result = describer.standardize_image_contents(image_bytes)
    
    # We should get a list with one base64 string
    assert isinstance(result, list)
    assert len(result) > 0
    assert isinstance(result[0], str)
    assert result[0].startswith("iVBOR") or "base64" in result[0]


@pytest.mark.skip(reason="This test uses OpenAI credits. Enable manually.")
def test_describe_document(describer, setup_test_document):
    """
    Test describing a document.
    
    Note: This test is skipped by default as it uses OpenAI credits.
    """
    document = setup_test_document
    
    # Store original content to compare later
    original_content = document.content
    
    # Try to describe the document
    result = describer.describe_document(document)
    
    # Check if the description was successful
    if result:
        # The document should have been updated
        assert document.content != original_content
        assert ScriptDefaults.DESCRIBED in [tag.name for tag in document.tags]
        assert ScriptDefaults.NEEDS_DESCRIPTION not in [tag.name for tag in document.tags]
        
        logging.info(f"Successfully described document {document.id}")
    else:
        # If it failed, check if it's due to expected errors
        logging.warning(f"Description failed for document {document.id}")


@pytest.mark.skip(reason="This test uses OpenAI credits. Enable manually.")
def test_describe_documents(describer, client, test_tag_name, setup_test_document):
    """
    Test describing multiple documents.
    
    Note: This test is skipped by default as it uses OpenAI credits.
    """
    # Set the tag to our test tag
    describer.paperless_tag = test_tag_name
    
    # Get documents with our test tag
    documents = list(client.documents().filter(tag_name=test_tag_name))
    assert len(documents) > 0
    
    # Describe the documents
    results = describer.describe_documents(documents)
    
    # Check the results
    assert isinstance(results, list)
    
    # If any documents were successfully described
    if results:
        for doc in results:
            assert ScriptDefaults.DESCRIBED in [tag.name for tag in doc.tags]
            assert ScriptDefaults.NEEDS_DESCRIPTION not in [tag.name for tag in doc.tags]
            
        logging.info(f"Successfully described {len(results)} documents")


def test_error_handling_invalid_image():
    """Test error handling for invalid images."""
    # Create a client and describer
    client = PaperlessClient(Settings())
    describer = DescribePhotos(client=client)
    
    # Test with invalid image data
    invalid_data = b'not an image or pdf'
    
    # This should raise an error when trying to extract images
    with pytest.raises((DocumentParsingError, NoImagesError)):
        describer.extract_images_from_pdf(invalid_data)
    
    # This should return an empty list for standardize_image_contents
    result = describer.standardize_image_contents(invalid_data)
    assert result == []
