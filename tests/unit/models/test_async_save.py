"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_async_save.py
        Project: paperap
        Created: 2025-03-15
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-15     By Jess Mann

"""
from typing import override
import unittest
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock, call, PropertyMock
from datetime import datetime

from pydantic.type_adapter import P
from pydantic.v1 import NoneBytes

from paperap.const import ModelStatus
from paperap.models.abstract.model import StandardModel
from paperap.models.abstract.meta import StatusContext
from paperap.exceptions import APIError, ResourceNotFoundError, RequestError
from pydantic import field_serializer
from unittest.mock import patch
from tests.lib import UnitTestCase
from paperap.models import StandardModel
from paperap.resources.base import StandardResource

class ExampleModel(StandardModel):
    """
    Example model for testing purposes.
    """
    name : str | None = None
    value : int | None = None
    a_date : datetime | None = None
    a_float : float | None = None
    a_bool : bool | None = None
    an_optional_str : str | None = None

    class Meta(StandardModel.Meta):
        save_on_write = True

    @field_serializer("a_date")
    def serialize_datetime(self, value: datetime | None, _info):
        return value.isoformat() if value else None
    
class ExampleResource(StandardResource[ExampleModel]):
    """
    Example resource for testing purposes.
    """
    name = "example"
    model_class = ExampleModel

    
class BaseTest(UnitTestCase[ExampleModel, ExampleResource]):
    """Test the asynchronous save functionality of StandardModel"""
    resource_class = ExampleResource
    model_type = ExampleModel
    
    @override
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        ExampleModel._meta.save_on_write = True

        # Create update method that returns a new instance
        def mock_update(model : ExampleModel):
            return model
            
        self.resource.update = mock_update
                
        # Create model instance
        self.model_data_unparsed = {
            'id': 1,
            'name': 'Original Name',
            'value': 42,
            'a_date': None,
            'a_float': 3.14,
            'a_bool': True,
            'an_optional_str': None
        }
        
        # Patch the sleep function to speed up tests
        self.sleep_patcher = patch('time.sleep', return_value=None)
        self.mock_sleep = self.sleep_patcher.start()
        self.addCleanup(self.sleep_patcher.stop)

class AsyncSaveTest(BaseTest):
    """Test the asynchronous save functionality of StandardModel"""

    @override
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.client.settings.save_on_write = True
        
        self.model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        self.addCleanup(self.model.cleanup)

    def test_original_data(self):
        """Test that original_data is set correctly"""
        self.assertEqual(self.model._meta.original_data, self.model_data_unparsed)

    def test_saved_data(self):
        """Test that saved_data is set correctly"""
        self.assertEqual(self.model._meta.saved_data, {})

    def test_save_updates_saved_data(self):
        """Test that save updates saved_data with current model state"""
        self.model.name = "New Name"
        self.model._perform_save()
        # Verify saved_data contains the new name
        self.assertEqual(self.model._meta.saved_data.get('name'), "New Name")

    def test_no_save_when_not_dirty(self):
        """Test that save doesn't do anything when model isn't dirty"""
        with patch.object(self.model, '_perform_save') as mock_perform_save:
            # Model is already clean from setUp
            self.model.save()
            mock_perform_save.assert_not_called()

    def test_save_emits_signals(self):
        """Test that save emits the appropriate signals"""
        with patch('paperap.signals.registry.emit') as mock_emit:
            self.model.name = "Signal Test"
            self.model._perform_save()
            # Verify before signal
            self.assertIn(call(
                "model.save:before",
                "Fired before the model data is sent to paperless ngx to be saved.",
                kwargs={'model': self.model, 'current_data': self.model.to_dict(include_read_only=False, exclude_none=False, exclude_unset=True)}
            ), mock_emit.call_args_list)

    def test_handle_save_result_updates_model(self):
        """Test that _handle_save_result updates the model with new data"""
        # Create a mock future
        future = concurrent.futures.Future()
        
        # Create a new model with updated data
        new_model = ExampleModel(resource=self.resource)
        new_model.id = 1
        new_model.name = "Result Name"
        new_model.value = 999
        
        # Set the future's result
        future.set_result(new_model)
        
        # Create a spy on update_locally
        with patch.object(self.model, 'update_locally') as mock_update_locally:
            self.model._handle_save_result(future)
            
            # Verify update_locally was called with the right parameters
            mock_update_locally.assert_called_once()
            call_kwargs = mock_update_locally.call_args[1]
            self.assertTrue(call_kwargs.get('from_db'))
            self.assertTrue(call_kwargs.get('skip_changed_fields'))
            self.assertEqual(call_kwargs.get('id'), 1)
            self.assertEqual(call_kwargs.get('name'), "Result Name")
            self.assertEqual(call_kwargs.get('value'), 999)

    def test_concurrent_attribute_changes(self):
        """Test handling of concurrent attribute changes during save"""
        # Setup a real asynchronous save that we can control
        original_update = self.resource.update
        
        update_event = threading.Event()
        save_started_event = threading.Event()
        
        # Replace update with a function that waits for a signal
        def delayed_update(model):
            print('delayed_update')
            # Signal that save has started
            save_started_event.set()
            # Wait for the test to signal it should proceed
            update_event.wait(timeout=5.0)
            # Then do the normal update
            return original_update(model)
            
        self.resource.update = delayed_update
        
        # Start a save in another thread
        self.model.name = "First Change"
        
        # Wait for save to start
        self.assertTrue(save_started_event.wait(timeout=5.0), "Save operation didn't start")
        
        # Now change an attribute while save is in progress
        self.model.value = 100
        
        # Let the save complete
        update_event.set()
        
        # Wait for the save to complete
        for _ in range(10):
            if self.model._pending_save is None or self.model._pending_save.done():
                break
            time.sleep(0.1)
        
        # Verify the result - the attribute change during save should be preserved
        self.assertEqual(self.model.name, "First Change")
        self.assertEqual(self.model.value, 100)
        
        # Clean up
        self.resource.update = original_update

    def test_error_handling_in_save(self):
        """Test error handling during save operation"""
        # Replace update with a function that raises an exception
        def failing_update(model):
            raise APIError("Test error")
            
        self.resource.update = failing_update
        
        # Set up signal spy
        with patch('paperap.signals.registry.emit') as mock_emit:
            # Trigger a save
            self.model.name = "Error Test"
            
            # Wait for the save to complete
            for _ in range(10):
                if self.model._pending_save is None or self.model._pending_save.done():
                    break
                time.sleep(0.1)
            
            # Verify error signal was emitted
            error_calls = [call for call in mock_emit.call_args_list 
                          if call[0][0] == "model.save:error"]
            self.assertTrue(error_calls, "Error signal wasn't emitted")
            
            # Verify the error was logged
            with self.assertLogs(level='ERROR') as log:
                # Force the future to run its callback if it hasn't already
                if self.model._pending_save:
                    for callback in self.model._pending_save._done_callbacks:
                        callback(self.model._pending_save)
                # Check log contents
                self.assertTrue(any("API error during save" in record.message for record in log.records))

    def test_timeout_handling(self):
        """Test handling of timeouts during save operation"""
        # Mock future.result to raise TimeoutError
        future = MagicMock()
        future.result.side_effect = concurrent.futures.TimeoutError()
        
        # Set up signal spy
        with patch('paperap.signals.registry.emit') as mock_emit:
            # Call the handler directly
            self.model._handle_save_result(future)
            
            # Verify timeout error signal was emitted
            timeout_calls = [call for call in mock_emit.call_args_list 
                            if call[0][0] == "model.save:error" and 
                               call[0][2]['kwargs']['error'] == "Timeout"]
            self.assertTrue(timeout_calls, "Timeout error signal wasn't emitted")

    def test_dirty_fields_doesnt_modify(self):
        """Test the different comparison modes of dirty_fields"""  
        # Calling dirty_fields doesn't modify data
        db_dirty = self.model.dirty_fields(comparison='db')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields(comparison='db')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields(comparison='saved')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields(comparison='saved')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields(comparison='both')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields(comparison='both')
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields()
        self.assertEqual(db_dirty, {})
        db_dirty = self.model.dirty_fields()
        self.assertEqual(db_dirty, {})
              
    def test_dirty_fields_db(self):
        # Update the model
        self.model.update_locally(name='Current', value=100)
        
        # Test 'db' comparison mode
        db_dirty = self.model.dirty_fields(comparison='db')
        self.assertIn('name', db_dirty)
        self.assertIn('value', db_dirty)
        self.assertEqual(db_dirty['name'], (self.model_data_unparsed['name'], 'Current'))
        self.assertEqual(db_dirty['value'], (self.model_data_unparsed['value'], 100))

    def test_dirty_fields_saved(self):
        # Update the model
        self.model.update_locally(name='Current', value=100)
        
        dirty = self.model.dirty_fields(comparison='saved')
        self.assertEqual(dirty, {})
        self.model._meta.saved_data = {**self.model_data_unparsed}
        self.model._meta.saved_data.update(name='BeforeSave', value=100)

        dirty = self.model.dirty_fields(comparison='saved')
        self.assertIn('name', dirty)
        self.assertNotIn('value', dirty)
        self.assertEqual(dirty['name'], ('BeforeSave', 'Current'))
        
        self.model._meta.saved_data.update(name='UpdatedName', value=200)
        
        dirty = self.model.dirty_fields(comparison='saved')
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], ('UpdatedName', 'Current'))
        self.assertEqual(dirty['value'], (200, 100))

    def test_dirty_fields_both(self):
        # Update the model
        self.model.update_locally(name='Current', value=100)
        
        dirty = self.model.dirty_fields(comparison='both')
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], (self.model_data_unparsed['name'], 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))

        self.model._meta.saved_data = {**self.model_data_unparsed}
        self.model._meta.saved_data.update(name='BeforeSave', value=100)
        
        dirty = self.model.dirty_fields(comparison='both')
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], ('Original Name', 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))

        self.model.update_locally(name='New Original Data')
        
        dirty = self.model.dirty_fields(comparison='both')
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], ('Original Name', 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))

    def test_dirty_fields_noparam(self):
        # Update the model
        self.model.update_locally(name='Current', value=100)
        
        dirty = self.model.dirty_fields()
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], (self.model_data_unparsed['name'], 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))

        self.model._meta.saved_data = {**self.model_data_unparsed}
        self.model._meta.saved_data.update(name='BeforeSave', value=100)
        
        dirty = self.model.dirty_fields()
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], ('Original Name', 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))

        self.model.update_locally(name='New Original Data')
        
        dirty = self.model.dirty_fields()
        self.assertIn('name', dirty)
        self.assertIn('value', dirty)
        self.assertEqual(dirty['name'], ('Original Name', 'Current'))
        self.assertEqual(dirty['value'], (self.model_data_unparsed['value'], 100))


class AsyncPatchTest(BaseTest):
    """Test the asynchronous save functionality of StandardModel that require patching"""

    @override
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.client.settings.save_on_write = True

    @patch('paperap.models.abstract.model.BaseModel.dirty_fields')
    def test_can_patch_model(self, mock_dirty_fields):
        """
        Patching pydantic models through patch.object is not working.
        """
        mock_dirty_fields.return_value = {'name': ('Original Name', 'BeforeSave')}
        model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        dirty_fields = model.dirty_fields()
        self.assertEqual(dirty_fields, {'name': ('Original Name', 'BeforeSave')})
        dirty_fields = model.dirty_fields(comparison='db')
        self.assertEqual(dirty_fields, {'name': ('Original Name', 'BeforeSave')})
        dirty_fields = model.dirty_fields(comparison='saved')
        self.assertEqual(dirty_fields, {'name': ('Original Name', 'BeforeSave')})
        dirty_fields = model.dirty_fields(comparison='both')
        self.assertEqual(dirty_fields, {'name': ('Original Name', 'BeforeSave')})

    @patch('paperap.models.abstract.model.BaseModel.dirty_fields')
    def test_skip_changed_fields(self, mock_dirty_fields):
        """Test that update_locally respects skip_changed_fields"""
        # Setup with some unsaved changes
        mock_dirty_fields.return_value = {'name': ('Original Name', 'BeforeSave')}
        model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
    
        # Update including the changed field
        model.update_locally(name='Value We Should Skip', value=200, skip_changed_fields=True)
        
        # The name should not have been updated, but value should be
        self.assertEqual(model.name, self.model_data_unparsed['name'])
        self.assertEqual(model.value, 200)

    @patch('paperap.models.abstract.model.StandardModel.save')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    def test_no_save_for_new_models(self, mock_is_new, mock_save):
        """Test that new models don't trigger auto-save"""
        mock_save.return_value = None
        mock_is_new.return_value = True
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        
        # Change an attribute
        new_model.name = "Changed"
        
        # Verify save wasn't called
        mock_save.assert_not_called()

    @patch('paperap.models.abstract.model.StandardModel.save')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    def test_no_save_on_update(self, mock_is_new, mock_save):
        """Test that new models don't trigger auto-save"""
        mock_save.return_value = None
        mock_is_new.return_value = False
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        new_model._meta.save_on_write = False
        
        # Change an attribute
        new_model.name = "Changed"
        
        # Verify save wasn't called
        mock_save.assert_not_called()

    @patch('paperap.models.abstract.model.StandardModel.save')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    def test_save_for_old_models(self, mock_is_new, mock_save):
        mock_save.return_value = None
        mock_is_new.return_value = False
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        
        # Change an attribute
        new_model.name = "Changed"
        
        # Verify save was called
        mock_save.assert_called_once()

    @patch('paperap.models.abstract.model.StandardModel.is_dirty')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    @patch('paperap.models.abstract.model.BaseModel.save_executor', new_callable=PropertyMock)
    def test_save_calls_executor(self, mock_save_executor, mock_is_new, mock_is_dirty):
        mock_is_dirty.return_value = True
        mock_is_new.return_value = False
        # Mock ThreadPoolExecutor behavior
        mock_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        mock_save_executor.return_value = mock_executor
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        
        # Try to save
        new_model.save()
        
        # Verify executor.submit was called once
        mock_save_executor.assert_called_once()

    @patch('paperap.models.abstract.model.StandardModel.is_dirty')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    @patch('paperap.models.abstract.model.BaseModel.save_executor', new_callable=PropertyMock)
    def test_no_duplicate_saves_while_saving(self, mock_save_executor, mock_is_new, mock_is_dirty):
        mock_is_dirty.return_value = True
        mock_is_new.return_value = False
        # Mock ThreadPoolExecutor behavior
        mock_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        mock_save_executor.return_value = mock_executor
        future = concurrent.futures.Future()
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        new_model._pending_save = future
        
        # Try to save
        new_model.save()
        
        # Verify executor.submit wasn't called
        mock_save_executor.assert_not_called()

    @patch('paperap.models.abstract.model.StandardModel.is_dirty')
    @patch('paperap.models.abstract.model.StandardModel.is_new')
    @patch('paperap.models.abstract.model.StandardModel._perform_save')
    def test_status_during_save(self, mock_perform_save, mock_is_new, mock_is_dirty):
        mock_is_dirty.return_value = True
        mock_is_new.return_value = False
        new_model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        original_status = new_model._meta.status
        self.assertNotEqual(original_status, ModelStatus.SAVING, "Test precondition failed")

        # Replace perform_save with a function that waits for a signal
        save_started_event = threading.Event()
        response_event = threading.Event()
        save_finished_event = threading.Event()
        def delayed_perform_save():
            print('delayed save')
            time.sleep(2)
            print('save started event')
            save_started_event.set()
            # Wait for the test to signal it should proceed
            print('waiting for response')
            response_event.wait(timeout=5.0)
            print('done waiting for response')
            time.sleep(5)
            save_finished_event.set()
            return None
        mock_perform_save.side_effect = delayed_perform_save
        
        # Try to save
        print('call save')
        new_model.save()

        # Wait for save to start
        print('waiting for save to start')
        self.assertTrue(save_started_event.wait(timeout=5.0), "Save operation didn't start")
        
        # Status should be SAVING
        print('CHECKING STATUS')
        self.assertEqual(new_model._meta.status, ModelStatus.SAVING)
        print('response event setting...')
        response_event.set()
        
        print('waiting for save to finish...')
        self.assertTrue(save_finished_event.wait(timeout=10), "Save operation didn't finish")  # ✅ Wait for completion

        # Status should reset
        print('comparing final')
        self.assertEqual(new_model._meta.status, ModelStatus.READY, "Status didn't change after save")

class AsyncTests(BaseTest):
    """Test the asynchronous save functionality of StandardModel"""

    @override
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.client.settings.save_on_write = True
        
        self.model = ExampleModel(resource=self.resource, **self.model_data_unparsed)
        self.addCleanup(self.model.cleanup)

    def test_status_during_save(self):
        """Test that model status is correctly set during save"""
        original_status = self.model._meta.status
        result = self.model._perform_save()
        
        # Status should be restored after save
        self.assertEqual(self.model._meta.status, original_status)
        
        # Simulate the entire save process with a real save
        self.model.name = "Status Test"
        
        # Wait for the save to complete
        for _ in range(10):
            if self.model._pending_save is None or self.model._pending_save.done():
                break
            time.sleep(0.1)
            
        # Final status should be READY
        self.assertEqual(self.model._meta.status, ModelStatus.READY)

    def test_cleanup_shuts_down_executor(self):
        """Test that cleanup properly shuts down the executor"""
        executor = self.model.save_executor
        with patch.object(executor, 'shutdown') as mock_shutdown:
            self.model.cleanup()
            mock_shutdown.assert_called_once_with(wait=True)

    def test_save_after_save_completes(self):
        """Test that changes during save are saved after the first save completes"""
        # Setup a real asynchronous save that we can control
        original_update = self.resource.update
        
        update_event = threading.Event()
        save_started_event = threading.Event()
        second_save_event = threading.Event()
        
        # Track number of updates
        update_count = [0]
        
        # Replace update with a function that waits for a signal
        def delayed_update(model):
            update_count[0] += 1
            
            if update_count[0] == 1:
                # First update
                save_started_event.set()
                update_event.wait()
            elif update_count[0] == 2:
                # Second update
                second_save_event.set()
                
            return original_update(model)
            
        self.resource.update = delayed_update
        
        # Start a save in another thread
        self.model.name = "First Save"
        
        # Wait for first save to start
        self.assertTrue(save_started_event.wait(timeout=1.0), "First save didn't start")
        
        # Make changes during the save
        self.model.value = 999
        
        # Let the first save complete
        update_event.set()
        
        # Wait for the second save to happen
        self.assertTrue(second_save_event.wait(timeout=1.0), "Second save didn't happen")
        
        # Verify both changes were saved
        self.assertEqual(self.model.name, "First Save")
        self.assertEqual(self.model.value, 999)
        self.assertEqual(update_count[0], 2)
        
        # Clean up
        self.resource.update = original_update


if __name__ == '__main__':
    unittest.main()
