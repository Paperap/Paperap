"""




----------------------------------------------------------------------------

   METADATA:

       File:    signals.py
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

from __future__ import annotations

from collections import defaultdict
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Optional,
    Self,
    TypeAlias,
    TypeVar,
    Generic,
    Set,
    TypedDict,
    overload,
)
import logging

T = TypeVar("T")

logger = logging.getLogger(__name__)


class SignalPriority:
    """Priority levels for signal handlers."""

    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100


class SignalParams(TypedDict):
    name: str
    description: str


class Signal(Generic[T]):
    """
    A signal that can be connected to and emitted.

    Handlers can be registered with a priority to control execution order.
    Each handler receives the output of the previous handler as its first argument,
    enabling a filter/transformation chain.
    """

    name: str
    description: str
    _handlers: dict[int, list[Callable[..., T]]]
    _disabled_handlers: Set[Callable[..., T]]

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._handlers = defaultdict(list)
        self._disabled_handlers = set()

    def connect(self, handler: Callable[..., T], priority: int = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to this signal.

        Args:
            handler: The handler function to be called when the signal is emitted.
            priority: The priority level for this handler (lower numbers execute first).
        """
        self._handlers[priority].append(handler)

        # Check if the handler was temporarily disabled in the registry
        if handler in SignalRegistry._instance._queue["disable"].get(self.name, set()):
            self._disabled_handlers.add(handler)

    def disconnect(self, handler: Callable[..., T]) -> None:
        """
        Disconnect a handler from this signal.

        Args:
            handler: The handler to disconnect.
        """
        for priority in self._handlers:
            if handler in self._handlers[priority]:
                self._handlers[priority].remove(handler)

    @overload
    def emit(self, value: T | None, *args: Any, **kwargs: Any) -> T | None: ...

    @overload
    def emit(self, **kwargs: Any) -> T | None: ...

    def emit(self, *args: Any, **kwargs: Any) -> T | None:
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
        current_value: T | None = None
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
                    # print(f'Calling handler with: cv: {current_value}, remaining: {remaining_args}')
                    current_value = handler(current_value, *remaining_args, **kwargs)

        return current_value

    def disable(self, handler: Callable[..., T]) -> None:
        """
        Temporarily disable a handler without disconnecting it.

        Args:
            handler: The handler to disable.
        """
        self._disabled_handlers.add(handler)

    def enable(self, handler: Callable[..., T]) -> None:
        """
        Re-enable a temporarily disabled handler.

        Args:
            handler: The handler to enable.
        """
        if handler in self._disabled_handlers:
            self._disabled_handlers.remove(handler)


class QueueType(TypedDict):
    connect: dict[str, set[tuple[Callable, int]]]
    disconnect: dict[str, set[Callable]]
    disable: dict[str, set[Callable]]
    enable: dict[str, set[Callable]]


ActionType = Literal["connect", "disconnect", "disable", "enable"]


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
    _signals: dict[str, Signal]
    _queue: QueueType

    def __init__(self):
        self._signals = {}
        self._queue = {
            "connect": {},  # {signal_name: {(handler, priority), ...}}
            "disconnect": {},  # {signal_name: {handler, ...}}
            "disable": {},  # {signal_name: {handler, ...}}
            "enable": {},  # {signal_name: {handler, ...}}
        }

    @classmethod
    def get_instance(cls) -> Self:
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, signal: Signal) -> None:
        """
        Register a signal and process queued actions.

        Args:
            signal: The signal to register.
        """
        self = cls.get_instance()
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

    @classmethod
    def queue_action(
        cls, action: ActionType, name: str, handler: Callable[..., T], priority: int | None = None
    ) -> None:
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
        self = cls.get_instance()
        if action not in self._queue:
            raise ValueError(f"Invalid queue action: {action}")

        if action == "connect":
            priority = priority if priority is not None else SignalPriority.NORMAL
            self._queue[action].setdefault(name, set()).add((handler, priority))
        else:
            self._queue[action].setdefault(name, set()).add(handler)

    @classmethod
    def get(cls, name: str) -> Signal | None:
        """
        Get a signal by name.

        Args:
            name: The signal name.

        Returns:
            The signal instance, or None if not found.
        """
        self = cls.get_instance()
        return self._signals.get(name)

    @classmethod
    def list_signals(cls) -> list[str]:
        """
        List all registered signal names.

        Returns:
            A list of signal names.
        """
        self = cls.get_instance()
        return list(self._signals.keys())

    @classmethod
    def create(cls, name: str, description: str = "", return_type: type[T] | None = None) -> Signal:
        """
        Create and register a new signal.

        Args:
            name: Signal name
            description: Optional description for new signals
            return_type: Optional return type for new signals

        Returns:
            The new signal instance.
        """
        signal = Signal[return_type](name, description)
        cls.register(signal)
        return signal

    @classmethod
    @overload
    def emit(
        cls,
        name: str,
        description: str = "",
        *,
        return_type: type[T],
        args: T | tuple[T, *tuple[Any, ...]] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> T: ...

    @classmethod
    @overload
    def emit(
        cls,
        name: str,
        description: str = "",
        *,
        return_type: None = None,
        args: T | tuple[T, *tuple[Any, ...]],
        kwargs: dict[str, Any] | None = None,
    ) -> T: ...

    @classmethod
    @overload
    def emit(
        cls,
        name: str,
        description: str = "",
        *,
        return_type: None = None,
        args: None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None: ...

    @classmethod
    def emit(
        cls,
        name: str,
        description: str = "",
        *,
        return_type: type[T] | None = None,
        args: T | tuple[T, *tuple[Any, ...]] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> T | None:
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
        if not (signal := cls.get(name)):
            signal = cls.create(name, description, return_type)

        arg_tuple = (args,)
        kwargs = kwargs or {}
        # print(f'Calling signal with args: {arg_tuple} and kwargs: {kwargs}')
        return signal.emit(*arg_tuple, **kwargs)

    @classmethod
    def connect(cls, name: str, handler: Callable[..., T], priority: int = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to connect.
            priority: The priority level for this handler (lower numbers execute first
        """
        if signal := cls.get(name):
            signal.connect(handler, priority)
        else:
            cls.queue_action("connect", name, handler, priority)

    @classmethod
    def disconnect(cls, name: str, handler: Callable[..., T]) -> None:
        """
        Disconnect a handler from a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to disconnect.
        """
        if signal := cls.get(name):
            signal.disconnect(handler)
        else:
            cls.queue_action("disconnect", name, handler)

    @classmethod
    def disable(cls, name: str, handler: Callable[..., T]) -> None:
        """
        Temporarily disable a handler for a signal, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to disable
        """
        if signal := cls.get(name):
            signal.disable(handler)
        else:
            cls.queue_action("disable", name, handler)

    @classmethod
    def enable(cls, name: str, handler: Callable[..., T]) -> None:
        """
        Enable a previously disabled handler, or queue it if the signal is not yet registered.

        Args:
            name: The signal name.
            handler: The handler function to enable.
        """
        if signal := cls.get(name):
            signal.enable(handler)
        else:
            cls.queue_action("enable", name, handler)
