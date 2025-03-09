"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_signals.py
        Project: paperap
        Created: 2025-03-08
        Version: 0.0.2
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-08     By Jess Mann

"""
import unittest
from typing import Any, Dict
from paperap.signals import Signal, SignalPriority, SignalRegistry


class TestSignalSystem(unittest.TestCase):

    def setUp(self):
        # Reset the singleton for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")
        SignalRegistry.get_instance()  # Initialize the singleton

    def test_basic_signal_emit(self):
        # Simple transformation handler
        def add_field(data: Dict[str, Any], **kwargs) -> dict[str, Any]:
            data["added_field"] = "test"
            return data

        # Register a signal and connect a handler
        SignalRegistry.connect("test.signal", add_field)

        # Emit the signal
        initial_data = {"original": "data"}
        result = SignalRegistry.emit("test.signal", args=initial_data)

        # Verify the result
        self.assertIsInstance(result, dict, "Result is not a dictionary")
        self.assertEqual(result["original"], "data", "Original data was not preserved")
        self.assertEqual(result["added_field"], "test", "New field was not added")

    def test_priority_ordering(self):
        # Create handlers with different priorities
        results = []

        def first_handler(data, **kwargs):
            results.append("first")
            return data

        def second_handler(data, **kwargs):
            results.append("second")
            return data

        def third_handler(data, **kwargs):
            results.append("third")
            return data

        # Connect handlers with explicit priorities
        SignalRegistry.connect("priority.test", third_handler, SignalPriority.LOW)  # 75
        SignalRegistry.connect("priority.test", first_handler, SignalPriority.FIRST)  # 0
        SignalRegistry.connect("priority.test", second_handler, 30)  # Custom priority

        # Emit the signal
        SignalRegistry.emit("priority.test")

        # Verify execution order
        self.assertEqual(results, ["first", "second", "third"])

    def test_data_transformation_chain(self):
        # Create handlers that transform data
        def add_one(number, **kwargs):
            return number + 1

        def multiply_by_two(number, **kwargs):
            return number * 2

        def subtract_three(number, **kwargs):
            return number - 3

        # Connect handlers
        SignalRegistry.connect("transform", add_one, SignalPriority.FIRST)
        SignalRegistry.connect("transform", multiply_by_two, SignalPriority.NORMAL)
        SignalRegistry.connect("transform", subtract_three, SignalPriority.LAST)

        # Emit signal with initial value 5
        result = SignalRegistry.emit("transform", args=5)

        # Verify transformation: ((5 + 1) * 2) - 3 = 9
        self.assertEqual(result, 9)

    def test_additional_arguments(self):
        # Handler that uses additional arguments
        def format_with_context(data, **kwargs):
            model = kwargs.get("model")
            if model and hasattr(model, "name"):
                data["context"] = f"Processed by {model.name}"
            return data

        # Connect handler
        SignalRegistry.connect("with.context", format_with_context)

        # Create a simple model class
        class Model:
            def __init__(self, name):
                self.name = name

        model_instance = Model("TestModel")

        # Emit with data and model in kwargs
        data = {"original": "value"}
        result = SignalRegistry.emit(
            "with.context",
            return_type = dict[str, Any],
            args=data,
            kwargs={"model": model_instance}
        )

        # Verify result
        self.assertEqual(result["context"], "Processed by TestModel")

    def test_handler_disable_enable(self):
        # Create a handler
        def add_field(data, **kwargs):
            data["field"] = "value"
            return data

        # Connect the handler
        SignalRegistry.connect("toggle.test", add_field)

        # Normal execution
        result1 = SignalRegistry.emit("toggle.test", args={})
        self.assertEqual(result1["field"], "value")

        # Disable the handler
        SignalRegistry.disable("toggle.test", add_field)
        result2 = SignalRegistry.emit("toggle.test", args={})
        self.assertNotIn("field", result2)

        # Enable the handler again
        SignalRegistry.enable("toggle.test", add_field)
        result3 = SignalRegistry.emit("toggle.test", args={})
        self.assertEqual(result3["field"], "value")

    def test_queued_connection(self):
        # Connect to a signal that doesn't exist yet
        def transform(data, **kwargs):
            data["transformed"] = True
            return data

        SignalRegistry.connect("future.signal", transform)

        # Later, create and emit the signal
        result = SignalRegistry.emit("future.signal", "A signal created after connection", args={})

        # Verify the handler was properly connected
        self.assertTrue(result["transformed"])


if __name__ == "__main__":
    unittest.main()
