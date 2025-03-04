"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_from_dict.py
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
import os
from datetime import datetime, timezone
import types
from typing import Any, Iterable, get_type_hints, get_origin, get_args, Union
from unittest.mock import patch, MagicMock

from paperap.models.base import PaperlessModel
from paperap.resources.base import PaperlessResource
from paperap.models.correspondent import Correspondent
from paperap.models.custom_field import CustomField
from paperap.models.document import Document
from paperap.models.document_type import DocumentType
from paperap.models.log import Log
from paperap.models.mail_accounts import MailAccounts
from paperap.models.mail_rules import MailRules
from paperap.models.profile import Profile
from paperap.models.saved_view import SavedView
from paperap.models.share_links import ShareLinks
from paperap.models.storage_path import StoragePath
from paperap.models.tag import Tag
from paperap.models.task import Task
from paperap.models.ui_settings import UISettings
from paperap.models.user import Group, User
from paperap.models.workflow import Workflow, WorkflowAction, WorkflowTrigger

from paperap.tests import TestCase
from paperap.client import PaperlessClient


class TestModelFromDict(TestCase):
    model_to_resource : dict[type[PaperlessModel], PaperlessResource]
    def setUp(self):
        env_data = {'PAPERLESS_BASE_URL': 'http://localhost:8000', 'PAPERLESS_TOKEN': 'abc123'}
        with patch.dict(os.environ, env_data, clear=True):
            self.client = PaperlessClient()
        
        # Map model classes to their corresponding resources
        self.model_to_resource = {
            Correspondent: self.client.correspondents,
            CustomField: self.client.custom_fields,
            Document: self.client.documents,
            DocumentType: self.client.document_types,
            Log: self.client.logs,
            MailAccounts: self.client.mail_accounts,
            MailRules: self.client.mail_rules,
            Profile: self.client.profile,
            SavedView: self.client.saved_views,
            ShareLinks: self.client.share_links,
            StoragePath: self.client.storage_paths,
            Tag: self.client.tags,
            Task: self.client.tasks,
            UISettings: self.client.ui_settings,
            User: self.client.users,
            Group: self.client.groups,
            Workflow: self.client.workflows,
            WorkflowAction: self.client.workflow_actions,
            WorkflowTrigger: self.client.workflow_triggers,
        }

    def get_sample_value(self, type_hint):
        """Generate a sample value based on the type hint."""
        # Handle None or NoneType
        if type_hint is None or type_hint == type(None):
            return None
        
        # Handle Union types (like str | None)
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            # Use the first non-None type
            for arg in args:
                if arg is not type(None):
                    return self.get_sample_value(arg)
            return None
        
        # Handle basic types
        if type_hint == str:
            return "Sample String"
        elif type_hint == int:
            return 1
        elif type_hint == float:
            return 1.0
        elif type_hint == bool:
            return True
        elif type_hint == datetime:
            return "2025-01-01T12:00:00Z"  # Will be parsed by from_dict
        
        # Handle container types
        if origin == list:
            item_type = get_args(type_hint)[0]
            if item_type == int:
                return [1, 2, 3]
            else:
                return [self.get_sample_value(item_type)]
        if origin == dict:
            key_type, value_type = get_args(type_hint)
            return {self.get_sample_value(key_type): self.get_sample_value(value_type)} # type: ignore
        
        # Default fallback
        return None

    def generate_sample_data(self, model_class):
        """Generate sample data dictionary for a model class."""
        sample_data : dict[str, Any] = {"id": 1}  # Always include ID
        
        # Add standard timestamp fields common in Paperless models
        sample_data["created"] = "2025-01-01T12:00:00Z"
        sample_data["updated"] = "2025-01-02T12:00:00Z"
        
        # Try to get model fields from type hints
        try:
            hints = get_type_hints(model_class)
            for attr_name, type_hint in hints.items():
                # Skip dunder and private methods
                if attr_name.startswith('_'):
                    continue
                
                # Generate appropriate value based on type hint
                sample_data[attr_name] = self.get_sample_value(type_hint)
                
        except Exception:
            # Fallback with common fields if we can't get type hints
            common_fields = {
                "name": "Sample Name",
                "title": "Sample Title",
                "content": "Sample Content",
                "description": "Sample Description",
                "slug": "sample-slug",
                "enabled": True,
                "active": True,
                "tags": [1, 2, 3],
                "correspondent": 1,
                "document_type": 1,
                "storage_path": 1,
            }
            sample_data.update(common_fields)
            
        return sample_data

    def _get_model_fields(self, model : "PaperlessModel") -> dict[str, Iterable[type]]:
        """Get all fields in the model."""
        hints = get_type_hints(model)
        fields = {}

        for field, type_hint in hints.items():
            model_types = []
            # Handle Unions (both new syntax `int | None` and `Union[int, None]`)
            if isinstance(type_hint, types.UnionType) or getattr(type_hint, "__origin__", None) is Union:
                args = getattr(type_hint, "__args__", ())
                model_types.extend(args)
            else:
                model_types.append(type_hint)

            fields[field] = model_types

        return fields
        
    def test_all_models_from_dict(self):
        """Test from_dict for all models without hardcoding their attributes."""
        
        for model_class, resource in self.model_to_resource.items():
            model_name = model_class.__name__
            
            # Generate test data based on model's structure
            sample_data = self.generate_sample_data(model_class)
            
            # Test the from_dict method
            try:
                model = model_class.from_dict(sample_data, resource)
                model_fields = self._get_model_fields(model)
                
                # Test basic instance creation
                self.assertIsInstance(
                    model, 
                    model_class, 
                    f"Expected {model_name}, got {type(model)}"
                )
                
                # Test ID was set correctly
                if hasattr(model, 'id'):
                    self.assertEqual(
                        model.id, 
                        sample_data["id"], 
                        f"{model_name} id is wrong: {model.id}"
                    )
                
                # Test datetime fields were parsed correctly
                for date_field in ['created', 'updated', 'added']:
                    if hasattr(model, date_field) and date_field in sample_data:
                        field_value = getattr(model, date_field)
                        self.assertIsInstance(
                            field_value, 
                            datetime, 
                            f"{model_name}.{date_field} should be datetime, got {type(field_value)}"
                        )
                
                # Check a sample of other attributes
                for attr_name, expected_value in sample_data.items():
                    if attr_name not in ['id', 'created', 'updated', 'added'] and hasattr(model, attr_name):
                        # Check if the attribute is allowed to be None
                        field_types = model_fields[attr_name]
                        if type(None) in field_types:
                            continue
                        
                        actual_value = getattr(model, attr_name)
                        # Just verify the attribute exists and was set to something
                        self.assertIsNotNone(
                            actual_value, 
                            f"{model_name}.{attr_name} was not set correctly"
                        )
                        
            except Exception as e:
                self.fail(f"Failed to test {model_name}.from_dict: {str(e)}")
