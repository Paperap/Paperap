"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    testcase.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.1
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from __future__ import annotations
import json
from typing import Any, Iterator
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from paperap.models.queryset import QuerySet
from paperap.models.document import Document
from paperap.models.tag import Tag
from paperap.client import PaperlessClient

class TestCase(unittest.TestCase):
    pass

def load_sample_data(filename : str) -> dict[str, Any]:
	# Load sample response from tests/sample_data/documents_list.json
	sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
	with open(sample_data_filepath, "r") as f:
		text = f.read()
		sample_data = json.loads(text)
	return sample_data
