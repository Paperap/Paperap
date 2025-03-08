"""




----------------------------------------------------------------------------

   METADATA:

       File:    base.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.2
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar, Generic, Literal, Self, TYPE_CHECKING
from typing_extensions import TypeVar
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from yarl import URL

from paperap.const import FilteringStrategies, ModelStatus
from paperap.models.abstract.meta import StatusContext
from paperap.models.abstract.parser import Parser
from paperap.models.abstract.queryset import QuerySet
from paperap.signals import SignalRegistry

if TYPE_CHECKING:
    from paperap.resources.base import PaperlessResource, StandardResource
    from paperap.client import PaperlessClient

_Self = TypeVar("_Self", bound="PaperlessModel")


class PaperlessModel(BaseModel, ABC):
    """
    Base model for all Paperless-ngx API objects.

    Provides automatic serialization, deserialization, and API interactions
    with minimal configuration needed.

    Attributes:
        _meta: Metadata for the model, including filtering and resource information.

    Returns:
        A new instance of PaperlessModel.

    Raises:
        ValueError: If resource is not provided.

    Examples:
        from paperap.models.abstract.model import StandardModel
        class Document(StandardModel):
            filename: str
            contents : bytes

            class Meta:
                api_endpoint: = URL("http://localhost:8000/api/documents/")
    """

    _meta: "Meta[Self]" = PrivateAttr()

    class Meta(Generic[_Self]):
        """
        Metadata for the PaperlessModel.

        Attributes:
            name: The name of the model.
            read_only_fields: Fields that should not be modified.
            filtering_disabled: Fields disabled for filtering.
            filtering_fields: Fields allowed for filtering.
            supported_filtering_params: Params allowed during queryset filtering.
            blacklist_filtering_params: Params disallowed during queryset filtering.
            filtering_strategies: Strategies for filtering.
            parser: The type of parser for API data.
            resource: The PaperlessResource instance.
            queryset: The type of QuerySet for the model.

        Raises:
            ValueError: If both ALLOW_ALL and ALLOW_NONE filtering strategies are set.
        """

        # The name of the model.
        # It will default to the classname
        name: str
        # Fields that should not be modified. These will be appended to read_only_fields for all parent classes.
        read_only_fields: ClassVar[set[str]] = {"id", "created", "updated"}
        # Fields that are disabled by Paperless NGX for filtering. These will be appended to filtering_disabled for all parent classes.
        filtering_disabled: ClassVar[set[str]] = set()
        # Fields allowed for filtering. Generated automatically during class init.
        filtering_fields: ClassVar[set[str]] = set()
        # If set, only these params will be allowed during queryset filtering. (e.g. {"content__icontains", "id__gt"})
        # These will be appended to supported_filtering_params for all parent classes.
        supported_filtering_params: ClassVar[set[str]] = set()
        # If set, these params will be disallowed during queryset filtering (e.g. {"content__icontains", "id__gt"})
        # These will be appended to blacklist_filtering_params for all parent classes.
        blacklist_filtering_params: ClassVar[set[str]] = set()
        # Strategies for filtering. This determines which of the above lists will be used to allow or deny filters to QuerySets.
        filtering_strategies: ClassVar[set[FilteringStrategies]] = {FilteringStrategies.BLACKLIST}
        # the type of parser, which parses api data into appropriate types
        # this will usually not need to be overridden
        parser: type[Parser[_Self]] = Parser[_Self]
        resource: "PaperlessResource[_Self]"
        queryset: type[QuerySet[_Self]] = QuerySet
        # Updating attributes will not trigger save()
        status: ModelStatus = ModelStatus.INITIALIZING
        original_data: dict[str, Any] = {}
        # If true, updating attributes will trigger save(). If false, save() must be called manually
        # True or False will override client.settings.save_on_write (PAPERLESS_SAVE_ON_WRITE)
        # None will respect client.settings.save_on_write
        save_on_write: bool | None = None

        def __init__(self, model: type[_Self]):
            self.model = model

            # Validate filtering strategies
            if all(
                x in self.filtering_strategies for x in (FilteringStrategies.ALLOW_ALL, FilteringStrategies.ALLOW_NONE)
            ):
                raise ValueError(f"Cannot have ALLOW_ALL and ALLOW_NONE filtering strategies in {self.model.__name__}")

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

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Initialize subclass and set up metadata.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init_subclass__(**kwargs)

        # Append read_only_fields from all parents to Meta
        # Same with filtering_disabled
        # Retrieve filtering_fields from the attributes of the class
        read_only_fields = (cls.Meta.read_only_fields or set()).copy()
        filtering_disabled = (cls.Meta.filtering_disabled or set()).copy()
        filtering_fields = set(cls.__annotations__.keys())
        supported_filtering_params = cls.Meta.supported_filtering_params
        blacklist_filtering_params = cls.Meta.blacklist_filtering_params
        for base in cls.__bases__:
            _meta: PaperlessModel.Meta | None
            if _meta := getattr(base, "Meta", None):
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

        cls.Meta.read_only_fields = read_only_fields
        cls.Meta.filtering_disabled = filtering_disabled
        # excluding filtering_disabled from filtering_fields
        cls.Meta.filtering_fields = filtering_fields - filtering_disabled
        cls.Meta.supported_filtering_params = supported_filtering_params
        cls.Meta.blacklist_filtering_params = blacklist_filtering_params

        # Instantiate _meta
        cls._meta = cls.Meta(cls)

        # Set name defaults
        if not hasattr(cls._meta, "name"):
            cls._meta.name = cls.__name__.lower()

    # Configure Pydantic behavior
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
    )

    @property
    def _resource(self) -> "PaperlessResource":
        """
        Get the resource associated with this model.

        Returns:
            The PaperlessResource instance.
        """
        return self._meta.resource

    @property
    def _client(self) -> "PaperlessClient":
        """
        Get the client associated with this model.

        Returns:
            The PaperlessClient instance.
        """
        return self._meta.resource.client

    def __init__(self, resource: "PaperlessResource | None" = None, **data):
        """
        Initialize the model with resource and data.

        Args:
            resource: The PaperlessResource instance.
            **data: Additional data to initialize the model.

        Raises:
            ValueError: If resource is not provided.
        """
        super().__init__(**data)

        if resource:
            self._meta.resource = resource

        if not getattr(self._meta, "resource", None):
            raise ValueError(
                "Resource is required for PaperlessModel. Initialize the resource before instantiating models."
            )

    def model_post_init(self, __context):
        super().model_post_init(__context)

        # Save original_data to support dirty fields
        self._meta.original_data = self.model_dump()

        # Allow updating attributes to trigger save() automatically
        self._meta.status = ModelStatus.READY

    @classmethod
    def from_dict(cls, data: dict[str, Any], resource: "PaperlessResource") -> Self:
        """
        Create a model instance from API response data.

        Args:
            data: Dictionary containing the API response data.
            resource: The PaperlessResource instance associated with the model.

        Returns:
            A model instance initialized with the provided data.

        Examples:
            # Create a Document instance from API data
            doc = Document.from_dict(api_data, resource=client.documents)
        """
        return cls.model_validate({**data, "resource": resource})

    def to_dict(
        self,
        *,
        include_read_only: bool = True,
        exclude_none: bool = True,
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
        exclude = set() if include_read_only else set(self._meta.read_only_fields)

        return self.model_dump(
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )

    def dirty_fields(self) -> dict[str, Any]:
        """
        Shows which fields have changed since last update from the paperless ngx db.

        Returns:
            A dictionary of fields that have changed since last update from the paperless ngx db.
        """
        return {
            field: value
            for field, value in self.model_dump().items()
            if field in self._meta.original_data and self._meta.original_data[field] != value
        }

    def is_dirty(self) -> bool:
        """
        Check if any field has changed since last update from the paperless ngx db.

        Returns:
            True if any field has changed.
        """
        return bool(self.dirty_fields())

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
        Factory method to create a new model instance.

        Args:
            **kwargs: Field values to set.

        Returns:
            A new model instance.

        Examples:
            # Create a new Document instance
            doc = Document.create(filename="example.pdf", contents=b"PDF data")
        """
        # TODO save
        return cls(**kwargs)

    def update_locally(self, **kwargs) -> None:
        """
        Update model attributes without triggering automatic save.

        Args:
            **kwargs: Field values to update

        Returns:
            Self with updated values
        """
        from_db = kwargs.pop("from_db", False)

        with StatusContext(self, ModelStatus.UPDATING):
            for name, value in kwargs.items():
                setattr(self, name, value)

        # Dirty has been reset
        if from_db:
            self._meta.original_data = self.model_dump()

    def update(self, **kwargs: Any) -> None:
        """
        Update this model with new values.

        Subclasses implement this with auto-saving features.
        However, base PaperlessModel instances simply call update_locally.

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

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.
        """
        return f"{self._meta.name.capitalize()}"


class StandardModel(PaperlessModel, ABC):
    """
    Standard model for Paperless-ngx API objects with an ID field.

    Attributes:
        id: Unique identifier for the model.

    Returns:
        A new instance of StandardModel.

    Examples:
        from paperap.models.abstract.model import StandardModel
        class Document(StandardModel):
            filename: str
            contents : bytes
    """

    id: int = Field(description="Unique identifier from Paperless NGX", default=0)

    class Meta(PaperlessModel.Meta[_Self], Generic[_Self]):
        """
        Metadata for the StandardModel.

        Attributes:
            read_only_fields: Fields that should not be modified.
            supported_filtering_params: Params allowed during queryset filtering.
        """

        # Fields that should not be modified
        read_only_fields: ClassVar[set[str]] = {"id"}
        supported_filtering_params = {
            "id__in",
            "id",
        }

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

    def save(self) -> None:
        """
        Save this model instance within paperless ngx.

        Raises:
            ResourceNotFoundError: If the resource with the given id is not found

        Examples:
            # Save a Document instance
            doc = client.documents().get(1)
            doc.title = "New Title"
            doc.save()
        """
        # Safety measure to ensure we don't fall into an infinite loop of saving and updating
        # this check shouldn't strictly be necessary, but it future proofs this feature
        if self._meta.status == ModelStatus.SAVING:
            return

        with StatusContext(self, ModelStatus.SAVING):
            # Nothing has changed, so we can save ourselves a request
            if not self.is_dirty():
                return

            current_data = self.to_dict(include_read_only=False, exclude_none=False, exclude_unset=True)
            SignalRegistry.emit(
                "model.save:before",
                "Fired before the model data is sent to paperless ngx to be saved.",
                kwargs={
                    "model": self,
                    "current_data": current_data,
                },
            )

            new_model = self._meta.resource.update(self.id, current_data)
            new_data = new_model.to_dict()
            self.update_locally(from_db=True, **new_data)

            SignalRegistry.emit(
                "model.save:after",
                "Fired after the model data is saved in paperless ngx.",
                kwargs={
                    "model": self,
                    "previous_data": current_data,
                    "updated_data": new_data,
                },
            )

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

    def __setattr__(self, name, value):
        """
        Override attribute setting to automatically call save when attributes change.

        Args:
            name: Attribute name
            value: New attribute value
        """
        # Call parent's setattr
        super().__setattr__(name, value)

        # Skip for private attributes (those starting with underscore)
        if name.startswith("_"):
            return

        # Check if the model is initialized or is new
        if not hasattr(self, "_meta") or self.is_new():
            return

        # Settings may override this behavior
        if self._meta.save_on_write is False or self._meta.resource.client.settings.save_on_write is False:
            return

        # Only trigger a save if the model is in a ready status
        if self._meta.status != ModelStatus.READY:
            return

        # All attribute changes trigger a save automatically
        self.save()

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.
        """
        return f"{self._meta.name.capitalize()} #{self.id}"
