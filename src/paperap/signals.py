"""
Signal system for Paperap.

This module provides a flexible signal/event system that allows components to communicate
without direct dependencies. It supports prioritized handlers, handler chains, and
temporary handler disabling.

The signal system is designed around a singleton registry that manages all signals
and their handlers. Signals can be created, connected to, and emitted through this registry.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Self,
    TypeAlias,
    TypedDict,
    TypeVar,
    final,
    overload,
)

logger = logging.getLogger(__name__)


class QueueType(TypedDict):
    """
    A type used by SignalRegistry for storing queued signal actions.

    This dictionary stores handlers that are registered before their signals
    are created, allowing for flexible registration order.

    Attributes:
        connect: Maps signal names to sets of (handler, priority) tuples.
        disconnect: Maps signal names to sets of handlers to disconnect.
        disable: Maps signal names to sets of handlers to disable.
        enable: Maps signal names to sets of handlers to enable.

    """

    connect: dict[str, set[tuple[Callable[..., Any], int]]]
    disconnect: dict[str, set[Callable[..., Any]]]
    disable: dict[str, set[Callable[..., Any]]]
    enable: dict[str, set[Callable[..., Any]]]


ActionType = Literal["connect", "disconnect", "disable", "enable"]


@final
class SignalPriority:
    """
    Priority levels for signal handlers.

    These constants define standard priority levels for signal handlers.
    Lower numbers execute first, allowing precise control over handler execution order.

    Attributes:
        FIRST: Execute before all other handlers.
        HIGH: Execute with high priority.
        NORMAL: Default priority level.
        LOW: Execute with low priority.
        LAST: Execute after all other handlers.

    """

    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100


class SignalParams(TypedDict):
    """
    A type used by SignalRegistry for storing signal parameters.

    Attributes:
        name: The name of the signal.
        description: A description of the signal's purpose.

    """

    name: str
    description: str


class Signal[_ReturnType]:
    """
    A signal that can be connected to and emitted.

    Handlers can be registered with a priority to control execution order.
    Each handler receives the output of the previous handler as its first argument,
    enabling a filter/transformation chain. This allows handlers to modify data
    as it passes through the chain.

    Attributes:
        name: The unique name of this signal.
        description: A human-readable description of the signal's purpose.
        _handlers: Dictionary mapping priority levels to lists of handler functions.
        _disabled_handlers: Set of temporarily disabled handler functions.

    Example:
        >>> signal = Signal("document.save")
        >>> def log_save(doc, **kwargs):
        ...     print(f"Saving document: {doc.title}")
        ...     return doc
        >>> signal.connect(log_save)
        >>> signal.emit(document)

    """

    name: str
    description: str
    _handlers: dict[int, list[Callable[..., _ReturnType]]]
    _disabled_handlers: set[Callable[..., _ReturnType]]

    def __init__(self, name: str, description: str = "") -> None:
        """
        Initialize a new signal.

        Args:
            name: The unique name of this signal.
            description: A human-readable description of the signal's purpose.

        """
        self.name = name
        self.description = description
        self._handlers = defaultdict(list)
        self._disabled_handlers = set()
        super().__init__()

    def connect(self, handler: Callable[..., _ReturnType], priority: int = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to this signal.

        Args:
            handler: The handler function to be called when the signal is emitted.
                The function should accept the transformed value as its first argument,
                and return the further transformed value.
            priority: The priority level for this handler (lower numbers execute first).
                Use SignalPriority constants for standard levels.

        Example:
            >>> def transform_document(doc, **kwargs):
            ...     doc.title = doc.title.upper()
            ...     return doc
            >>> signal.connect(transform_document, SignalPriority.HIGH)

        """
        self._handlers[priority].append(handler)

        # Check if the handler was temporarily disabled in the registry
        if SignalRegistry.get_instance().is_queued("disable", self.name, handler):
            self._disabled_handlers.add(handler)

    def disconnect(self, handler: Callable[..., _ReturnType]) -> None:
        """
        Disconnect a handler from this signal.

        Args:
            handler: The handler to disconnect. The handler will no longer be called
                when the signal is emitted.

        Example:
            >>> signal.disconnect(transform_document)

        """
        for priority in self._handlers:
            if handler in self._handlers[priority]:
                self._handlers[priority].remove(handler)

    @overload
    def emit(self, value: _ReturnType | None, *args: Any, **kwargs: Any) -> _ReturnType | None: ...

    @overload
    def emit(self, **kwargs: Any) -> _ReturnType | None: ...

    def emit(self, *args: Any, **kwargs: Any) -> _ReturnType | None:
        """
        Emit the signal, calling all connected handlers in priority order.

        Each handler receives the output of the previous handler as its first argument.
        Other arguments are passed unchanged. This creates a transformation chain
        where each handler can modify the data before passing it to the next handler.

        Args:
            *args: Positional arguments to pass to handlers. The first argument
                is the value that will be transformed through the handler chain.
            **kwargs: Keyword arguments to pass to all handlers.

        Returns:
            The final result after all handlers have processed the data.

        Example:
            >>> # Transform a document through multiple handlers
            >>> transformed_doc = signal.emit(document, user="admin")

        """
        current_value: _ReturnType | None = None
        remaining_args = args
        if args:
            # Start with the first argument as the initial value
            current_value = args[0]
            remaining_args = args[1:]

        # Get all priorities in ascending order (lower numbers execute first)
        priorities = sorted(self._handlers.keys())

        # Process handlers in priority order
        for priority in priorities:
            for handler in self._handlers[priority]:
                if handler not in self._disabled_handlers:
                    # Pass the current value as the first argument, along with any other args
                    current_value = handler(current_value, *remaining_args, **kwargs)

        return current_value

    def disable(self, handler: Callable[..., _ReturnType]) -> None:
        """
        Temporarily disable a handler without disconnecting it.

        Disabled handlers remain connected but are skipped during signal emission.
        This is useful for temporarily suspending a handler's execution without
        losing its registration.

        Args:
            handler: The handler to disable.

        Example:
            >>> signal.disable(log_save)  # Temporarily stop logging

        """
        self._disabled_handlers.add(handler)

    def enable(self, handler: Callable[..., _ReturnType]) -> None:
        """
        Re-enable a temporarily disabled handler.

        Args:
            handler: The handler to enable. If the handler wasn't disabled,
                this method has no effect.

        Example:
            >>> signal.enable(log_save)  # Resume logging

        """
        if handler in self._disabled_handlers:
            self._disabled_handlers.remove(handler)


class SignalRegistry:
    """
    Registry of all signals in the application.

    This singleton class manages all signals in the application, providing
    a central point for creating, connecting to, and emitting signals.

    The registry also handles queuing of signal actions when signals are
    connected to before they are created, ensuring that handlers are properly
    registered regardless of initialization order.

    Attributes:
        _instance: The singleton instance of this class.
        _signals: Dictionary mapping signal names to Signal instances.
        _queue: Dictionary of queued actions for signals not yet created.

    Examples:
        >>> # Emit a signal with keyword arguments
        >>> SignalRegistry.emit(
        ...     "document.save:success",
        ...     "Fired when a document has been saved successfully",
        ...     kwargs = {"document": document}
        ... )

        >>> # Emit a signal that transforms data
        >>> filtered_data = SignalRegistry.emit(
        ...     "document.save:before",
        ...     "Fired before a document is saved. Optionally filters the data that will be saved.",
        ...     args = (data,),
        ...     kwargs = {"document": document}
        ... )

        >>> # Connect a handler to a signal
        >>> def log_document_save(document, **kwargs):
        ...     print(f"Document saved: {document.title}")
        ...     return document
        >>> SignalRegistry.connect("document.save:success", log_document_save)

    """

    _instance: Self
    _signals: dict[str, Signal[Any]]
    _queue: QueueType

    def __init__(self) -> None:
        """Initialize the signal registry."""
        self._signals = {}
        self._queue = {
            "connect": {},  # {signal_name: {(handler, priority), ...}}
            "disconnect": {},  # {signal_name: {handler, ...}}
            "disable": {},  # {signal_name: {handler, ...}}
            "enable": {},  # {signal_name: {handler, ...}}
        }
        super().__init__()

    def __new__(cls) -> Self:
        """
        Ensure that only one instance of the class is created (singleton pattern).

        Returns:
            The singleton instance of this class.

        """
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Self:
        """
        Get the singleton instance of this class.

        This method ensures that only one instance of SignalRegistry exists
        throughout the application.

        Returns:
            The singleton instance of this class.

        """
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance  # type: ignore # mypy issue with Self return type

    def register(self, signal: Signal[Any]) -> None:
        """
        Register a signal and process any queued actions for it.

        This method registers a signal with the registry and processes any
        actions (connect, disconnect, etc.) that were queued for this signal
        before it was created.

        Args:
            signal: The signal to register.

        """
        self._signals[signal.name] = signal

        # Process queued connections
        for handler, priority in self._queue["connect"].pop(signal.name, set()):
            signal.connect(handler, priority)

        # Process queued disconnections
        for handler in self._queue["disconnect"].pop(signal.name, set()):
            signal.disconnect(handler)

        # Process queued disables
        for handler in self._queue["disable"].pop(signal.name, set()):
            signal.disable(handler)

        # Process queued enables
        for handler in self._queue["enable"].pop(signal.name, set()):
            signal.enable(handler)

    def queue_action(self, action: ActionType, name: str, handler: Callable[..., Any], priority: int | None = None) -> None:
        """
        Queue a signal-related action to be processed when the signal is registered.

        This method allows actions to be queued for signals that haven't been
        created yet, ensuring that handlers can be registered in any order.

        Args:
            action: The action to queue (connect, disconnect, disable, enable).
            name: The signal name.
            handler: The handler function to queue.
            priority: The priority level for this handler (only for connect action).

        Raises:
            ValueError: If the action is invalid.

        Example:
            >>> registry.queue_action("connect", "document.save", log_handler, SignalPriority.HIGH)

        """
        if action not in self._queue:
            raise ValueError(f"Invalid queue action: {action}")

        if action == "connect":
            # If it's in the disconnect queue, remove it
            priority = priority if priority is not None else SignalPriority.NORMAL
            self._queue[action].setdefault(name, set()).add((handler, priority))
        else:
            # For non-connect actions, just add the handler without priority
            self._queue[action].setdefault(name, set()).add(handler)

    def get(self, name: str) -> Signal[Any] | None:
        """
        Get a signal by name.

        Args:
            name: The signal name.

        Returns:
            The signal instance, or None if not found.

        Example:
            >>> signal = registry.get("document.save:success")
            >>> if signal:
            ...     signal.emit(document)

        """
        return self._signals.get(name)

    def list_signals(self) -> list[str]:
        """
        List all registered signal names.

        Returns:
            A list of signal names.

        Example:
            >>> signals = registry.list_signals()
            >>> print(f"Available signals: {', '.join(signals)}")

        """
        return list(self._signals.keys())

    def create[R](self, name: str, description: str = "", return_type: type[R] | None = None) -> Signal[R]:
        """
        Create and register a new signal.

        This method creates a new signal with the given name and description,
        registers it with the registry, and processes any queued actions for it.

        Args:
            name: Signal name. Should be unique and descriptive.
            description: Optional description for the new signal.
            return_type: Optional return type for the new signal.

        Returns:
            The new signal instance.

        Example:
            >>> save_signal = registry.create(
            ...     "document.save:success",
            ...     "Fired when a document has been saved successfully"
            ... )

        """
        signal = Signal[R](name, description)
        self.register(signal)
        return signal

    @overload
    def emit[_ReturnType](
        self,
        name: str,
        description: str = "",
        *,
        return_type: type[_ReturnType],
        args: _ReturnType | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> _ReturnType: ...

    @overload
    def emit[_ReturnType](
        self,
        name: str,
        description: str = "",
        *,
        return_type: None = None,
        args: _ReturnType,
        kwargs: dict[str, Any] | None = None,
    ) -> _ReturnType: ...

    @overload
    def emit(
        self,
        name: str,
        description: str = "",
        *,
        return_type: None = None,
        args: None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None: ...

    def emit[_ReturnType](
        self,
        name: str,
        description: str = "",
        *,
        return_type: type[_ReturnType] | None = None,
        args: _ReturnType | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> _ReturnType | None:
        """
        Emit a signal, calling handlers in priority order.

        This method emits a signal with the given name, creating it if it doesn't
        exist. Each handler in the signal's chain receives the output of the previous
        handler as its first argument, allowing for data transformation.

        Args:
            name: Signal name. If the signal doesn't exist, it will be created.
            description: Optional description for new signals.
            return_type: Optional return type for new signals.
            args: The value to be transformed through the handler chain.
            kwargs: Keyword arguments passed to all handlers.

        Returns:
            The transformed value after all handlers have processed it.

        Example:
            >>> # Transform document data through a handler chain
            >>> processed_data = registry.emit(
            ...     "document.process",
            ...     "Process document data before saving",
            ...     args=document_data,
            ...     kwargs={"user": current_user}
            ... )

        """
        if not (signal := self.get(name)):
            signal = self.create(name, description, return_type)

        arg_tuple = (args,)
        kwargs = kwargs or {}
        return signal.emit(*arg_tuple, **kwargs)

    def connect(self, name: str, handler: Callable[..., Any], priority: int = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to a signal, or queue it if the signal is not yet registered.

        This method connects a handler function to a signal with the given name.
        If the signal doesn't exist yet, the connection is queued and will be
        established when the signal is created.

        Args:
            name: The signal name.
            handler: The handler function to connect.
            priority: The priority level for this handler (lower numbers execute first).
                Use SignalPriority constants for standard levels.

        Example:
            >>> def log_document_save(document, **kwargs):
            ...     print(f"Document saved: {document.title}")
            ...     return document
            >>> registry.connect("document.save:success", log_document_save)

        """
        if signal := self.get(name):
            signal.connect(handler, priority)
        else:
            self.queue_action("connect", name, handler, priority)

    def disconnect(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Disconnect a handler from a signal, or queue it if the signal is not yet registered.

        This method disconnects a handler function from a signal with the given name.
        If the signal doesn't exist yet, the disconnection is queued and will be
        processed when the signal is created.

        Args:
            name: The signal name.
            handler: The handler function to disconnect.

        Example:
            >>> registry.disconnect("document.save:success", log_document_save)

        """
        if signal := self.get(name):
            signal.disconnect(handler)
        else:
            self.queue_action("disconnect", name, handler)

    def disable(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Temporarily disable a handler for a signal, or queue it if the signal is not yet registered.

        This method temporarily disables a handler function for a signal with the given name.
        The handler remains connected but will be skipped during signal emission.
        If the signal doesn't exist yet, the disable action is queued.

        Args:
            name: The signal name.
            handler: The handler function to disable.

        Example:
            >>> # Temporarily disable logging during bulk operations
            >>> registry.disable("document.save:success", log_document_save)

        """
        if signal := self.get(name):
            signal.disable(handler)
        else:
            self.queue_action("disable", name, handler)

    def enable(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Enable a previously disabled handler, or queue it if the signal is not yet registered.

        This method re-enables a previously disabled handler function for a signal.
        If the signal doesn't exist yet, the enable action is queued.

        Args:
            name: The signal name.
            handler: The handler function to enable.

        Example:
            >>> # Re-enable logging after bulk operations
            >>> registry.enable("document.save:success", log_document_save)

        """
        if signal := self.get(name):
            signal.enable(handler)
        else:
            self.queue_action("enable", name, handler)

    def is_queued(self, action: ActionType, name: str, handler: Callable[..., Any]) -> bool:
        """
        Check if a handler is queued for a signal action.

        This method checks if a specific handler is queued for a specific action
        on a signal that hasn't been created yet.

        Args:
            action: The action to check (connect, disconnect, disable, enable).
            name: The signal name.
            handler: The handler function to check.

        Returns:
            True if the handler is queued for the specified action, False otherwise.

        Example:
            >>> is_queued = registry.is_queued("disable", "document.save", log_handler)
            >>> print(f"Handler is {'queued for disabling' if is_queued else 'not queued'}")

        """
        for queued_handler in self._queue[action].get(name, set()):
            # Handle "connect" case where queued_handler is a tuple (handler, priority)
            if isinstance(queued_handler, tuple):
                if queued_handler[0] == handler:
                    return True
            elif queued_handler == handler:
                return True
        return False


# Create a singleton instance of the registry for global use
registry = SignalRegistry.get_instance()
