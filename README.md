# Paperap

**Python library for interacting with the Paperless NGX REST API**

## Overview

Paperap (pronounced like "paperwrap") is a Python client library for interacting with the [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx) REST API. It provides an object-oriented interface for managing documents, tags, correspondents, and other resources within Paperless-NGX.

## Status

The library is in active development, and is not ready for production use.

## Features

- Authentication via API token or username/password
- Object-oriented interface with lazy-loaded querysets
- Pagination and filtering support
- Strongly typed models with Pydantic
- Intended to be easily integrated with existing Python applications

## Installation

```sh
pip install paperap
```

## Quick Start

### Creating a Client

#### Using API Token:

```python
from paperap import PaperlessClient

client = PaperlessClient(
    base_url="https://paperless.example.com",
    token="your-token"
)
```

#### Using Username and Password:

```python
client = PaperlessClient(
    base_url="https://paperless.example.com",
    username="user",
    password="pass"
)
```

#### Loading Settings from Environment Variables:

Set the following environment variables:

- `PAPERLESS_BASE_URL`
- `PAPERLESS_TOKEN` or both `PAPERLESS_USERNAME` and `PAPERLESS_PASSWORD`

Then create a client without arguments:

```python
client = PaperlessClient()
```

## Working with Documents

### Listing Documents:

```python
for doc in client.documents.all():
    print(doc.title)
```

### Filtering Documents:

```python
docs = client.documents.filter(title__contains="invoice")
for doc in docs:
    print(doc.title)
```

### Getting a Single Document:

```python
doc = client.documents.get(123)
print(doc.title)
```

## Tags, Correspondents, and Other Resources

The same interface applies to other resources like tags, correspondents, and document types:

```python
for tag in client.tags.all():
    print(tag.name)
```

## Error Handling

Paperap raises exceptions for API errors:

- `PaperlessError` - Base exception
- `APIError` - Error when contacting the Paperless NGX API
- `AuthenticationError` - Error when authentication fails
- `ObjectNotFoundError` - Error when a single object is requested but not found
- `MultipleObjectsFoundError` - Error when a single object is requested but multiple objects are found

```python
from paperap.exceptions import APIError

try:
    doc = client.documents.get(9999)  # Nonexistent document
except ObjectNotFoundError as e:
    print(f"Error: {e}")
```

## Contributing

I welcome contributions! Please open an issue or submit a pull request on GitHub.

Run tests with either of the following cli commands:

```sh
bun run test
uv run python -m unittest discover -s tests
```

Setup dev environment:

```sh
uv venv
source .venv/bin/activate
uv sync --all-groups
```

Setup env vars:

```sh
cp env-sample .env
```

Run pre-commit:

```sh
pre-commit run --all-files
```

## License

Paperap is released under the MIT License.

## Author

**Jess Mann** - [jess@jmann.me](mailto:jess@jmann.me)

## Related Projects

- [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx)
- [pypaperless](https://github.com/tb1337/paperless-api) - async client that is more mature