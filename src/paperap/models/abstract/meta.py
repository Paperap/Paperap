"""
----------------------------------------------------------------------------

   METADATA:

       File:    meta.py
        Project: paperap
       Created: 2025-03-07
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-07     By Jess Mann

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Literal

from paperap.const import ModelStatus

if TYPE_CHECKING:
    from paperap.models.abstract.model import BaseModel


class StatusContext:
    """
    Context manager for safely updating model status.

    Attributes:
        model (SomeModel): The model whose status is being updated.
        new_status (ModelStatus): The status to set within the context.
        previous_status (ModelStatus): The status before entering the context.

    Examples:
        >>> class SomeModel(BaseModel):
        ...     def perform_update(self):
        ...         with StatusContext(self, ModelStatus.UPDATING):
        ...             # Perform an update

    """

    _model: "BaseModel"
    _new_status: ModelStatus
    _previous_status: ModelStatus | None
    _save_lock_acquired: bool = False

    @property
    def model(self) -> "BaseModel":
        """Read-only access to the model."""
        return self._model

    @property
    def _model_meta(self) -> "BaseModel.Meta[Any]":
        """Read-only access to the model's meta."""
        return self.model._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    @property
    def new_status(self) -> ModelStatus:
        """Read-only access to the new status."""
        return self._new_status

    @property
    def previous_status(self) -> ModelStatus | None:
        """Read-only access to the previous status."""
        return self._previous_status

    def __init__(self, model: "BaseModel", new_status: ModelStatus) -> None:
        self._model = model
        self._new_status = new_status
        self._previous_status = None
        super().__init__()

    def save_lock(self) -> None:
        """
        Acquire the save lock
        """
        # Trigger the self.model._save_lock (threading.RLock) to be acquired
        self.model._save_lock.acquire()  # type: ignore # allow protected access
        self._save_lock_acquired = True

    def save_unlock(self) -> None:
        """
        Release the save lock, only if this statuscontext previous acquired it.
        """
        # Release the self.model._save_lock (threading.RLock)
        if self._save_lock_acquired:
            self.model._save_lock.release()  # type: ignore # allow protected access

    def __enter__(self) -> None:
        # Acquire a save lock
        if self.new_status == ModelStatus.SAVING:
            self.save_lock()

        self._previous_status = self._model._status  # type: ignore # allow private access
        self._model._status = self.new_status  # type: ignore # allow private access

        # Do NOT return context manager, because we want to guarantee that the status is reverted
        # so we do not want to allow access to the context manager object

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Iterable[Any]
    ) -> None:
        if self.previous_status is not None:
            self._model._status = self.previous_status  # type: ignore # allow private access
        else:
            self._model._status = ModelStatus.ERROR  # type: ignore # allow private access

        self.save_unlock()
