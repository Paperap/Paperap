# Usage Guide

This guide covers how to use Paperap to interact with your Paperless-NgX instance, from basic setup to advanced operations.

## Client Setup

The `PaperlessClient` class is your entry point to the Paperless-NgX API:

```python
from paperap import PaperlessClient
from paperap.settings import Settings

# Token-based authentication from environment variables (recommended)
# Set PAPERLESS_BASE_URL and PAPERLESS_TOKEN in your environment
client = PaperlessClient()

# Alternatively, specify credentials directly
client = PaperlessClient(
    base_url="http://paperless.local:8000",  # Your Paperless-NgX URL
    token="your_api_token"                   # API token from admin interface
)

# Username and password authentication
client = PaperlessClient(
    base_url="http://paperless.local:8000",
    username="your_username",
    password="your_password"
)

# With custom options
client = PaperlessClient(
    base_url="https://paperless.example.com",
    token="your_api_token",
    timeout=30,                  # Request timeout in seconds
    plugins=[MyCustomPlugin()],  # Custom plugins
    save_on_write=False          # Require explicit save() calls
)
```

## Resources, Models, and QuerySets

Paperap works very similarly to django, and syntax is largely interchangeable.

Each endpoint exposed by paperless NGX has a corresponding Model, Resource, and QuerySet.

- Resources serve as a gateway for sending requests to the API, and parsing its responses.

- Models work just like a typical ORM model, but loaded from the Paperless NGX REST API, instead of a database.

- QuerySets are a lazy-loaded iterator of Models that can be filtered, ordered, and sliced.

```python
# Access resources from the client
client.documents  # DocumentResource
client.tags       # TagResource

# Access querysets by calling the resource
all_docs = client.documents()           # DocumentQuerySet
all_docs = client.documents.all()       # Equivalent to above
tags = client.tags().filter(name="tax") # TagQuerySet

# QuerySets are chainable
docs = client.documents(name="tax")
docs = client.documents().filter(name="tax")
docs = client.documents().all().filter(name="tax").order_by("created")

# Access models by iterating over querysets
document = client.documents.get(123)    # DocumentModel
for tag in client.tags().filter(name__icontains="invoice"):
    print(tag.name)
```

## Working with Documents

Documents are the core resource in Paperless-NgX. Paperap provides a rich interface for managing them:

### Retrieving Documents

```python
# Get all documents (lazy-loaded)
all_docs = client.documents()

# Get a specific document by ID
doc = client.documents().get(123)

# Access document properties
print(f"Title: {doc.title}")
print(f"Added: {doc.added}")
print(f"Content: {doc.content}")

# Count documents
total = client.documents().count()
print(f"Total documents: {total}")
```

### Searching and Filtering

```python
# Basic filtering
invoices = client.documents().filter(
    title__icontains="invoice",
    correspondent__id=5
)

# Filter by date range
from datetime import datetime, timedelta
last_month = datetime.now() - timedelta(days=30)
recent_docs = client.documents().filter(
    added__gt=last_month.isoformat()
)

# Filter by specific tag
tagged_docs = client.documents(tags__id=3)

# Complex filtering
complex_query = client.documents.filter(
    title__icontains="invoice",
    correspondent__name__icontains="electric",
    created__gt="2023-01-01T00:00:00Z"
).exclude(
    tags__name="archived"
)

# Chain filters for more complex queries
from_2023 = client.documents.filter(created__gte="2023-01-01")
tax_docs = from_2023.filter(tags__name="tax")
important_tax_docs = tax_docs.filter(tags__name="important")
```

### Uploading Documents

```python
# Basic document upload with a file path
doc = client.documents.upload("path/to/document.pdf")

# Upload with metadata
doc = client.documents.upload(
    "path/to/invoice.pdf",
    title="Electric Bill March 2023",
    correspondent=5,               # ID of correspondent 
    document_type=3,               # ID of document type
    tags=[1, 2],                   # List of tag IDs
    created="2023-03-15",          # Custom created date
    archive_serial_number="INV-123" # Custom reference number
)

# Upload with file object
with open("document.pdf", "rb") as f:
    doc = client.documents.upload(
        file=f,
        title="My Document"
    )

# Asynchronous upload (returns task_id instead of document)
task_id = client.documents.upload_async("path/to/large_document.pdf")

# Wait for the task to complete and get the document
document = client.tasks.wait_for_task(task_id)

### Downloading Documents

```python
# Download original document
doc.download("my_document.pdf")

# Download original to a specific path
import os
doc.download(os.path.join("/tmp", "download.pdf"))

# Access the raw bytes
original_content = doc.download_content()

# Download the archive version (if available)
doc.download("my_document.pdf", archive_version=True)

# Download a thumbnail
doc.download_thumbnail("thumbnail.png")
```

### Updating Documents

The setting PAPERLESS_SAVE_ON_WRITE can be set to True to automatically save changes to the server when an attribute is set on a model, or False to require an explicit call to the save method. `save_on_write` can be passed to the PaperlessClient constructor to set the value without environment variables.

```python
# With save_on_write set to True
doc = client.documents.get(123)
doc.title = "New Title" # Sends a request to Paperless NGX to save the model

# With save_on_write set to False
doc = client.documents.get(123)
doc.title = "New Title"
doc.save() # Sends a request to Paperless NGX to save the model

# Update with dictionary
doc.update(
    title="Updated Title",
    archive_serial_number="NEW-123"
)

# Bulk update multiple documents
client.documents.filter(correspondent__name="Old Company").update(correspondent=123)
```

### Deleting Documents

```python
# Delete a document
doc = client.documents.get(123)
doc.delete()

# Bulk delete
client.documents.filter(created__lt="2020-01-01").delete()
```

### Bulk Operations

Perform operations on multiple documents efficiently:

```python
# Bulk add tags to documents
tax_docs = client.documents.filter(title__icontains="tax")
tax_docs.add_tag(5)  # Add tag with ID 5

# Bulk remove tags
old_docs = client.documents.filter(created_before="2020-01-01")
old_docs.remove_tag(7)  # Remove tag with ID 7

# Bulk update document metadata
invoices = client.documents.filter(title__icontains="invoice")
invoices.update(
    correspondent=12,    # Set correspondent ID 
    document_type=3      # Set document type ID
)

# Bulk modify custom fields
docs = client.documents.filter(correspondent_id=5)
docs.modify_custom_fields(
    add_custom_fields={3: "High", 7: "2023-04-15"},
    remove_custom_fields=[9]
)

# Bulk delete
temp_docs = client.documents.filter(tags__name="temporary")
temp_docs.delete()

# Bulk reprocess documents
client.documents.filter(content="").reprocess()

# Merge multiple documents
client.documents.filter(correspondent_id=5).merge(
    metadata_document_id=123,  # Use metadata from this document
    delete_originals=True      # Delete original documents after merging
)

# Bulk rotate documents
client.documents.filter(title__contains="sideways").rotate(90)
```

## Working with Tags

Tags help organize documents in Paperless-NgX:

```python
# Get all tags
all_tags = client.tags.all()

# Create a new tag
new_tag = client.tags.create(
    name="Tax Documents",
    color="#00ff00",
    is_inbox_tag=False
)

# Get tag by ID
tax_tag = client.tags.get(5)

# Update a tag
tax_tag.color = "#ff0000"
tax_tag.save()

# Find documents with a specific tag
docs_with_tag = client.documents.filter(tags__id=tax_tag.id)

# Add a tag to a document
doc = client.documents.get(123)
doc.tags.append(tax_tag.id)
doc.save()

# Delete a tag
tax_tag.delete()
```

## Working with Correspondents

Correspondents represent people or organizations that send or receive documents:

```python
# Get all correspondents
all_correspondents = client.correspondents.all()

# Create a new correspondent
new_correspondent = client.correspondents.create(name="Electric Company")

# Get correspondent by ID
electric = client.correspondents.get(3)

# Update a correspondent
electric.name = "City Power & Light"
electric.matching_algorithm = "auto"
electric.match = "city power"
electric.save()

# Find documents from a specific correspondent
docs_from_electric = client.documents.filter(correspondent__id=electric.id)

# Delete a correspondent
electric.delete()
```

## Document Types

Document types categorize your documents:

```python
# Get all document types
all_types = client.document_types.all()

# Create a new document type
new_type = client.document_types.create(
    name="Invoice",
    matching_algorithm="auto",
    match="invoice"
)

# Get document type by ID
invoice_type = client.document_types.get(2)

# Update a document type
invoice_type.name = "Bill or Invoice"
invoice_type.save()

# Find documents of a specific type
invoices = client.documents.filter(document_type__id=invoice_type.id)

# Delete a document type
invoice_type.delete()
```

## Storage Paths

Storage paths control where documents are stored in Paperless-NgX:

```python
# Get all storage paths
all_paths = client.storage_paths.all()

# Create a new storage path
new_path = client.storage_paths.create(
    name="Tax Documents",
    path="/documents/taxes/"
)

# Get storage path by ID
tax_path = client.storage_paths.get(4)

# Update a storage path
tax_path.path = "/documents/finance/taxes/"
tax_path.save()

# Assign storage path to a document
doc = client.documents.get(123)
doc.storage_path = tax_path.id
doc.save()

# Delete a storage path
tax_path.delete()
```

## Custom Fields

Paperless-NgX supports custom fields for documents:

```python
# Get all custom fields
all_fields = client.custom_fields.all()

# Create a new custom field
date_field = client.custom_fields.create(
    name="Due Date",
    data_type="date"
)

string_field = client.custom_fields.create(
    name="Reference Number",
    data_type="string"
)

# Set custom field on a document
doc = client.documents.get(123)
doc.custom_fields = {
    date_field.id: "2023-04-15",
    string_field.id: "REF-12345"
}
doc.save()

# Query by custom field
docs_due_soon = client.documents.filter(**{
    f"custom_fields__{date_field.id}__lt": "2023-04-01"
})
```

## Saved Views

Saved views let you recall frequently used filters:

```python
# Get all saved views
all_views = client.saved_views.all()

# Create a new saved view
tax_view = client.saved_views.create(
    name="Tax Documents",
    show_on_dashboard=True,
    show_in_sidebar=True,
    filter_rules=[
        {"rule_type": "document_type", "value": "5"}
    ]
)

# Get a saved view by ID
view = client.saved_views.get(3)

# Update a saved view
view.filter_rules.append({"rule_type": "correspondent", "value": "7"})
view.save()

# Delete a saved view
view.delete()
```

## Tasks and Workflows

Interact with the Paperless-NgX task system:

```python
# Get running tasks
tasks = client.tasks.all()

# Get a specific task
task = client.tasks.get(5)
print(f"Task status: {task.status}")

# Wait for a task to complete and get the resulting document
document = client.tasks.wait_for_task(task_id)
print(f"Document {document.id} ready: {document.title}")

# Upload a series of documents asynchronously, then wait for all of them
task_ids = []
for i in range(10):
    task_id = client.documents.upload_async(f"doc_{i}.pdf", title=f"Document {i}")
    task_ids.append(task_id)
documents = client.tasks.wait_for_tasks(task_ids)

# Monitor tasks with callbacks
def on_task_success(task):
    print(f"Task {task.id} completed successfully")

def on_task_failure(task):
    print(f"Task {task.id} failed: {task.status_str}")

client.tasks.wait_for_task(
    task_id,
    success_callback=on_task_success,
    failure_callback=on_task_failure
)
```

## Advanced Features

### Using Signals

Paperap has a signal system that lets you hook into client events:

```python
from paperap.signals import SignalRegistry

# Connect to a signal
def on_document_save(document, **kwargs):
    print(f"Document {document.id} saved: {document.title}")

SignalRegistry.connect("document.save:success", on_document_save)

# Now this function will be called whenever a document is saved
doc = client.documents.get(123)
doc.title = "Updated Title"
doc.save()  # Will trigger on_document_save
```

### Asynchronous Operations

Paperap handles long-running operations asynchronously:

```python
# Start a document upload and get a task ID
task_id = client.documents.upload_async(
    "large_document.pdf",
    title="Large Document"
)

# Do other work while upload happens in background
print("Doing other work...")

# Wait for the task to complete when needed
document = client.tasks.wait_for_task(task_id)
print(f"Uploaded document: {document.title} (ID: {document.id})")

# Upload multiple documents in parallel
from pathlib import Path
import concurrent.futures

def upload_document(filepath):
    return client.documents.upload_async(filepath)

documents_dir = Path("documents_to_upload")
filepaths = list(documents_dir.glob("*.pdf"))

# Upload all documents in parallel (up to 5 at a time)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    task_ids = list(executor.map(upload_document, filepaths))

# Wait for all uploads to complete
documents = client.tasks.wait_for_tasks(task_ids)
print(f"Uploaded {len(documents)} documents")
```

### Using Plugins

Extend Paperap with custom plugins:

```python
from paperap.plugins.base import Plugin
from paperap.signals import SignalRegistry

class LoggingPlugin(Plugin):
    """Plugin that logs all API calls"""
    
    def __init__(self):
        super().__init__()
        SignalRegistry.connect("request:before", self.log_request)
        SignalRegistry.connect("request:after", self.log_response)
    
    def log_request(self, method, url, **kwargs):
        print(f"API Request: {method} {url}")
        return kwargs
    
    def log_response(self, response, **kwargs):
        print(f"API Response: {response.status_code}")
        return response

# Use the plugin
from paperap import PaperlessClient
client = PaperlessClient(plugins=[LoggingPlugin()])
```

See src/paperap/plugins/collect_test_data.py for an example plugin that intercepts API calls to save data for unit testing.

## Error Handling

Paperap provides detailed error information through a hierarchy of exception classes:

```python
from paperap.exceptions import PaperapError, ResourceNotFoundError, APIError

try:
    # Non-existent document
    doc = client.documents.get(99999)
except ResourceNotFoundError:
    print("Document not found")
except APIError as e:
    print(f"API Error: {e.status_code} - {e.detail}")
except PaperapError as e:
    # Base exception for all Paperap errors
    print(f"General error: {e}")

try:
    # Invalid operation
    client.documents.create(title="Test")  # Missing required file
except APIError as e:
    print(f"API Error: {e.status_code}")
    print(f"Error details: {e.detail}")
    print(f"API response: {e.response.text}")
```

## Pagination and Performance

Paperap uses lazy loading to efficiently handle large result sets:

```python
# Results are fetched only when needed
all_docs = client.documents.all()

# No API calls yet - just query definition
print("Query defined")

# First API call happens here - fetches only first page
for doc in all_docs[:25]:
    print(doc.title)

# Fetches next pages as needed
total = 0
for doc in all_docs:
    total += 1
print(f"Total processed: {total}")

# Limit results for performance
recent = client.documents.all().order_by("-created")[:100]
```
