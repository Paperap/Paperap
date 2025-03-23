
import unittest
from typing import Any, Dict, List, override

from paperap.signals import Signal, SignalPriority, SignalRegistry


class TestSignalSystem(unittest.TestCase):
    @override
    def setUp(self):
        # Reset the singleton for each test
        if hasattr(SignalRegistry, "_instance"):
            delattr(SignalRegistry, "_instance")
        self.registry = SignalRegistry.get_instance()  # Initialize the singleton

    def test_basic_signal_emit(self):
        # Simple transformation handler
        def add_field(data: dict[str, Any], **kwargs : Any) -> dict[str, Any]:
            data["added_field"] = "test"
            return data

        # Register a signal and connect a handler
        self.registry.connect("test.signal", add_field)

        # Emit the signal
        initial_data = {"original": "data"}
        result = self.registry.emit("test.signal", args=initial_data)

        # Verify the result
        self.assertIsInstance(result, dict, "Result is not a dictionary")
        self.assertEqual(result["original"], "data", "Original data was not preserved")
        self.assertEqual(result["added_field"], "test", "New field was not added")

    def test_priority_ordering(self):
        # Create handlers with different priorities
        results = []

        def first_handler(data, **kwargs : Any):
            results.append("first")
            return data

        def second_handler(data, **kwargs : Any):
            results.append("second")
            return data

        def third_handler(data, **kwargs : Any):
            results.append("third")
            return data

        # Connect handlers with explicit priorities
        self.registry.connect("priority.test", third_handler, SignalPriority.LOW)  # 75
        self.registry.connect("priority.test", first_handler, SignalPriority.FIRST)  # 0
        self.registry.connect("priority.test", second_handler, 30)  # Custom priority

        # Emit the signal
        self.registry.emit("priority.test")

        # Verify execution order
        self.assertEqual(results, ["first", "second", "third"])

    def test_data_transformation_chain(self):
        # Create handlers that transform data
        def add_one(number, **kwargs : Any):
            return number + 1

        def multiply_by_two(number, **kwargs : Any):
            return number * 2

        def subtract_three(number, **kwargs : Any):
            return number - 3

        # Connect handlers
        self.registry.connect("transform", add_one, SignalPriority.FIRST)
        self.registry.connect("transform", multiply_by_two, SignalPriority.NORMAL)
        self.registry.connect("transform", subtract_three, SignalPriority.LAST)

        # Emit signal with initial value 5
        result = self.registry.emit("transform", args=5)

        # Verify transformation: ((5 + 1) * 2) - 3 = 9
        self.assertEqual(result, 9)

    def test_additional_arguments(self):
        # Handler that uses additional arguments
        def format_with_context(data, **kwargs : Any):
            model = kwargs.get("model")
            if model and hasattr(model, "name"):
                data["context"] = f"Processed by {model.name}"
            return data

        # Connect handler
        self.registry.connect("with.context", format_with_context)

        # Create a simple model class
        class Model:
            @override
            def __init__(self, name):
                self.name = name
                super().__init__()

        model_instance = Model("TestModel")

        # Emit with data and model in kwargs
        data = {"original": "value"}
        result = self.registry.emit(
            "with.context",
            return_type = dict[str, Any],
            args=data,
            kwargs={"model": model_instance}
        )

        # Verify result
        self.assertEqual(result["context"], "Processed by TestModel")

    def test_handler_disable_enable(self):
        # Create a handler
        def add_field(data, **kwargs : Any):
            data["field"] = "value"
            return data

        # Connect the handler
        self.registry.connect("toggle.test", add_field)

        # Normal execution
        result1 = self.registry.emit("toggle.test", args={})
        self.assertEqual(result1["field"], "value")

        # Disable the handler
        self.registry.disable("toggle.test", add_field)
        result2 = self.registry.emit("toggle.test", args={})
        self.assertNotIn("field", result2)

        # Enable the handler again
        self.registry.enable("toggle.test", add_field)
        result3 = self.registry.emit("toggle.test", args={})
        self.assertEqual(result3["field"], "value")

    def test_queued_connection(self):
        # Connect to a signal that doesn't exist yet
        def transform(data, **kwargs : Any):
            data["transformed"] = True
            return data

        self.registry.connect("future.signal", transform)

        # Later, create and emit the signal
        result = self.registry.emit("future.signal", "A signal created after connection", args={})

        # Verify the handler was properly connected
        self.assertTrue(result["transformed"])

    def test_direct_signal_creation(self):
        """Test creating a Signal directly and registering it."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create a signal directly
        signal = Signal[dict[str, Any]]("direct.signal", "A directly created signal")

        # Register it with the registry
        self.registry.register(signal)

        # Connect a handler
        def add_field(data, **kwargs: Any):
            data["direct"] = True
            return data

        signal.connect(add_field)

        # Emit the signal
        result = signal.emit({"original": "data"})
        assert result is not None # make mypy happy

        # Verify the result
        self.assertTrue(result["direct"])
        self.assertEqual(result["original"], "data")

        # Verify it's in the registry
        self.assertIn("direct.signal", self.registry.list_signals())

    def test_signal_disconnect(self):
        """Test disconnecting a handler from a signal."""
        # Create handlers
        def add_field1(data, **kwargs: Any):
            data["field1"] = True
            return data

        def add_field2(data, **kwargs: Any):
            data["field2"] = True
            return data

        # Connect handlers
        self.registry.connect("disconnect.test", add_field1)
        self.registry.connect("disconnect.test", add_field2)

        # Emit with both handlers
        result1 = self.registry.emit("disconnect.test", args={})
        self.assertTrue(result1["field1"])
        self.assertTrue(result1["field2"])

        # Disconnect one handler
        self.registry.disconnect("disconnect.test", add_field1)

        # Emit again
        result2 = self.registry.emit("disconnect.test", args={})
        self.assertNotIn("field1", result2)
        self.assertTrue(result2["field2"])

        # Disconnect all handlers
        self.registry.disconnect("disconnect.test", add_field2)
        result3 = self.registry.emit("disconnect.test", args={})
        self.assertEqual(result3, {})

    def test_list_signals(self):
        """Test listing all registered signals."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create several signals
        self.registry.emit("signal1", "First test signal")
        self.registry.emit("signal2", "Second test signal")
        self.registry.emit("signal3", "Third test signal")

        # Get the list of signals
        signals = self.registry.list_signals()

        # Verify all signals are in the list
        self.assertIn("signal1", signals)
        self.assertIn("signal2", signals)
        self.assertIn("signal3", signals)

    def test_get_signal(self):
        """Test getting a signal by name."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create a signal
        self.registry.emit("get.test", "A signal to retrieve")

        # Get the signal
        signal = self.registry.get("get.test")

        # Verify it's the right signal
        self.assertIsNotNone(signal)
        assert signal is not None # make mypy happy
        self.assertEqual(signal.name, "get.test")
        self.assertEqual(signal.description, "A signal to retrieve")

        # Try getting a non-existent signal
        nonexistent = self.registry.get("nonexistent.signal")
        self.assertIsNone(nonexistent)

    def test_queue_actions(self):
        """Test queuing actions for signals that don't exist yet."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create handlers
        def handler1(data, **kwargs: Any):
            return data

        def handler2(data, **kwargs: Any):
            return data

        # Queue various actions
        self.registry.connect("future.queue", handler1, SignalPriority.HIGH)
        self.registry.disable("future.queue", handler1)
        self.registry.connect("future.queue", handler2)
        self.registry.disconnect("future.queue", handler2)

        # Check if actions are queued - use function id for comparison instead of direct equality
        handler1_id = id(handler1)
        # For connect, we need to check the first element of the tuple
        self.assertTrue(
            any(id(h) == handler1_id for h, _ in self.registry._queue["connect"]["future.queue"]), # type: ignore
            f"Handler1 not queued for connect: {self.registry._queue['connect'].__repr__()}" # type: ignore
        )
        # For disable, we directly check the handler
        self.assertTrue(
            any(id(h) == handler1_id for h in self.registry._queue["disable"]["future.queue"]), # type: ignore
            f"Handler1 not queued for disable: {self.registry._queue['disable'].__repr__()}" # type: ignore
        )
        # For enable, we check if it's not there
        self.assertFalse(
            "future.queue" in self.registry._queue.get("enable", {}) and # type: ignore
            any(id(h) == handler1_id for h in self.registry._queue["enable"].get("future.queue", set())), # type: ignore
            f"Handler1 queued for enable: {self.registry._queue.get('enable', {}).__repr__()}" # type: ignore
        )

        # Create the signal - this should process the queue
        _signal = self.registry.create("future.queue", "A signal with queued actions")

        # Verify queue was processed
        self.assertFalse(self.registry.is_queued("connect", "future.queue", handler1))
        self.assertFalse(self.registry.is_queued("disable", "future.queue", handler1))

    def test_invalid_queue_action(self):
        """Test that invalid queue actions raise ValueError."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        def handler(data, **kwargs: Any):
            return data

        # Try to queue an invalid action
        with self.assertRaises(ValueError):
            self.registry.queue_action("invalid_action", "test.signal", handler) # type: ignore

    def test_emit_with_no_args(self):
        """Test emitting a signal with no args."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create a handler that doesn't need args
        results = []

        def simple_handler(data, **kwargs: Any):
            results.append("called")
            return data

        # Connect and emit
        self.registry.connect("no.args", simple_handler)
        self.registry.emit("no.args")

        # Verify handler was called
        self.assertEqual(results, ["called"])

    def test_emit_with_return_type(self):
        """Test emitting a signal with explicit return type."""
        # TODO: AI Generated Test. Will remove this note when it is reviewed.
        # Create a handler that returns a list
        def list_handler(data: list[str], **kwargs: Any) -> list[str]:
            data.append("item")
            return data

        # Connect and emit with return_type
        self.registry.connect("typed.signal", list_handler)
        result = self.registry.emit(
            "typed.signal",
            return_type=list[str],
            args=["initial"]
        )

        # Verify result
        self.assertEqual(result, ["initial", "item"])

if __name__ == "__main__":
    unittest.main()
