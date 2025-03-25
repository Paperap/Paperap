"""
Define base model classes for Paperless-ngx API objects.

This module provides the foundation for all model classes in Paperap,
implementing core functionality for serialization, validation, and API
interactions. The models handle data mapping between Python objects and
the Paperless-ngx API, with support for automatic saving, dirty tracking,
and asynchronous operations.

The module contains two primary classes:
- BaseModel: Abstract base class for all API objects
- StandardModel: Extension of BaseModel for objects with ID fields

These classes are designed to be subclassed by specific resource models
like Document, Tag, Correspondent, etc.
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

from paperap.const import ClientResponse, FilteringStrategies, ModelStatus
from paperap.exceptions import APIError, ConfigurationError, ReadOnlyFieldError, RequestError, ResourceNotFoundError
from paperap.models.abstract.meta import StatusContext
from paperap.signals import registry

if TYPE_CHECKING:
    from paperap.client import PaperlessClient
    from paperap.resources.base import BaseResource, StandardResource

logger = logging.getLogger(__name__)


class ModelConfigType(TypedDict):
    """
    Define configuration options for Pydantic models.

    This type definition specifies the configuration options used for
    all Pydantic models in the application, ensuring consistent behavior
    across all model classes.

    Attributes:
        populate_by_name: Allow population by field name as well as alias.
        validate_assignment: Validate values when attributes are set.
        validate_default: Validate default values during model initialization.
        use_enum_values: Use enum values rather than enum instances.
        extra: How to handle extra fields (ignore them).
        arbitrary_types_allowed: Allow arbitrary types in model fields.

    """

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

    Provide automatic serialization, deserialization, and API interactions
    with minimal configuration. This abstract class serves as the foundation
    for all models in the Paperap library, handling data validation, dirty
    tracking, and API communication.

    Attributes:
        _meta: Metadata for the model, including filtering and resource information.
        _save_lock: Lock for saving operations to prevent race conditions.
        _pending_save: Future object for pending save operations.
        _save_executor: Executor for asynchronous save operations.
        _status: Current status of the model (INITIALIZING, READY, UPDATING, SAVING).
        _original_data: Original data from the server for dirty checking.
        _saved_data: Data last sent to the database during save operations.
        _resource: Associated resource for API interactions.

    Raises:
        ValueError: If resource is not provided during initialization.

    Examples:
        Models are typically accessed through the client interface:

        >>> document = client.documents.get(123)
        >>> print(document.title)
        >>> document.title = "New Title"
        >>> document.save()

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

        Define model behavior, filtering capabilities, and API interaction rules.
        Each model class has its own Meta instance that controls how the model
        interacts with the Paperless-ngx API.

        Attributes:
            model: Reference to the model class this metadata belongs to.
            name: The name of the model, used in API paths and error messages.
            read_only_fields: Fields that should not be modified by the client.
            filtering_disabled: Fields that cannot be used for filtering.
            filtering_fields: Fields allowed for filtering operations.
            supported_filtering_params: Specific filter parameters allowed
                during queryset filtering (e.g., "content__icontains", "id__gt").
            blacklist_filtering_params: Filter parameters explicitly disallowed.
            filtering_strategies: Strategies that determine how filtering is handled
                (ALLOW_ALL, ALLOW_NONE, WHITELIST, BLACKLIST).
            field_map: Map of API field names to model attribute names.
            save_on_write: If True, updating attributes triggers automatic save.
                If None, follows client.settings.save_on_write.
            save_timeout: Timeout in seconds for save operations.

        Raises:
            ValueError: If both ALLOW_ALL and ALLOW_NONE filtering strategies are set,
                which would create contradictory behavior.

        Examples:
            Defining a custom Meta for a model:

            >>> class Document(StandardModel):
            >>>     class Meta(StandardModel.Meta):
            >>>         read_only_fields = {"content", "checksum"}
            >>>         filtering_strategies = {FilteringStrategies.WHITELIST}
            >>>         supported_filtering_params = {"title__icontains", "created__gt"}

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
            Check if a filter parameter is allowed based on the filtering strategies.

            Evaluate whether a given filter parameter can be used with this model
            based on the configured filtering strategies and rules. This method
            implements the filtering logic defined by the model's filtering_strategies.

            Args:
                filter_param: The filter parameter to check (e.g., "title__contains").

            Returns:
                bool: True if the filter is allowed, False otherwise.

            Examples:
                >>> meta.filter_allowed("title__contains")
                True
                >>> meta.filter_allowed("content__exact")
                False  # If content is in filtering_disabled

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

        Ensure that each subclass has its own Meta definition and properly
        inherits metadata attributes from parent classes. This method handles
        the automatic creation and configuration of model metadata.

        Args:
            **kwargs: Additional keyword arguments passed to parent __init_subclass__.

        Raises:
            ConfigurationError: If no Meta class is found in the class hierarchy.

        Notes:
            This method automatically:
            - Creates a Meta class for the subclass if not explicitly defined
            - Inherits and merges metadata from parent classes
            - Initializes the _meta instance for the subclass

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

        Set up the model with the provided resource and initialize it with
        field values from the API response or user input.

        Args:
            **data: Field values to initialize the model with.

        Raises:
            ValueError: If resource is not provided or properly initialized.

        Notes:
            Models should typically be created through their resource's methods
            rather than directly instantiated.

        """
        super().__init__(**data)

        if not hasattr(self, "_resource"):
            raise ValueError(f"Resource required. Initialize resource for {self.__class__.__name__} before instantiating models.")

    @property
    def _client(self) -> "PaperlessClient":
        """
        Get the client associated with this model.

        Provide access to the PaperlessClient instance that handles API
        communication for this model.

        Returns:
            PaperlessClient: The client instance associated with this model's resource.

        """
        return self._resource.client

    @property
    def resource(self) -> "BaseResource[Self]":
        """
        Get the resource associated with this model.

        Provide access to the resource instance that handles API interactions
        for this model type, such as retrieving, creating, updating, and
        deleting objects.

        Returns:
            BaseResource[Self]: The resource instance for this model type.

        """
        return self._resource

    @property
    def save_executor(self) -> concurrent.futures.ThreadPoolExecutor:
        """
        Get the thread pool executor for asynchronous save operations.

        Provide access to the thread pool that handles asynchronous save operations,
        creating a new executor if one doesn't exist yet.

        Returns:
            concurrent.futures.ThreadPoolExecutor: The executor for handling
                asynchronous save operations.

        """
        if not self._save_executor:
            self._save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="model_save_worker")
        return self._save_executor

    def cleanup(self) -> None:
        """
        Clean up resources used by the model.

        Shut down the save executor to release resources. Call this method
        when the model is no longer needed to prevent resource leaks.
        """
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

        Instantiate a model from a dictionary of API response data,
        handling field mapping and type conversion through the resource's
        parse_to_model method.

        Args:
            data: Dictionary containing the API response data.

        Returns:
            Self: A model instance initialized with the provided data.

        Examples:
            >>> api_data = {"id": 123, "title": "Invoice", "created": "2023-01-01T00:00:00Z"}
            >>> doc = Document.from_dict(api_data)
            >>> print(doc.id, doc.title)
            123 Invoice

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

        Prepare the model data for submission to the API, with options to
        control which fields are included based on their properties and values.

        Args:
            include_read_only: Whether to include read-only fields in the output.
                Set to False when preparing data for update operations.
            exclude_none: Whether to exclude fields with None values.
            exclude_unset: Whether to exclude fields that were not explicitly set.
                Useful for partial updates.

        Returns:
            dict[str, Any]: A dictionary with model data ready for API submission.

        Examples:
            >>> # Full representation including all fields
            >>> data = doc.to_dict()
            >>>
            >>> # Only include fields that can be modified
            >>> update_data = doc.to_dict(include_read_only=False)
            >>>
            >>> # Only include fields that have been explicitly set
            >>> partial_data = doc.to_dict(exclude_unset=True)

        """
        exclude: set[str] = set() if include_read_only else set(self._meta.read_only_fields)

        return self.model_dump(
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )

    def dirty_fields(self, comparison: Literal["saved", "db", "both"] = "both") -> dict[str, tuple[Any, Any]]:
        """
        Show which fields have changed since last update from the Paperless NGX database.

        Compare the current model data with the last saved or retrieved data
        to identify changes. This method helps determine what will be sent to
        the server on the next save operation.

        Args:
            comparison: Specify the data to compare against:
                - "saved": Compare against the last data sent to Paperless NGX
                - "db": Compare against the last data retrieved from Paperless NGX
                - "both": Compare against both saved and db data (default)

        Returns:
            dict[str, tuple[Any, Any]]: A dictionary mapping field names to tuples of
                (original_value, current_value) for all fields that have changed.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.title = "New Title"
            >>> doc.dirty_fields()
            {'title': ('Original Title', 'New Title')}

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
        Check if any field has changed since last update from the Paperless NGX database.

        Determine if the model has unsaved changes by comparing current data
        with the last saved or retrieved data. New models are always considered dirty.

        Args:
            comparison: Specify the data to compare against:
                - "saved": Compare against the last data sent to Paperless NGX
                - "db": Compare against the last data retrieved from Paperless NGX
                - "both": Compare against both saved and db data (default)

        Returns:
            bool: True if any field has changed, False otherwise.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.is_dirty()
            False
            >>> doc.title = "New Title"
            >>> doc.is_dirty()
            True

        """
        if self.is_new():
            return True
        return bool(self.dirty_fields(comparison=comparison))

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
        Create a new model instance and save it to the server.

        Create a new instance of the model with the specified field values
        and immediately save it to the Paperless NGX server. This is a
        convenience method that delegates to the resource's create method.

        Args:
            **kwargs: Field values to set on the new model instance.

        Returns:
            Self: A new model instance that has been saved to the server.

        Examples:
            >>> tag = Tag.create(name="Invoices", color="#ff0000")
            >>> correspondent = Correspondent.create(name="Electric Company")
            >>> doc_type = DocumentType.create(name="Bill")

        """
        return cls._resource.create(**kwargs)

    def delete(self) -> ClientResponse:
        """
        Delete this model from the Paperless NGX server.

        Remove the model from the server. After calling this method,
        the model instance should not be used anymore as it no longer
        represents a valid server object.

        Raises:
            ResourceNotFoundError: If the model doesn't exist on the server.
            APIError: If the server returns an error response.

        """
        return self._resource.delete(self)

    def update_locally(self, *, from_db: bool | None = None, skip_changed_fields: bool = False, **kwargs: Any) -> None:
        """
        Update model attributes without triggering automatic save.

        Update the model's attributes with the provided values without sending
        changes to the server, regardless of the save_on_write setting. This is
        useful for local modifications or when applying server updates.

        Args:
            from_db: Whether the update is from the database. If True, resets the
                dirty tracking to consider the model clean after the update.
            skip_changed_fields: Whether to skip updating fields that have unsaved
                changes. Useful when merging updates from the server with local changes.
            **kwargs: Field values to update.

        Raises:
            ReadOnlyFieldError: If attempting to change a read-only field when
                from_db is False.

        Examples:
            >>> doc = client.documents.get(123)
            >>> # Update without saving to server
            >>> doc.update_locally(title="New Title", correspondent_id=5)
            >>> # Update from server data
            >>> doc.update_locally(from_db=True, **server_data)

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

        Update the model with the provided field values. In BaseModel,
        this simply calls update_locally without saving. Subclasses
        (like StandardModel) may implement automatic saving.

        Args:
            **kwargs: New field values to set on the model.

        Examples:
            >>> model.update(name="New Name", description="Updated description")

        """
        # Since we have no id, we can't save. Therefore, all updates are silent updates
        # subclasses may implement this.
        self.update_locally(**kwargs)

    @abstractmethod
    def is_new(self) -> bool:
        """
        Check if this model represents a new (unsaved) object.

        Determine if the model has been saved to the server. Subclasses
        must implement this method, typically by checking if the model
        has a valid ID or other server-assigned identifier.

        Returns:
            bool: True if the model is new (not yet saved), False otherwise.

        Examples:
            >>> doc = Document.create(title="New Document")
            >>> doc.is_new()  # Returns False after creation
            >>>
            >>> # When creating a model instance manually:
            >>> doc = Document(title="Draft Document")
            >>> doc.is_new()  # Returns True

        """

    def should_save_on_write(self) -> bool:
        """
        Check if the model should save on attribute write.

        Determine if changes to model attributes should trigger an automatic
        save operation based on configuration settings. This method considers
        both the model's meta settings and the client settings, with the
        model's setting taking precedence.

        Returns:
            bool: True if the model should save on write, False otherwise.

        """
        if self._meta.save_on_write is not None:
            return self._meta.save_on_write
        return self._resource.client.settings.save_on_write

    def enable_save_on_write(self) -> None:
        """
        Enable automatic saving on attribute write.

        Set the model's meta configuration to allow automatic saving whenever
        an attribute is modified, overriding the client's default setting.
        This affects only this specific model instance.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.enable_save_on_write()
            >>> doc.title = "New Title"  # This will trigger an automatic save

        """
        self._meta.save_on_write = True

    def disable_save_on_write(self) -> None:
        """
        Disable automatic saving on attribute write.

        Set the model's meta configuration to prevent automatic saving whenever
        an attribute is modified, overriding the client's default setting.
        This affects only this specific model instance.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.disable_save_on_write()
            >>> doc.title = "New Title"  # This won't trigger an automatic save
            >>> doc.save()  # Manual save required

        """
        self._meta.save_on_write = False

    def matches_dict(self, data: dict[str, Any]) -> bool:
        """
        Check if the model matches the provided data.

        Compare the model's current data with a given dictionary to determine
        if they are equivalent. This is useful for checking if a model needs
        to be updated based on new data from the server.

        Args:
            data: Dictionary containing the data to compare against.

        Returns:
            bool: True if the model matches the data, False otherwise.

        Examples:
            >>> doc = client.documents.get(123)
            >>> new_data = {"id": 123, "title": "Invoice", "correspondent_id": 5}
            >>> doc.matches_dict(new_data)
            False  # If any values differ

        """
        return self.to_dict() == data

    @override
    def __eq__(self, value: object) -> bool:
        """
        Compare this model with another object for equality.
        """
        if isinstance(value, BaseModel):
            return self.to_dict() == value.to_dict()
        return super().__eq__(value)

    @override
    def __str__(self) -> str:
        """
        Human-readable string representation.

        Provide a string representation of the model that includes the
        model type and ID, typically used for logging and debugging purposes.

        Returns:
            str: A string representation of the model (e.g., "Document #123").

        """
        return f"{self._meta.name.capitalize()}"


class StandardModel(BaseModel, ABC):
    """
    Standard model for Paperless-ngx API objects with an ID field.

    Extend BaseModel to include a unique identifier and additional functionality
    for API objects that require an ID. Most Paperless-ngx resources are
    represented by StandardModel subclasses.

    This class adds functionality for:
    - Tracking whether an object is new or existing
    - Automatic saving of changes to the server
    - Refreshing data from the server
    - Synchronous and asynchronous save operations

    Attributes:
        id: Unique identifier for the model from Paperless-ngx.
        _resource: Associated resource for API interactions.

    Examples:
        StandardModel subclasses are typically accessed through the client:

        >>> doc = client.documents.get(123)
        >>> tag = client.tags.create(name="Important")
        >>> correspondent = client.correspondents.all()[0]

    """

    id: int = Field(description="Unique identifier from Paperless NGX", default=0)
    _resource: "StandardResource[Self]"  # type: ignore # override

    class Meta(BaseModel.Meta):
        """
        Metadata for the StandardModel.

        Define metadata specific to StandardModel, including read-only fields
        and filtering parameters common to all standard Paperless-ngx resources.

        Attributes:
            read_only_fields: Fields that should not be modified,
                including the 'id' field which is set by the server.
            supported_filtering_params: Common filtering parameters
                supported for all standard models, including id-based lookups.

        """

        read_only_fields: ClassVar[set[str]] = {"id"}
        supported_filtering_params = {"id__in", "id"}

    @property
    def resource(self) -> "StandardResource[Self]":  # type: ignore
        """
        Get the resource associated with this model.

        Provide access to the StandardResource instance that handles API
        interactions for this model type, with support for ID-based operations.

        Returns:
            StandardResource[Self]: The resource instance for this model type.

        """
        return self._resource

    @override
    def update(self, **kwargs: Any) -> None:
        """
        Update this model with new values and save changes.

        Update the model with the provided field values and automatically
        save the changes to the server if the model is not new. This method
        combines update_locally and save for convenience.

        Args:
            **kwargs: New field values to set on the model.

        Note:
            New (unsaved) instances will be updated locally but not saved automatically.
            Use create() to save new instances.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.update(title="New Title", correspondent_id=5)
            >>> # Changes are immediately saved to the server

        """
        # Hold off on saving until all updates are complete
        self.update_locally(**kwargs)
        if not self.is_new():
            self.save()

    def refresh(self) -> bool:
        """
        Refresh the model with the latest data from the server.

        Retrieve the latest data for the model from the server and update
        the model instance with any changes. This is useful when you suspect
        the server data may have changed due to actions by other users or
        automated processes.

        Returns:
            bool: True if the model data changed, False if the data is identical
                or the refresh failed.

        Raises:
            ResourceNotFoundError: If the model is not found on the server
                (e.g., it was deleted remotely).

        Examples:
            >>> doc = client.documents.get(123)
            >>> # After some time or operations by other users
            >>> doc.refresh()  # Update with latest data from server

        """
        if self.is_new():
            raise ResourceNotFoundError("Model does not have an id, so cannot be refreshed. Save first.")

        new_model = self._resource.get(self.id)

        if self == new_model:
            return False

        self.update_locally(from_db=True, **new_model.to_dict())
        return True

    def save(self, *, force: bool = False) -> bool:
        """
        Save this model to the Paperless NGX server.

        Send the current model state to the server, creating a new object
        or updating an existing one. This is a convenience method that
        calls save_sync.

        Args:
            force: Whether to force the save operation even if the model
                is not dirty or is already saving.

        Returns:
            bool: True if the save was successful, False otherwise.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.title = "New Title"
            >>> doc.save()
            >>>
            >>> # Force save even if no changes
            >>> doc.save(force=True)

        """
        return self.save_sync(force=force)

    def save_sync(self, *, force: bool = False) -> bool:
        """
        Save this model instance synchronously.

        Send changes to the server immediately and update the model when
        the server responds. This method blocks until the save operation
        is complete.

        Args:
            force: Whether to force the save operation even if the model
                is not dirty or is already saving.

        Returns:
            bool: True if the save was successful, False otherwise.

        Raises:
            ResourceNotFoundError: If the resource doesn't exist on the server.
            RequestError: If there's a communication error with the server.
            APIError: If the server returns an error response.
            PermissionError: If the user doesn't have permission to update the resource.

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.title = "New Title"
            >>> success = doc.save_sync()
            >>> print(f"Save {'succeeded' if success else 'failed'}")

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

        Send changes to the server in a background thread, allowing other
        operations to continue while waiting for the server response.
        The model will be updated with the server's response when the
        save completes.

        Args:
            force: Whether to force the save operation even if the model
                is not dirty or is already saving.

        Returns:
            bool: True if the save was successfully submitted to the background
                thread, False otherwise (e.g., if there are no changes to save).

        Examples:
            >>> doc = client.documents.get(123)
            >>> doc.title = "New Title"
            >>> # Continue execution immediately while save happens in background
            >>> doc.save_async()
            >>> # Do other work...

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
        Perform the actual save operation in a background thread.

        Handle the core logic for saving the model to the server, preparing
        the data and sending the update request. This internal method is called
        by save_async() in a separate thread.

        Returns:
            Self | None: The updated model from the server or None if no save was needed.

        Raises:
            ResourceNotFoundError: If the resource doesn't exist on the server.
            RequestError: If there's a communication error with the server.
            APIError: If the server returns an error response.
            PermissionError: If the user doesn't have permission to update the resource.

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

        Process the result of an async save, updating the model with the
        server's response or handling errors. This internal method is called
        automatically when an asynchronous save operation completes.

        Args:
            future: The completed Future object containing the save result.

        Returns:
            bool: True if the save result was handled successfully, False otherwise.

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

        Determine if the model has been saved to the server by checking
        if it has a valid ID (non-zero). StandardModel implements this
        method by checking the id attribute.

        Returns:
            bool: True if the model is new (not yet saved), False otherwise.

        Examples:
            >>> doc = Document(title="Draft")  # No ID yet
            >>> doc.is_new()
            True
            >>> saved_doc = client.documents.get(123)
            >>> saved_doc.is_new()
            False

        """
        return self.id == 0

    def _autosave(self) -> None:
        """
        Automatically save the model if conditions are met.

        Handle automatic saving based on the save_on_write setting when
        attributes are modified. This internal method is called by __setattr__
        and skips saving for:
        - New models (not yet saved)
        - When auto-save is disabled
        - When there are no changes to save
        """
        # Skip autosave for:
        # - New models (not yet saved)
        # - When auto-save is disabled
        if self.is_new() or self.should_save_on_write() is False or not self.is_dirty():
            return

        self.save()

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override attribute setting to automatically trigger save.

        Intercept attribute assignments and trigger an automatic save
        operation if appropriate based on the save_on_write setting.
        This enables the "save on write" functionality that makes the
        model automatically sync changes to the server.

        Args:
            name: Attribute name to set
            value: New attribute value

        Notes:
            - Private attributes (starting with '_') never trigger autosave
            - Autosave only happens when model status is READY
            - Autosave is skipped for new models or when save_on_write is False

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

        This method returns a string representation of the model, typically
        used for logging and debugging purposes.

        Returns:
            str: A string representation of the model.

        """
        return f"{self._meta.name.capitalize()} #{self.id}"
