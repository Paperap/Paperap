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
import os
from typing import TYPE_CHECKING, Any, Callable, Iterator, TypeVar
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from paperap.client import PaperlessClient

if TYPE_CHECKING:
    from paperap.resources import PaperlessResource
    from paperap.models import StandardModel
    from paperap.models.abstract import QuerySet

def load_sample_data(filename : str) -> dict[str, Any]:
	# Load sample response from tests/sample_data/{model}_{endpoint}.json
	sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
	with open(sample_data_filepath, "r") as f:
		text = f.read()
		sample_data = json.loads(text)
	return sample_data

_StandardModel = TypeVar("_StandardModel", bound="StandardModel")

class TestCase(unittest.TestCase):
    client : "PaperlessClient"
    mock_env : bool = False

    def setUp(self):
        self.setup_client()

    def setup_client(self):
        if not hasattr(self, "client") or not self.client:
            if self.mock_env:
                env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
                with patch.dict(os.environ, env_data, clear=True):
                    self.client = PaperlessClient()
            else:
                self.client = PaperlessClient()

    def _call_list_resource(self, resource : type["PaperlessResource[_StandardModel]"] | "PaperlessResource[_StandardModel]", **kwargs) -> QuerySet[_StandardModel]:
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).filter(**kwargs)
        return resource.filter(**kwargs)

    def _call_get_resource(self, resource : type["PaperlessResource[_StandardModel]"] | "PaperlessResource[_StandardModel]", id : int) -> _StandardModel:
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).get(id)
        return resource.get(id)

    def list_resource(self, resource : type["PaperlessResource[_StandardModel]"] | "PaperlessResource[_StandardModel]", **kwargs) -> QuerySet[_StandardModel]:
        filename = f"{resource.name}_list.json"
        try:
            sample_data = load_sample_data(filename)
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                qs = self._call_list_resource(resource, **kwargs)
                for _ in qs:
                    pass
                return qs

        except FileNotFoundError:
            return self._call_list_resource(resource, **kwargs)

    def get_resource(self, resource : type["PaperlessResource[_StandardModel]"] | "PaperlessResource[_StandardModel]", id : int) -> _StandardModel:
        filename = f"{resource.name}_item.json"
        try:
            sample_data = load_sample_data(filename)
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                return self._call_get_resource(resource, id)
        except FileNotFoundError:
            return self._call_get_resource(resource, id)
