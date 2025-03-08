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
    model : "PaperlessModel"
    new_status : ModelStatus
    previous_status : ModelStatus | None

    def __init__(self, model : "PaperlessModel", new_status: ModelStatus):
        self.model = model
        self.new_status = new_status
        self.previous_status = None

    def __enter__(self):
        self.previous_status = self.model._meta.status
        self.model._meta.status = self.new_status

    def __exit__(self, exc_type, exc_value, traceback):
        if self.previous_status is not None:
            self.model._meta.status = self.previous_status