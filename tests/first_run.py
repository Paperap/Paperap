"""

Create sample data in a new testing environment. This data will (ideally)
persist between integration tests.

You must set env vars for the new test environment.

 ----------------------------------------------------------------------------

    METADATA:

        File:    setup.py
        Project: paperap
        Created: 2025-03-20
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-20     By Jess Mann

"""
from typing import Any
from pathlib import Path
import json
from paperap.client import PaperlessClient
from paperap.models import (
    Correspondent,
    Document,
    DocumentType,
    Tag
)
from paperap.exceptions import PaperapError

def load_sample_data(filename : str) -> dict[str, Any]:
    """
    Load sample data from a JSON file.

    Args:
        filename: The name of the file to load.

    Returns:
        A dictionary containing the sample data.

    """
    # Load sample response from tests/sample_data/{model}_{endpoint}.json
    sample_data_filepath = Path(__file__).parent / "sample_data" / filename
    with open(sample_data_filepath, "r", encoding="utf-8") as f:
        text = f.read()
        sample_data = json.loads(text)
    return sample_data

def cleanup():
    client = PaperlessClient()
    try:
        correspondent_data = load_sample_data("correspondents_item.json")
        client.correspondents.delete(correspondent_data['id'])
    except PaperapError:
        pass
    try:
        document_type_data = load_sample_data("document_types_item.json")
        client.document_types.delete(document_type_data['id'])
    except PaperapError:
        pass
    try:
        tag_data = load_sample_data("tags_item.json")
        client.tags.delete(tag_data['id'])
    except PaperapError:
        pass
    
    
def upload():
    # Setup the testing environment by inserting some test data
    client = PaperlessClient()
    correspondent_data = load_sample_data("correspondents_item.json")
    correspondent = Correspondent.create(**correspondent_data)

    document_type_data = load_sample_data("document_types_item.json")
    document_type = DocumentType.create(**document_type_data)

    tag_data = load_sample_data("tags_item.json")
    tag = Tag.create(**tag_data)

def main():
    cleanup()
    upload()

if __name__ == "__main__":
    main()
