"""
----------------------------------------------------------------------------

   METADATA:

       File:    base.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import concurrent.futures
import logging
import threading
import time
import types
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, Self, TypedDict, cast, override

import pydantic
from pydantic import Field, PrivateAttr
from typing_extensions import TypeVar

from paperap.const import FilteringStrategies, ModelStatus
from paperap.exceptions import APIError, ConfigurationError, ReadOnlyFieldError, RequestError, ResourceNotFoundError
from paperap.models.abstract.meta import StatusContext
from paperap.signals import registry

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.resources.base import BaseResource, StandardResource

logger = logging.getLogger(__name__)


class ModelConfigType(TypedDict):
    populate_by_name: bool
    validate_assignment: bool
    validate_default: bool
    use_enum_values: bool
    extra: Literal["ignore"]
    arbitrary_types_allowed: bool


BASE_MODEL_CONFIG: ModelConfigType = {
    "populate_by_name": True,
    "validate_assignment": True,
    "validate_default": True,
    "use_enum_values": True,
    "extra": "ignore",
    "arbitrary_types_allowed": True,
}


class BaseModel(pydantic.BaseModel, ABC):
    """
    Base model for all Paperless-ngx API objects.

    Provides automatic serialization, deserialization, and API interactions
    with minimal configuration needed.

    Attributes:
        _meta: Metadata for the model, including filtering and resource information.
        _save_lock: Lock for saving operations.
        _pending_save: Future object for pending save operations.

    Raises:
        ValueError: If resource is not provided.

    """

    _meta: ClassVar["Meta[Self]"]
    _save_lock: threading.RLock = PrivateAttr(default_factory=threading.RLock)
    _pending_save: concurrent.futures.Future[Any] | None = PrivateAttr(default=None)
    _save_executor: concurrent.futures.ThreadPoolExecutor | None = None
    # Updating attributes will not trigger save()
    _status: ModelStatus = ModelStatus.INITIALIZING  # The last data we retrieved from the db
    # this is used to calculate if the model is dirty
    _original_data: dict[str, Any] = {}
    # The last data we sent to the db to save
    # This is used to determine if the model has been changed in the time it took to perform a save
    _saved_data: dict[str, Any] = {}
    _resource: "BaseResource[Self]"

    class Meta[_Self: "BaseModel"]:
        """
        Metadata for the Model.

        Attributes:
            name: The name of the model.
            read_only_fields: Fields that should not be modified.
            filtering_disabled: Fields disabled for filtering.
            filtering_fields: Fields allowed for filtering.
            supported_filtering_params: Params allowed during queryset filtering.
            blacklist_filtering_params: Params disallowed during queryset filtering.
            filtering_strategies: Strategies for filtering.
            resource: The BaseResource instance.
            queryset: The type of QuerySet for the model.

        Raises:
            ValueError: If both ALLOW_ALL and ALLOW_NONE filtering strategies are set.

        """

        model: type[_Self]
        # The name of the model.
        # It will default to the classname
        name: str
        # Fields that should not be modified. These will be appended to read_only_fields for all parent classes.
        read_only_fields: ClassVar[set[str]] = set()
        # Fields that are disabled by Paperless NGX for filtering.
        # These will be appended to filtering_disabled for all parent classes.
        filtering_disabled: ClassVar[set[str]] = set()
        # Fields allowed for filtering. Generated automatically during class init.
        filtering_fields: ClassVar[set[str]] = set()
        # If set, only these params will be allowed during queryset filtering. (e.g. {"content__icontains", "id__gt"})
        # These will be appended to supported_filtering_params for all parent classes.
        supported_filtering_params: ClassVar[set[str]] = {"limit"}
        # If set, these params will be disallowed during queryset filtering (e.g. {"content__icontains", "id__gt"})
        # These will be appended to blacklist_filtering_params for all parent classes.
        blacklist_filtering_params: ClassVar[set[str]] = set()
        # Strategies for filtering.
        # This determines which of the above lists will be used to allow or deny filters to QuerySets.
        filtering_strategies: ClassVar[set[FilteringStrategies]] = {FilteringStrategies.BLACKLIST}
        # A map of field names to their attribute names.
        # Parser uses this to transform input and output data.
        # This will be populated from all parent classes.
        field_map: dict[str, str] = {}
        # If true, updating attributes will trigger save(). If false, save() must be called manually
        # True or False will override client.settings.save_on_write (PAPERLESS_SAVE_ON_WRITE)
        # None will respect client.settings.save_on_write
        save_on_write: bool | None = None
        save_timeout: int = PrivateAttr(default=60)  # seconds

        __type_hints_cache__: dict[str, type] = {}

        def __init__(self, model: type[_Self]):
            self.model = model

            # Validate filtering strategies
            if all(x in self.filtering_strategies for x in (FilteringStrategies.ALLOW_ALL, FilteringStrategies.ALLOW_NONE)):
                raise ValueError(f"Cannot have ALLOW_ALL and ALLOW_NONE filtering strategies in {self.model.__name__}")

            super().__init__()

        def filter_allowed(self, filter_param: str) -> bool:
            """
            Check if a filter is allowed based on the filtering strategies.

            Args:
                filter_param: The filter parameter to check.

            Returns:
                True if the filter is allowed, False otherwise.

            """
            if FilteringStrategies.ALLOW_ALL in self.filtering_strategies:
                return True

            if FilteringStrategies.ALLOW_NONE in self.filtering_strategies:
                return False

            # If we have a whitelist, check if the filter_param is in it
            if FilteringStrategies.WHITELIST in self.filtering_strategies:
                if self.supported_filtering_params and filter_param not in self.supported_filtering_params:
                    return False
                # Allow other rules to fire

            # If we have a blacklist, check if the filter_param is in it
            if FilteringStrategies.BLACKLIST in self.filtering_strategies:
                if self.blacklist_filtering_params and filter_param in self.blacklist_filtering_params:
                    return False
                # Allow other rules to fire

            # Check if the filtering key is disabled
            split_key = filter_param.split("__")
            if len(split_key) > 1:
                field, _lookup = split_key[-2:]
            else:
                field, _lookup = filter_param, None

            # If key is in filtering_disabled, throw an error
            if field in self.filtering_disabled:
                return False

            # Not disabled, so it's allowed
            return True

    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize subclass and set up metadata.

        Args:
            **kwargs: Additional keyword arguments.

        """
        super().__init_subclass__(**kwargs)
        # Ensure the subclass has its own Meta definition.
        # If not, create a new one inheriting from the parent’s Meta.
        # If the subclass hasn't defined its own Meta, auto-generate one.
        if "Meta" not in cls.__dict__:
            top_meta: type[BaseModel.Meta[Self]] | None = None
            # Iterate over ancestors to get the top-most explicitly defined Meta.
            for base in cls.__mro__[1:]:
                if "Meta" in base.__dict__:
                    top_meta = cast("type[BaseModel.Meta[Self]]", base.Meta)
                    break
            if top_meta is None:
                # This should never happen.
                raise ConfigurationError(f"Meta class not found in {cls.__name__} or its bases")

            # Create a new Meta class that inherits from the top-most Meta.
            meta_attrs = {
                k: v
                for k, v in vars(top_meta).items()
                if not k.startswith("_")  # Avoid special attributes like __parameters__
            }
            cls.Meta = type("Meta", (top_meta,), meta_attrs)  # type: ignore # mypy complains about setting to a type
            logger.debug(
                "Auto-generated Meta for %s inheriting from %s",
                cls.__name__,
                top_meta.__name__,
            )

        # Append read_only_fields from all parents to Meta
        # Same with filtering_disabled
        # Retrieve filtering_fields from the attributes of the class
        read_only_fields = (cls.Meta.read_only_fields or set[str]()).copy()
        filtering_disabled = (cls.Meta.filtering_disabled or set[str]()).copy()
        filtering_fields = set(cls.__annotations__.keys())
        supported_filtering_params = cls.Meta.supported_filtering_params
        blacklist_filtering_params = cls.Meta.blacklist_filtering_params
        field_map = cls.Meta.field_map
        for base in cls.__bases__:
            _meta: BaseModel.Meta[Self] | None
            if _meta := getattr(base, "Meta", None):  # type: ignore # we are confident this is BaseModel.Meta
                if hasattr(_meta, "read_only_fields"):
                    read_only_fields.update(_meta.read_only_fields)
                if hasattr(_meta, "filtering_disabled"):
                    filtering_disabled.update(_meta.filtering_disabled)
                if hasattr(_meta, "filtering_fields"):
                    filtering_fields.update(_meta.filtering_fields)
                if hasattr(_meta, "supported_filtering_params"):
                    supported_filtering_params.update(_meta.supported_filtering_params)
                if hasattr(_meta, "blacklist_filtering_params"):
                    blacklist_filtering_params.update(_meta.blacklist_filtering_params)
                if hasattr(_meta, "field_map"):
                    field_map.update(_meta.field_map)

        cls.Meta.read_only_fields = read_only_fields
        cls.Meta.filtering_disabled = filtering_disabled
        # excluding filtering_disabled from filtering_fields
        cls.Meta.filtering_fields = filtering_fields - filtering_disabled
        cls.Meta.supported_filtering_params = supported_filtering_params
        cls.Meta.blacklist_filtering_params = blacklist_filtering_params
        cls.Meta.field_map = field_map

        # Instantiate _meta
        cls._meta = cls.Meta(cls)  # type: ignore # due to a mypy bug in version 1.15.0 (issue #18776)

        # Set name defaults
        if not hasattr(cls._meta, "name"):
            cls._meta.name = cls.__name__.lower()

    # Configure Pydantic behavior
    # type ignore because mypy complains about non-required keys
    model_config = pydantic.ConfigDict(**BASE_MODEL_CONFIG)  # type: ignore

    def __init__(self, **data: Any) -> None:
        """
        Initialize the model with resource and data.

        Args:
            resource: The BaseResource instance.
            **data: Additional data to initialize the model.

        Raises:
            ValueError: If resource is not provided.

        """
        super().__init__(**data)

        if not hasattr(self, "_resource"):
            raise ValueError(f"Resource required. Initialize resource for {self.__class__.__name__} before instantiating models.")

    @property
    def _client(self) -> "PaperlessClient":
        """
        Get the client associated with this model.

        Returns:
            The PaperlessClient instance.

        """
        return self._resource.client

    @property
    def resource(self) -> "BaseResource[Self]":
        return self._resource

    @property
    def save_executor(self) -> concurrent.futures.ThreadPoolExecutor:
        if not self._save_executor:
            self._save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="model_save_worker")
        return self._save_executor

    def cleanup(self) -> None:
        """Clean up resources used by the model class."""
        if self._save_executor:
            self._save_executor.shutdown(wait=True)
            self._save_executor = None

    @override
    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

        # Save original_data to support dirty fields
        self._original_data = self.model_dump()

        # Allow updating attributes to trigger save() automatically
        self._status = ModelStatus.READY

        super().model_post_init(__context)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Create a model instance from API response data.

        Args:
            data: Dictionary containing the API response data.

        Returns:
            A model instance initialized with the provided data.

        Examples:
            # Create a Document instance from API data
            doc = Document.from_dict(api_data)

        """
        return cls._resource.parse_to_model(data)

    def to_dict(
        self,
        *,
        include_read_only: bool = True,
        exclude_none: bool = False,
        exclude_unset: bool = True,
    ) -> dict[str, Any]:
        """
        Convert the model to a dictionary for API requests.

        Args:
            include_read_only: Whether to include read-only fields.
            exclude_none: Whether to exclude fields with None values.
            exclude_unset: Whether to exclude fields that are not set.

        Returns:
            A dictionary with model data ready for API submission.

        Examples:
            # Convert a Document instance to a dictionary
            data = doc.to_dict()

        """
        exclude: set[str] = set() if include_read_only else set(self._meta.read_only_fields)

        return self.model_dump(
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )

    def dirty_fields(self, comparison: Literal["saved", "db", "both"] = "both") -> dict[str, tuple[Any, Any]]:
        """
        Show which fields have changed since last update from the paperless ngx db.

        Args:
            comparison:
                Specify the data to compare ('saved' or 'db').
                Db is the last data retrieved from Paperless NGX
                Saved is the last data sent to Paperless NGX to be saved

        Returns:
            A dictionary {field: (original_value, new_value)} of fields that have
            changed since last update from the paperless ngx db.

        """
        current_data = self.model_dump()
        current_data.pop("id", None)

        if comparison == "saved":
            compare_dict = self._saved_data
        elif comparison == "db":
            compare_dict = self._original_data
        else:
            # For 'both', we want to compare against both original and saved data
            # A field is dirty if it differs from either original or saved data
            compare_dict = {}
            for field in set(list(self._original_data.keys()) + list(self._saved_data.keys())):
                # ID cannot change, and is not set before first save sometimes
                if field == "id":
                    continue

                # Prefer original data (from DB) over saved data when both exist
                compare_dict[field] = self._original_data.get(field, self._saved_data.get(field))

        return {
            field: (compare_dict.get(field, None), current_data.get(field, None))
            for field in current_data
            if compare_dict.get(field, None) != current_data.get(field, None)
        }

    def is_dirty(self, comparison: Literal["saved", "db", "both"] = "both") -> bool:
        """
        Check if any field has changed since last update from the paperless ngx db.

        Args:
            comparison:
                Specify the data to compare ('saved' or 'db').
                Db is the last data retrieved from Paperless NGX
                Saved is the last data sent to Paperless NGX to be saved

        Returns:
            True if any field has changed.

        """
        if self.is_new():
            return True
        return bool(self.dirty_fields(comparison=comparison))

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
        Create a new model instance.

        Args:
            **kwargs: Field values to set.

        Returns:
            A new model instance.

        Examples:
            # Create a new Document instance
            doc = Document.create(filename="example.pdf", contents=b"PDF data")

        """
        return cls._resource.create(**kwargs)

    def delete(self) -> None:
        return self._resource.delete(self)

    def update_locally(self, *, from_db: bool | None = None, skip_changed_fields: bool = False, **kwargs: Any) -> None:
        """
        Update model attributes without triggering automatic save.

        Args:
            **kwargs: Field values to update

        Returns:
            Self with updated values

        """
        from_db = from_db if from_db is not None else False

        # Avoid infinite saving loops
        with StatusContext(self, ModelStatus.UPDATING):
            # Ensure read-only fields were not changed
            if not from_db:
                for field in self._meta.read_only_fields:
                    if field in kwargs and kwargs[field] != self._original_data.get(field, None):
                        raise ReadOnlyFieldError(f"Cannot change read-only field {field}")

            # If the field contains unsaved changes, skip updating it
            # Determine unsaved changes based on the dirty fields before we last called save
            if skip_changed_fields:
                unsaved_changes = self.dirty_fields(comparison="saved")
                kwargs = {k: v for k, v in kwargs.items() if k not in unsaved_changes}

            for name, value in kwargs.items():
                setattr(self, name, value)

            # Dirty has been reset
            if from_db:
                self._original_data = self.model_dump()

    def update(self, **kwargs: Any) -> None:
        """
        Update this model with new values.

        Subclasses implement this with auto-saving features.
        However, base BaseModel instances simply call update_locally.

        Args:
            **kwargs: New field values.

        Examples:
            # Update a Document instance
            doc.update(filename="new_example.pdf")

        """
        # Since we have no id, we can't save. Therefore, all updates are silent updates
        # subclasses may implement this.
        self.update_locally(**kwargs)

    @abstractmethod
    def is_new(self) -> bool:
        """
        Check if this model represents a new (unsaved) object.

        Returns:
            True if the model is new, False otherwise.

        Examples:
            # Check if a Document instance is new
            is_new = doc.is_new()

        """

    def should_save_on_write(self) -> bool:
        """
        Check if the model should save on attribute write, factoring in the client settings.
        """
        if self._meta.save_on_write is not None:
            return self._meta.save_on_write
        return self._resource.client.settings.save_on_write

    def enable_save_on_write(self) -> None:
        """
        Enable automatic saving on attribute write.
        """
        self._meta.save_on_write = True

    def disable_save_on_write(self) -> None:
        """
        Disable automatic saving on attribute write.
        """
        self._meta.save_on_write = False

    def matches_dict(self, data: dict[str, Any]) -> bool:
        """
        Check if the model matches the provided data.

        Args:
            data: Dictionary containing the data to compare.

        Returns:
            True if the model matches the data, False otherwise.

        Examples:
            # Check if a Document instance matches API data
            matches = doc.matches_dict(api_data)

        """
        return self.to_dict() == data

    @override
    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.

        """
        return f"{self._meta.name.capitalize()}"


class StandardModel(BaseModel, ABC):
    """
    Standard model for Paperless-ngx API objects with an ID field.

    Attributes:
        id: Unique identifier for the model.

    """

    id: int = Field(description="Unique identifier from Paperless NGX", default=0)
    _resource: "StandardResource[Self]"  # type: ignore # override

    class Meta(BaseModel.Meta):
        """
        Metadata for the StandardModel.

        Attributes:
            read_only_fields: Fields that should not be modified.
            supported_filtering_params: Params allowed during queryset filtering.

        """

        # Fields that should not be modified
        read_only_fields: ClassVar[set[str]] = {"id"}
        supported_filtering_params = {"id__in", "id"}

    @property
    def resource(self) -> "StandardResource[Self]":  # type: ignore
        return self._resource

    @override
    def update(self, **kwargs: Any) -> None:
        """
        Update this model with new values and save changes.

        NOTE: new instances will not be saved automatically.
        (I'm not sure if that's the right design decision or not)

        Args:
            **kwargs: New field values.

        """
        # Hold off on saving until all updates are complete
        self.update_locally(**kwargs)
        if not self.is_new():
            self.save()

    def refresh(self) -> bool:
        """
        Refresh the model with the latest data from the server.

        Returns:
            True if the model data changes, False on failure or if the data does not change.

        Raises:
            ResourceNotFoundError: If the model is not found on Paperless. (e.g. it was deleted remotely)

        """
        if self.is_new():
            raise ResourceNotFoundError("Model does not have an id, so cannot be refreshed. Save first.")

        new_model = self._resource.get(self.id)

        if self == new_model:
            return False

        self.update_locally(from_db=True, **new_model.to_dict())
        return True

    def save(self, *, force: bool = False) -> bool:
        return self.save_sync(force=force)

    def save_sync(self, *, force: bool = False) -> bool:
        """
        Save this model instance synchronously.

        Changes are sent to the server immediately, and the model is updated
        when the server responds.

        Returns:
            True if the save was successful, False otherwise.

        Raises:
            ResourceNotFoundError: If the resource doesn't exist on the server
            RequestError: If there's a communication error with the server
            PermissionError: If the user doesn't have permission to update the resource

        """
        if self.is_new():
            model = self.create(**self.to_dict())
            self.update_locally(from_db=True, **model.to_dict())
            return True

        if not force:
            if self._status == ModelStatus.SAVING:
                logger.warning("Model is already saving, skipping save")
                return False

            # Only start a save if there are changes
            if not self.is_dirty():
                logger.warning("Model is not dirty, skipping save")
                return False

        with StatusContext(self, ModelStatus.SAVING):
            # Prepare and send the update to the server
            current_data = self.to_dict(include_read_only=False, exclude_none=False, exclude_unset=True)
            self._saved_data = {**current_data}

            registry.emit(
                "model.save:before",
                "Fired before the model data is sent to paperless ngx to be saved.",
                kwargs={"model": self, "current_data": current_data},
            )

            new_model = self._resource.update(self)  # type: ignore # basedmypy complaining about self

            if not new_model:
                logger.warning(f"Result of save was none for model id {self.id}")
                return False

            if not isinstance(new_model, StandardModel):
                # This should never happen
                logger.error("Result of save was not a StandardModel instance")
                return False

            try:
                # Update the model with the server response
                new_data = new_model.to_dict()
                self.update_locally(from_db=True, **new_data)

                registry.emit(
                    "model.save:after",
                    "Fired after the model data is saved in paperless ngx.",
                    kwargs={"model": self, "updated_data": new_data},
                )

            except APIError as e:
                logger.error(f"API error during save of {self}: {e}")
                registry.emit(
                    "model.save:error",
                    "Fired when a network error occurs during save.",
                    kwargs={"model": self, "error": e},
                )

            except Exception as e:
                # Log unexpected errors but don't swallow them
                logger.exception(f"Unexpected error during save of {self}")
                registry.emit(
                    "model.save:error",
                    "Fired when an unexpected error occurs during save.",
                    kwargs={"model": self, "error": e},
                )
                # Re-raise so the executor can handle it properly
                raise

        return True

    def save_async(self, *, force: bool = False) -> bool:
        """
        Save this model instance asynchronously.

        Changes are sent to the server in a background thread, and the model
        is updated when the server responds.

        Returns:
            True if the save was successfully submitted async, False otherwise.

        """
        if not force:
            if self._status == ModelStatus.SAVING:
                return False

            # Only start a save if there are changes
            if not self.is_dirty():
                if hasattr(self, "_save_lock") and self._save_lock._is_owned():  # type: ignore # temporary TODO
                    self._save_lock.release()
                return False

            # If there's a pending save, skip saving until it finishes
            if self._pending_save is not None and not self._pending_save.done():
                return False

        self._status = ModelStatus.SAVING
        self._save_lock.acquire(timeout=30)

        # Start a new save operation
        executor = self.save_executor
        future = executor.submit(self._perform_save_async)
        self._pending_save = future
        future.add_done_callback(self._handle_save_result_async)
        return True

    def _perform_save_async(self) -> Self | None:
        """
        Perform the actual save operation.

        Returns:
            The updated model from the server or None if no save was needed.

        Raises:
            ResourceNotFoundError: If the resource doesn't exist on the server
            RequestError: If there's a communication error with the server
            PermissionError: If the user doesn't have permission to update the resource

        """
        # Prepare and send the update to the server
        current_data = self.to_dict(include_read_only=False, exclude_none=False, exclude_unset=True)
        self._saved_data = {**current_data}

        registry.emit(
            "model.save:before",
            "Fired before the model data is sent to paperless ngx to be saved.",
            kwargs={"model": self, "current_data": current_data},
        )

        return self._resource.update(self)

    def _handle_save_result_async(self, future: concurrent.futures.Future[Any]) -> bool:
        """
        Handle the result of an asynchronous save operation.

        Args:
            future: The completed Future object containing the save result.

        """
        try:
            # Get the result with a timeout
            new_model: Self = future.result(timeout=self._meta.save_timeout)

            if not new_model:
                logger.warning(f"Result of save was none for model id {self.id}")
                return False

            if not isinstance(new_model, StandardModel):
                # This should never happen
                logger.error("Result of save was not a StandardModel instance")
                return False

            # Update the model with the server response
            new_data = new_model.to_dict()
            # Use direct attribute setting instead of update_locally to avoid mocking issues
            with StatusContext(self, ModelStatus.UPDATING):
                for name, value in new_data.items():
                    if self.is_dirty("saved") and name in self.dirty_fields("saved"):
                        continue  # Skip fields changed during save
                    setattr(self, name, value)
                # Mark as from DB
                self._original_data = self.model_dump()

            registry.emit(
                "model.save:after",
                "Fired after the model data is saved in paperless ngx.",
                kwargs={"model": self, "updated_data": new_data},
            )

        except concurrent.futures.TimeoutError:
            logger.error(f"Save operation timed out for {self}")
            registry.emit(
                "model.save:error",
                "Fired when a save operation times out.",
                kwargs={"model": self, "error": "Timeout"},
            )

        except APIError as e:
            logger.error(f"API error during save of {self}: {e}")
            registry.emit(
                "model.save:error",
                "Fired when a network error occurs during save.",
                kwargs={"model": self, "error": e},
            )

        except Exception as e:
            # Log unexpected errors but don't swallow them
            logger.exception(f"Unexpected error during save of {self}")
            registry.emit(
                "model.save:error",
                "Fired when an unexpected error occurs during save.",
                kwargs={"model": self, "error": e},
            )
            # Re-raise so the executor can handle it properly
            raise

        finally:
            self._pending_save = None
            try:
                self._save_lock.release()
            except RuntimeError:
                logger.debug("Save lock already released")
            self._status = ModelStatus.READY

            # If the model was changed while the save was in progress,
            # we need to save again
            if self.is_dirty("saved"):
                # Small delay to avoid hammering the server
                time.sleep(0.1)
                # Save, and reset unsaved data
                self.save()

        return True

    @override
    def is_new(self) -> bool:
        """
        Check if this model represents a new (unsaved) object.

        Returns:
            True if the model is new, False otherwise.

        Examples:
            # Check if a Document instance is new
            is_new = doc.is_new()

        """
        return self.id == 0

    def _autosave(self) -> None:
        # Skip autosave for:
        # - New models (not yet saved)
        # - When auto-save is disabled
        if self.is_new() or self.should_save_on_write() is False or not self.is_dirty():
            return

        self.save()

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override attribute setting to automatically trigger async save.

        Args:
            name: Attribute name
            value: New attribute value

        """
        # Set the new value
        super().__setattr__(name, value)

        # Autosave logic below
        if self._status != ModelStatus.READY:
            return

        # Skip autosave for private fields
        if not name.startswith("_"):
            self._autosave()

    @override
    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.

        """
        return f"{self._meta.name.capitalize()} #{self.id}"
