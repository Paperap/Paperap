"""




----------------------------------------------------------------------------

   METADATA:

       File:    signals.py
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

from collections import defaultdict
from enum import Enum, StrEnum, auto
from typing import Any, Callable, Literal, Optional, Self, TypeAlias, TypeVar, Generic, Set, TypedDict
import logging

T = TypeVar("T")

logger = logging.getLogger(__name__)

class SignalPriority(Enum):
    """Priority levels for signal handlers."""

    FIRST = auto()
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()
    LAST = auto()

class SignalParams(TypedDict):
    name: str
    description: str

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

    def disable(self, handler: Callable[..., T]) -> None:
        """Temporarily disable a handler without disconnecting it."""
        self._disabled_handlers.add(handler)

    def enable(self, handler: Callable[..., T]) -> None:
        """Re-enable a temporarily disabled handler."""
        if handler in self._disabled_handlers:
            self._disabled_handlers.remove(handler)

class QueueType(TypedDict):
    connect : dict[str, set[tuple[Callable, SignalPriority]]]
    disconnect : dict[str, set[tuple[Callable, SignalPriority]]]
    disable : dict[str, set[tuple[Callable, SignalPriority]]]
    enable : dict[str, set[tuple[Callable, SignalPriority]]]

ActionType = Literal["connect", "disconnect", "disable", "enable"]

class SignalRegistry:
    """Registry of all signals in the application."""

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
        """Register a signal and process queued actions."""
        self = cls.get_instance()
        self._signals[signal.name] = signal

        # Process queued connections
        for handler, priority in self._queue["connect"].pop(signal.name, set()):
            signal.connect(handler, priority)

        # Process queued disconnections
        for handler, priority in self._queue["disconnect"].pop(signal.name, set()):
            signal.disconnect(handler)

        # Process queued disables
        for handler, priority in self._queue["disable"].pop(signal.name, set()):
            signal.disable(handler)

        # Process queued enables
        for handler, priority in self._queue["enable"].pop(signal.name, set()):
            signal.enable(handler)

    @classmethod
    def queue_action(cls, action: ActionType, name: str, handler: Callable[..., T], priority: SignalPriority | None = None) -> None:
        """Queue any signal-related action to be processed when the signal is registered."""
        self = cls.get_instance()
        if action not in self._queue:
            raise ValueError(f"Invalid queue action: {action}")

        priority = priority or SignalPriority.NORMAL
        self._queue[action].setdefault(name, set()).add((handler, priority))

    @classmethod
    def get(cls, name: str) -> Optional[Signal]:
        """Get a signal by name."""
        self = cls.get_instance()
        return self._signals.get(name)

    @classmethod
    def list_signals(cls) -> list[str]:
        """List all registered signal names."""
        self = cls.get_instance()
        return list(self._signals.keys())


    @classmethod
    def create(cls, name: str, description: str = "", return_type: type[T] | None = None) -> Signal:
        """Create and register a new signal."""
        signal = Signal[return_type](name, description)
        cls.register(signal)
        return signal

    @classmethod
    def emit(
        cls,
        name: str,
        description: str = "",
        *,
        return_type: type[T] | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> list[T]:
        """Emit a signal."""
        if not (signal := cls.get(name)):
            signal = cls.create(name, description, return_type)

        args = args or []
        kwargs = kwargs or {}
        return signal.emit(*args, **kwargs)

    @classmethod
    def connect(cls, name: str, handler: Callable[..., T], priority: SignalPriority = SignalPriority.NORMAL) -> None:
        """Connect a handler to a signal, or queue it if the signal is not yet registered."""
        if (signal := cls.get(name)):
            signal.connect(handler, priority)
        else:
            cls.queue_action("connect", name, handler, priority)

    @classmethod
    def disconnect(cls, name: str, handler: Callable[..., T]) -> None:
        """Disconnect a handler from a signal, or queue it if the signal is not yet registered."""
        if (signal := cls.get(name)):
            signal.disconnect(handler)
        else:
            cls.queue_action("disconnect", name, handler)

    @classmethod
    def disable(cls, name: str, handler: Callable[..., T]) -> None:
        """Temporarily disable a handler for a signal, or queue it if the signal is not yet registered."""
        if (signal := cls.get(name)):
            signal.disable(handler)
        else:
            cls.queue_action("disable", name, handler)

    @classmethod
    def enable(cls, name: str, handler: Callable[..., T]) -> None:
        """Enable a previously disabled handler, or queue it if the signal is not yet registered."""
        if (signal := cls.get(name)):
            signal.enable(handler)
        else:
            cls.queue_action("enable", name, handler)
