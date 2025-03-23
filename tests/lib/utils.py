
from __future__ import annotations

import json
import os
import random
import string
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from faker import Faker
from typing_extensions import TypeVar

from paperap.client import PaperlessClient

if TYPE_CHECKING:
    from paperap.resources import BaseResource

def defaults(defaults : dict[str, Any], **kwargs : Any) -> dict[str, Any]:
    """
    Merge default fields with overrides for hypothesis @example

    This avoids ugly double unpacking. The following two examples are equivalent:
    - @example(**defaults(v, field1="value1", field2="value2"))
    - @example(**{**v, "field1": "value1", "field2": "value2"})

    Examples:
    >>> from tests.lib.utils import default as d
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
    sample_data_filepath = Path(__file__).parent.parent / "sample_data" / filename
    with open(sample_data_filepath, "r", encoding="utf-8") as f:
        text = f.read()
        sample_data = json.loads(text)
    return sample_data

def create_client() -> PaperlessClient:
    # patch env
    env_data = {'PAPERLESS_BASE_URL': 'http://example.com', 'PAPERLESS_TOKEN': '40characterslong40characterslong40charac'}
    with patch.dict(os.environ, env_data, clear=True):
        return PaperlessClient()

def create_resource[R : BaseResource](resource : type[R]) -> R:
    client = create_client()
    return resource(client=client)
