# Usage

## Basic Usage

```python
from paperap import PaperlessClient
from paperap.settings import Settings

# Initialize the client with your Paperless-ngx instance settings
client = PaperlessClient(
    Settings(
        host="http://localhost:8000",
        token="your_api_token"
    )
)

# Get all documents
documents = client.documents.all()

# Filter documents
pdf_docs = client.documents.filter(mime_type="application/pdf")

# Get a specific document by ID
doc = client.documents.get(1)

# Download a document
doc.download("my_document.pdf")
```

## Working with Documents

```python
# Create a new document (upload a file)
with open("example.pdf", "rb") as f:
    doc = client.documents.upload(
        file=f,
        title="Example Document",
        correspondent=1,  # ID of correspondent
        document_type=2,  # ID of document type
    )

# Update a document
doc.title = "Updated Title"
doc.save()

# Delete a document
doc.delete()
```

## Working with Other Resources

```python
# Get all correspondents
correspondents = client.correspondents.all()

# Create a new correspondent
new_correspondent = client.correspondents.create(
    name="Example Company"
)

# Get all tags
tags = client.tags.all()

# Create a new tag
new_tag = client.tags.create(
    name="Important",
    color="#ff0000"
)
```
