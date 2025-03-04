"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    signals.py                                                                                           *
*        Project: paperap                                                                                            *
*        Created: 2025-03-02                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-02     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from collections import defaultdict
from enum import Enum, auto
from typing import Any, Callable, Optional, TypeVar, Generic, Set

T = TypeVar("T")


class SignalPriority(Enum):
    """Priority levels for signal handlers."""

    FIRST = auto()
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()
    LAST = auto()


class Signal(Generic[T]):
    """
    A signal that can be connected to and emitted.

    Handlers can be registered with a priority to control execution order.
    """

    name: str
    description: str
    _handlers: dict[SignalPriority, list[Callable[..., T]]]
    _disabled_handlers: Set[Callable[..., T]]

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._handlers = defaultdict(list)
        self._disabled_handlers = set()

    def connect(self, handler: Callable[..., T], priority: SignalPriority = SignalPriority.NORMAL) -> None:
        """
        Connect a handler to this signal.

        Args:
            handler: The handler function to be called when the signal is emitted.
            priority: The priority level for this handler.
        """
        self._handlers[priority].append(handler)

    def disconnect(self, handler: Callable[..., T]) -> None:
        """
        Disconnect a handler from this signal.

        Args:
            handler: The handler to disconnect.
        """
        for priority in self._handlers:
            if handler in self._handlers[priority]:
                self._handlers[priority].remove(handler)

    def emit(self, *args: Any, **kwargs: Any) -> list[T]:
        """
        Emit the signal, calling all connected handlers.

        Args:
            *args: Positional arguments to pass to handlers.
            **kwargs: Keyword arguments to pass to handlers.

        Returns:
            A list of results from all handlers.
        """
        results = []

        # Process handlers in priority order
        for priority in [
            SignalPriority.FIRST,
            SignalPriority.HIGH,
            SignalPriority.NORMAL,
            SignalPriority.LOW,
            SignalPriority.LAST,
        ]:
            for handler in self._handlers[priority]:
                if handler not in self._disabled_handlers:
                    results.append(handler(*args, **kwargs))

        return results

    def temporarily_disable(self, handler: Callable[..., T]) -> None:
        """Temporarily disable a handler without disconnecting it."""
        self._disabled_handlers.add(handler)

    def enable(self, handler: Callable[..., T]) -> None:
        """Re-enable a temporarily disabled handler."""
        if handler in self._disabled_handlers:
            self._disabled_handlers.remove(handler)


class SignalRegistry:
    """Registry of all signals in the application."""

    _instance = None
    _signals: dict[str, Signal]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SignalRegistry, cls).__new__(cls)
            cls._instance._signals = {}
        return cls._instance

    def register(self, signal: Signal) -> None:
        """Register a signal with the registry."""
        self._signals[signal.name] = signal

    def get(self, name: str) -> Optional[Signal]:
        """Get a signal by name."""
        return self._signals.get(name)

    def list_signals(self) -> list[str]:
        """List all registered signal names."""
        return list(self._signals.keys())


# Resource lifecycle signals
pre_list = Signal[dict[str, Any]]("pre_list", "Emitted before listing resources")
post_list_response = Signal[dict[str, Any]]("post_list_response", "Emitted after list response, before processing")
post_list_item = Signal[dict[str, Any]]("post_list_item", "Emitted for each item in a list response")
post_list = Signal[list[Any]]("post_list", "Emitted after listing resources")

pre_get = Signal[dict[str, Any]]("pre_get", "Emitted before getting a resource")
post_get = Signal[dict[str, Any]]("post_get", "Emitted after getting a resource")

pre_create = Signal[dict[str, Any]]("pre_create", "Emitted before creating a resource")
post_create = Signal[dict[str, Any]]("post_create", "Emitted after creating a resource")

pre_update = Signal[dict[str, Any]]("pre_update", "Emitted before updating a resource")
post_update = Signal[dict[str, Any]]("post_update", "Emitted after updating a resource")

pre_delete = Signal[dict[str, Any]]("pre_delete", "Emitted before deleting a resource")
post_delete = Signal[None]("post_delete", "Emitted after deleting a resource")

resource_signals: list[Signal] = [
    pre_list,
    post_list_response,
    post_list_item,
    post_list,
    pre_get,
    post_get,
    pre_create,
    post_create,
    pre_update,
    post_update,
    pre_delete,
    post_delete,
]

# Register all signals
registry = SignalRegistry()
for obj in resource_signals:
    registry.register(obj)
