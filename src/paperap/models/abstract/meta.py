"""




----------------------------------------------------------------------------

   METADATA:

       File:    meta.py
       Project: paperap
       Created: 2025-03-07
       Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-07     By Jess Mann

"""

from typing import TYPE_CHECKING, Iterable, Literal
from paperap.const import ModelStatus

if TYPE_CHECKING:
    from paperap.models.abstract import PaperlessModel


class StatusContext:
    """
    Context manager for safely updating model status.

    Attributes:
        model (SomeModel): The model whose status is being updated.
        new_status (ModelStatus): The status to set within the context.
        previous_status (ModelStatus): The status before entering the context.

    Examples:
        >>> class SomeModel(PaperlessModel):
        ...     def perform_update(self):
        ...         with StatusContext(self, ModelStatus.UPDATING):
        ...             # Perform an update
    """

    _model: "PaperlessModel"
    _new_status: ModelStatus
    _previous_status: ModelStatus | None

    @property
    def model(self) -> "PaperlessModel":
        """Read-only access to the model."""
        return self._model

    @property
    def new_status(self) -> ModelStatus:
        """Read-only access to the new status."""
        return self._new_status

    @property
    def previous_status(self) -> ModelStatus | None:
        """Read-only access to the previous status."""
        return self._previous_status

    def __init__(self, model: "PaperlessModel", new_status: ModelStatus):
        self._model = model
        self._new_status = new_status
        self._previous_status = None

    def __enter__(self):
        self._previous_status = self.model._meta.status
        self.model._meta.status = self.new_status
        # Do NOT return context manager, because we want to guarantee that the status is reverted
        # so we do not want to allow access to the context manager object

    def __exit__(self, exc_type, exc_value, traceback):
        if self.previous_status is not None:
            self.model._meta.status = self.previous_status
        else:
            self.model._meta.status = ModelStatus.ERROR
