"""



----------------------------------------------------------------------------

METADATA:

File:    signals.py
        Project: paperap
Created: 2025-03-09
        Version: 0.0.9
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-09     By Jess Mann

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

    Any int can be provided, but these are the recommended values.
    """

    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100


class SignalParams(TypedDict):
    """
    A type used by SignalRegistry for storing signal parameters.
    """

    name: str
    description: str


class Signal[_ReturnType]:
    """
    A signal that can be connected to and emitted.

    Handlers can be registered with a priority to control execution order.
    Each handler receives the output of the previous handler as its first argument,
    enabling a filter/transformation chain.
    """

    name: str
    description: str
    _handlers: dict[int, list[Callable[..., _ReturnType]]]
    _disabled_handlers: set[Callable[..., _ReturnType]]

    def __init__(self, name: str, description: str = "") -> None:
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
            priority: The priority level for this handler (lower numbers execute first).

        """
        self._handlers[priority].append(handler)

        # Check if the handler was temporarily disabled in the registry
        if SignalRegistry.get_instance().is_queued("disable", self.name, handler):
            self._disabled_handlers.add(handler)

    def disconnect(self, handler: Callable[..., _ReturnType]) -> None:
        """
        Disconnect a handler from this signal.

        Args:
            handler: The handler to disconnect.

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
        Other arguments are passed unchanged.

        Args:
            *args: Positional arguments to pass to handlers.
            **kwargs: Keyword arguments to pass to handlers.

        Returns:
            The final result after all handlers have processed the data.

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

        Args:
            handler: The handler to disable.

        """
        self._disabled_handlers.add(handler)

    def enable(self, handler: Callable[..., _ReturnType]) -> None:
        """
        Re-enable a temporarily disabled handler.

        Args:
            handler: The handler to enable.

        """
        if handler in self._disabled_handlers:
            self._disabled_handlers.remove(handler)


class SignalRegistry:
    """
    Registry of all signals in the application.

    Signals can be created, connected to, and emitted through the registry.

    Examples:
        >>> SignalRegistry.emit(
        ...     "document.save:success",
        ...     "Fired when a document has been saved successfully",
        ...     kwargs = {"document": document}
        ... )

        >>> filtered_data = SignalRegistry.emit(
        ...     "document.save:before",
        ...     "Fired before a document is saved. Optionally filters the data that will be saved.",
        ...     args = (data,),
        ...     kwargs = {"document": document}
        ... )

        >>> SignalRegistry.connect("document.save:success", my_handler)

    """

    _instance: Self
    _signals: dict[str, Signal[Any]]
    _queue: QueueType

    def __init__(self) -> None:
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
        Ensure that only one instance of the class is created.

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

        Returns:
            The singleton instance of this class.

        """
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance  # type: ignore # mypy issue with Self return type

    def register(self, signal: Signal[Any]) -> None:
        """
        Register a signal and process queued actions.

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
        Queue any signal-related action to be processed when the signal is registered.

        Args:
            action: The action to queue (connect, disconnect, disable, enable).
            name: The signal name.
            handler: The handler function to queue.
            priority: The priority level for this handler (only for connect action).

        Raises:
            ValueError: If the action is invalid.

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

        """
        return self._signals.get(name)

    def list_signals(self) -> list[str]:
        """
        List all registered signal names.

        Returns:
            A list of signal names.

        """
        return list(self._signals.keys())

    def create[R](self, name: str, description: str = "", return_type: type[R] | None = None) -> Signal[R]:
        """
        Create and register a new signal.

        Args:
            name: Signal name
            description: Optional description for new signals
            return_type: Optional return type for new signals

        Returns:
            The new signal instance.

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

        Each handler transforms the first argument and passes it to the next handler.

        Args:
            name: Signal name
            description: Optional description for new signals
            return_type: Optional return type for new signals
            args: List of positional arguments (first one is transformed through the chain)
            kwargs: Keyword arguments passed to all handlers

        Returns:
            The transformed first argument after all handlers have processed it

        """
        if not (signal := self.get(name)):
            signal = self.create(name, description, return_type)

        arg_tuple = (args,)
        kwargs = kwargs or {}
        return signal.emit(*arg_tuple, **kwargs)

    def connect(self, name: str, handler: Callable[..., Any], priority: int = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to connect.
            priority: The priority level for this handler (lower numbers execute first

        """
        if signal := self.get(name):
            signal.connect(handler, priority)
        else:
            self.queue_action("connect", name, handler, priority)

    def disconnect(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Disconnect a handler from a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to disconnect.

        """
        if signal := self.get(name):
            signal.disconnect(handler)
        else:
            self.queue_action("disconnect", name, handler)

    def disable(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Temporarily disable a handler for a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to disable

        """
        if signal := self.get(name):
            signal.disable(handler)
        else:
            self.queue_action("disable", name, handler)

    def enable(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Enable a previously disabled handler, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to enable.

        """
        if signal := self.get(name):
            signal.enable(handler)
        else:
            self.queue_action("enable", name, handler)

    def is_queued(self, action: ActionType, name: str, handler: Callable[..., Any]) -> bool:
        """
        Check if a handler is queued for a signal action.

        Args:
            action: The action to check (connect, disconnect, disable, enable).
            name: The signal name.
            handler: The handler function to check.

        Returns:
            True if the handler is queued, False otherwise.

        """
        for queued_handler in self._queue[action].get(name, set()):
            # Handle "connect" case where queued_handler is a tuple (handler, priority)
            if isinstance(queued_handler, tuple):
                if queued_handler[0] == handler:
                    return True
            elif queued_handler == handler:
                return True
        return False


registry = SignalRegistry.get_instance()
