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
from enum import Enum, auto
from typing import Any, Callable, Optional, Self, TypeVar, Generic, Set, TypedDict
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
        if (self.name, handler) in SignalRegistry._instance._disable_queue:
            self.temporarily_disable(handler)
            
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

    _instance : Self
    _signals: dict[str, Signal]
    _connect_queue : list[tuple[str, Callable, SignalPriority]]
    _disable_queue : list[tuple[str, Callable]]

    def __new__(cls):
        if not hasattr(cls, '_instance') or cls._instance is None:
            cls._instance = super(SignalRegistry, cls).__new__(cls)
            cls._instance._signals = {}
        return cls._instance

    def register(self, signal: Signal) -> None:
        """Register a signal with the registry."""
        self._signals[signal.name] = signal

        for name, handler, priority in self._connect_queue:
            if name == signal.name:
                signal.connect(handler, priority)
                # Remove the handler from the queue
                self._connect_queue.remove((name, handler, priority))

    def queue_connect(self, name: str, handler: Callable[..., T], priority: SignalPriority = SignalPriority.NORMAL) -> None:
        """Queue a connection to a signal."""
        self._connect_queue.append((name, handler, priority))

    def queue_disable(self, name: str, handler: Callable[..., T]) -> None:
        """Queue a handler to be disabled."""
        self._disable_queue.append((name, handler))

    def get(self, name: str) -> Optional[Signal]:
        """Get a signal by name."""
        return self._signals.get(name)

    def list_signals(self) -> list[str]:
        """List all registered signal names."""
        return list(self._signals.keys())

    @classmethod
    def create(cls, name : str, description : str = "", return_type : type[T] | None = None) -> Signal:
        signal = Signal[return_type](name, description)
        cls._instance.register(signal)
        return signal

    @classmethod
    def emit(cls, name: str, description : str = "", *, return_type : type[T] | None = None, args: list[Any] | None = None, kwargs : dict[str, Any] | None = None) -> list[T]:
        if not (signal := cls._instance.get(name)):
            signal = cls.create(name, description, return_type)

        args = args or []
        kwargs = kwargs or {}
        return signal.emit(*args, **kwargs)

    @classmethod
    def connect(cls, name: str, handler: Callable[..., T], priority: SignalPriority = SignalPriority.NORMAL) -> None:
        if not (signal := cls._instance.get(name)):
            logger.error('Signal not found to connect to: %s', name)
            cls._instance.queue_connect(name, handler, priority)
            return

        signal.connect(handler, priority)

    @classmethod
    def disconnect(cls, name: str, handler: Callable[..., T]) -> None:
        if not (signal := cls._instance.get(name)):
            logger.error('Signal not found to disconnect from: %s', name)
            return

        signal.disconnect(handler)

    @classmethod
    def temporarily_disable(cls, name: str, handler: Callable[..., T]) -> None:
        if not (signal := cls._instance.get(name)):
            logger.debug('Signal not found to temporarily disable: %s', name)
            cls._instance.queue_disable(name, handler)
            return

        signal.temporarily_disable(handler)

    @classmethod
    def enable(cls, name: str, handler: Callable[..., T]) -> None:
        if not (signal := cls._instance.get(name)):
            logger.debug('Signal not found to enable: %s', name)
            # Remove it from the disable queue
            cls._instance._disable_queue = [(n, h) for n, h in cls._instance._disable_queue if n != name and h != handler]
            return

        signal.enable(handler)