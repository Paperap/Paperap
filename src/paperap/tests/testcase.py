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
from typing import TYPE_CHECKING, Any, Callable, Iterator, TypeVar
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.resources import PaperlessResource
    from paperap.models import PaperlessModel
    from paperap.models.queryset import QuerySet

def load_sample_data(filename : str) -> dict[str, Any]:
	# Load sample response from tests/sample_data/{model}_{endpoint}.json
	sample_data_filepath = Path(__file__).parent.parent.parent.parent / "tests" / "sample_data" / filename
	with open(sample_data_filepath, "r") as f:
		text = f.read()
		sample_data = json.loads(text)
	return sample_data

_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel")

class TestCase(unittest.TestCase):
    client : "PaperlessClient"

    def _call_list_resource(self, resource : type["PaperlessResource[_PaperlessModel]"] | "PaperlessResource[_PaperlessModel]", **kwargs) -> QuerySet[_PaperlessModel]:
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).filter(**kwargs)
        return resource.filter(**kwargs)

    def _call_get_resource(self, resource : type["PaperlessResource[_PaperlessModel]"] | "PaperlessResource[_PaperlessModel]", id : int) -> _PaperlessModel:
        # If resource is a type, instantiate it
        if isinstance(resource, type):
            return resource(client=self.client).get(id)
        return resource.get(id)

    def list_resource(self, resource : type["PaperlessResource[_PaperlessModel]"] | "PaperlessResource[_PaperlessModel]", **kwargs) -> QuerySet[_PaperlessModel]:
        filename = f"{resource.name}_list.json"
        try:
            sample_data = load_sample_data(filename)
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                return self._call_list_resource(resource, **kwargs)
            
        except FileNotFoundError:
            return self._call_list_resource(resource, **kwargs)

    def get_resource(self, resource : type["PaperlessResource[_PaperlessModel]"] | "PaperlessResource[_PaperlessModel]", id : int) -> _PaperlessModel:
        filename = f"{resource.name}_item.json"
        try:
            sample_data = load_sample_data(filename)
            with patch("paperap.client.PaperlessClient.request") as request:
                request.return_value = sample_data
                return self._call_get_resource(resource, id)
        except FileNotFoundError:
            return self._call_get_resource(resource, id)