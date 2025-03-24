"""
Provide context management for model status transitions.

The module implements a context manager that safely handles model status changes
during operations like saving or updating. It ensures proper status transitions
and resource locking to maintain data integrity throughout the lifecycle of
model operations.

Examples:
    Basic usage to temporarily change a model's status:

    >>> with StatusContext(model, ModelStatus.UPDATING):
    ...     # Perform operations that require the model to be in UPDATING status
    ...     model.update_field("value")

    Using StatusContext in a model method:

    >>> def save(self):
    ...     with StatusContext(self, ModelStatus.SAVING):
    ...         # Perform save operation
    ...         self._save_to_api()

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Literal

from paperap.const import ModelStatus

if TYPE_CHECKING:
    from paperap.models.abstract.model import BaseModel


class StatusContext:
    """
    Manage model status changes safely with proper resource locking.

    Provides a mechanism to temporarily change the status of a model
    while ensuring the previous status is restored upon completion.
    Handles acquisition and release of save locks to prevent concurrent
    modifications that could lead to data inconsistency.

    When used as a context manager, StatusContext will:
    1. Optionally acquire a save lock if the new status is SAVING
    2. Store the model's current status
    3. Set the model's status to the new status
    4. Execute the context body
    5. Restore the original status when exiting
    6. Release any acquired locks

    Attributes:
        model (BaseModel): The model whose status is being managed.
        new_status (ModelStatus): The status to set within the context.
        previous_status (ModelStatus | None): The status before entering the context.

    Examples:
        Using StatusContext in a model method:

        >>> class SomeModel(BaseModel):
        ...     def perform_update(self):
        ...         with StatusContext(self, ModelStatus.UPDATING):
        ...             # Perform an update operation
        ...             self._update_remote_data()

        Using StatusContext with error handling:

        >>> try:
        ...     with StatusContext(model, ModelStatus.SAVING):
        ...         # Attempt to save the model
        ...         model._save_to_api()
        ... except APIError:
        ...     # The model's status will be restored even if an error occurs
        ...     print("Failed to save model")

    """

    _model: "BaseModel"
    _new_status: ModelStatus
    _previous_status: ModelStatus | None
    _save_lock_acquired: bool = False

    @property
    def model(self) -> "BaseModel":
        """
        Get the model associated with this context.

        Returns:
            BaseModel: The model whose status is being managed.

        """
        return self._model

    @property
    def _model_meta(self) -> "BaseModel.Meta[Any]":
        """
        Get the model's metadata.

        Returns:
            BaseModel.Meta[Any]: The metadata associated with the model.

        """
        return self.model._meta  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    @property
    def new_status(self) -> ModelStatus:
        """
        Get the status that will be set within this context.

        Returns:
            ModelStatus: The status to set within the context.

        """
        return self._new_status

    @property
    def previous_status(self) -> ModelStatus | None:
        """
        Get the status that was set before entering this context.

        Returns:
            ModelStatus | None: The previous status, or None if not yet entered.

        """
        return self._previous_status

    def __init__(self, model: "BaseModel", new_status: ModelStatus) -> None:
        """
        Initialize the StatusContext with a model and target status.

        Args:
            model (BaseModel): The model whose status will be temporarily changed.
            new_status (ModelStatus): The status to set while in this context.

        """
        self._model = model
        self._new_status = new_status
        self._previous_status = None
        self._save_lock_acquired = False
        super().__init__()

    def save_lock(self) -> None:
        """
        Acquire the save lock for the model.

        Acquires the model's save lock to ensure that no other operations can
        modify the model while the status is being updated. The lock is implemented
        as a threading.RLock to allow reentrant locking from the same thread.

        Note:
            This method sets the internal _save_lock_acquired flag to True when
            successful, which is used to determine if unlock is needed later.

        """
        self.model._save_lock.acquire()  # type: ignore # allow protected access
        self._save_lock_acquired = True

    def save_unlock(self) -> None:
        """
        Release the save lock for the model.

        Releases the model's save lock if it was acquired by this context manager,
        allowing other operations to modify the model. The lock is only released
        if it was previously acquired by this specific StatusContext instance.

        Note:
            This method checks the internal _save_lock_acquired flag to ensure
            it only releases locks that it has acquired.

        """
        if self._save_lock_acquired:
            self.model._save_lock.release()  # type: ignore # allow protected access
            self._save_lock_acquired = False

    def __enter__(self) -> None:
        """
        Enter the context, updating the model's status.

        Performs the following operations:
        1. Acquires the save lock if the new status is ModelStatus.SAVING
        2. Stores the model's current status for later restoration
        3. Sets the model's status to the new status

        Note:
            This method intentionally returns None instead of self to prevent
            direct access to the context manager, ensuring proper status reversion.

        """
        # Acquire a save lock
        if self.new_status == ModelStatus.SAVING:
            self.save_lock()

        self._previous_status = self._model._status  # type: ignore # allow private access
        self._model._status = self.new_status  # type: ignore # allow private access

        # Do NOT return context manager, because we want to guarantee that the status is reverted
        # so we do not want to allow access to the context manager object

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Iterable[Any]) -> None:
        """
        Exit the context, restoring the model's previous status.

        Performs the following cleanup operations:
        1. Restores the model's status to its previous value
        2. Sets status to ModelStatus.ERROR if no previous status was recorded
        3. Releases the save lock if it was acquired

        Ensures proper cleanup even if an exception occurred within the context.

        Args:
            exc_type (type[BaseException] | None): The exception type, if any.
            exc_value (BaseException | None): The exception value, if any.
            traceback (Iterable[Any]): The traceback information, if any.

        Note:
            This method does not suppress exceptions; they will propagate normally.

        Examples:
            Handling exceptions while using StatusContext:

            >>> try:
            ...     with StatusContext(model, ModelStatus.PROCESSING):
            ...         raise ValueError("Something went wrong")
            ... except ValueError:
            ...     # The model's status will be restored before this exception handler runs
            ...     print("Error occurred, but model status was properly restored")

        """
        if self.previous_status is not None:
            self._model._status = self.previous_status  # type: ignore # allow private access
        else:
            self._model._status = ModelStatus.ERROR  # type: ignore # allow private access

        self.save_unlock()
