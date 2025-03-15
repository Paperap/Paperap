"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    utils.py
        Project: paperap
        Created: 2025-03-12
        Version: 0.0.7
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-12     By Jess Mann

"""
from __future__ import annotations
import json
import os
from pathlib import Path
import random
import string
from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar
from unittest.mock import patch
from paperap.client import PaperlessClient

if TYPE_CHECKING:
    from paperap.resources import BaseResource

_BaseResource = TypeVar("_BaseResource", bound="BaseResource")

def defaults(defaults : dict[str, Any], **kwargs : Any) -> dict[str, Any]:
    """
    Merge default fields with overrides for hypothesis @example

    This avoids ugly double unpacking. The following two examples are equivalent:
	- @example(**defaults(v, field1="value1", field2="value2"))
	- @example(**{**v, "field1": "value1", "field2": "value2"})

	Examples:
		>>> from paperap.tests.utils import default as d
		>>> note = { "title": "Sample Title", "created": datetime.datetime.now() }
		>>> @example(**d(note, title="Note Title", content="Note Content"))
		>>> def test_create_note(note: dict[str, Any]): ...
    """
    return {**defaults, **kwargs}

def load_sample_data(filename : str) -> dict[str, Any]:
    """
    Load sample data from a JSON file.

    Args:
        filename: The name of the file to load.

    Returns:
        A dictionary containing the sample data.
    """
    # Load sample response from tests/sample_data/{model}_{endpoint}.json
    sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
    with open(sample_data_filepath, "r", encoding="utf-8") as f:
        text = f.read()
        sample_data = json.loads(text)
    return sample_data


def random_string(length=10):
    """Generate a random string with mixed characters."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_json():
    """Generate random JSON-like data."""
    return json.dumps({
        "id": random.randint(1, 10**9),
        "value": random.choice([None, random_string(15), 123, 3.14, True, {}, []])
    })

def create_client() -> PaperlessClient:
    # patch env
    env_data = {'PAPERLESS_BASE_URL': 'http://example.com', 'PAPERLESS_TOKEN': '40characterslong40characterslong40charac'}
    with patch.dict(os.environ, env_data, clear=True):
        return PaperlessClient()

def create_resource(resource : type[_BaseResource]) -> _BaseResource:
    client = create_client()
    return resource(client=client)
