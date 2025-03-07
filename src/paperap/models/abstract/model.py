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

from paperap.models.abstract.parser import Parser
from paperap.models.abstract.queryset import QuerySet

if TYPE_CHECKING:
    from paperap.resources.base import PaperlessResource, StandardResource
    from paperap.client import PaperlessClient

_Self = TypeVar("_Self", bound="PaperlessModel")

class FilteringStrategies(StrEnum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    ALLOW_ALL = "allow_all"
    ALLOW_NONE = "allow_none"

class PaperlessModel(BaseModel, ABC):
    """
    Base model for all Paperless-ngx API objects.

    Provides automatic serialization, deserialization, and API interactions
    with minimal configuration needed.

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
        # The name of the model.
        # It will default to the classname
        name: str
        # Fields that should not be modified. These will be appended to read_only_fields for all parent classes.
        read_only_fields: ClassVar[set[str]] = {"id", "created", "updated"}
        # Fields that are disabled by Paperless NGX for filtering. These will be appended to filtering_disabled for all parent classes.
        filtering_disabled : ClassVar[set[str]] = set()
        # Fields allowed for filtering. Generated automatically during class init.
        filtering_fields : ClassVar[set[str]] = set()
        # If set, only these params will be allowed during queryset filtering. (e.g. {"content__icontains", "id__gt"})
        # These will be appended to whitelist_filtering_params for all parent classes.
        supported_filtering_params : ClassVar[set[str]] = set()
        # If set, these params will be disallowed during queryset filtering (e.g. {"content__icontains", "id__gt"})
        # These will be appended to blaclist_filtering_params for all parent classes.
        blaclist_filtering_params : ClassVar[set[str]] = set()
        # Strategies for filtering. This determines which of the above lists will be used to allow or deny filters to QuerySets.
        filtering_strategies : ClassVar[set[FilteringStrategies]] = {FilteringStrategies.BLACKLIST}
        # the type of parser, which parses api data into appropriate types
        # this will usually not need to be overridden
        parser: type[Parser[_Self]] = Parser[_Self]
        resource: "PaperlessResource[_Self]"
        queryset: type[QuerySet[_Self]] = QuerySet

        def __init__(self, model : type[_Self]):
            self.model = model

            # Validate filtering strategies
            if FilteringStrategies.ALLOW_ALL in self.filtering_strategies and FilteringStrategies.ALLOW_NONE in self.filtering_strategies:
                raise ValueError(f"Cannot have both ALLOW_ALL and ALLOW_NONE filtering strategies. Model {self.model.__name__}")

        def filter_allowed(self, filter_param : str) -> bool:
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
                if self.blaclist_filtering_params and filter_param in self.blaclist_filtering_params:
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
        super().__init_subclass__(**kwargs)

        # Append read_only_fields from all parents to Meta
        # Same with filtering_disabled
        # Retrieve filtering_fields from the attributes of the class
        read_only_fields = (cls.Meta.read_only_fields or set()).copy()
        filtering_disabled = (cls.Meta.filtering_disabled or set()).copy()
        filtering_fields = set(cls.__annotations__.keys())
        whitelist_filtering_params = cls.Meta.supported_filtering_params
        blaclist_filtering_params = cls.Meta.blaclist_filtering_params
        for base in cls.__bases__:
            _meta : PaperlessModel.Meta | None
            if _meta := getattr(base, "Meta", None):
                if hasattr(_meta, "read_only_fields"):
                    read_only_fields.update(_meta.read_only_fields)
                if hasattr(_meta, "filtering_disabled"):
                    filtering_disabled.update(_meta.filtering_disabled)
                if hasattr(_meta, "filtering_fields"):
                    filtering_fields.update(_meta.filtering_fields)
                if hasattr(_meta, "supported_filtering_params"):
                    whitelist_filtering_params.update(_meta.supported_filtering_params)
                if hasattr(_meta, "blaclist_filtering_params"):
                    blaclist_filtering_params.update(_meta.blaclist_filtering_params)

        cls.Meta.read_only_fields = read_only_fields
        cls.Meta.filtering_disabled = filtering_disabled
        # excluding filtering_disabled from filtering_fields
        cls.Meta.filtering_fields = filtering_fields - filtering_disabled
        cls.Meta.supported_filtering_params = whitelist_filtering_params
        cls.Meta.blaclist_filtering_params = blaclist_filtering_params
        
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
        return self._meta.resource

    @property
    def _client(self) -> "PaperlessClient":
        return self._meta.resource.client

    def __init__(self, resource: "PaperlessResource", **data):
        if resource is None:
            raise ValueError("Resource is required for PaperlessModel")
        
        super().__init__(**data)
        self._meta.resource = resource

    @classmethod
    def from_dict(cls, data: dict[str, Any], resource: "PaperlessResource") -> Self:
        """
        Create a model instance from API response data.

        Args:
            data (dict[str, Any]): dictionary containing the API response data.

        Returns:
            A model instance initialized with the provided data.
        """
        return cls.model_validate({**data, "resource": resource})

    def to_dict(
        self, *, include_read_only: bool = True, exclude_none: bool = True, exclude_unset: bool = True
    ) -> dict[str, Any]:
        """
        Convert the model to a dictionary for API requests.

        Args:
            include_read_only (bool): Whether to include read-only fields.
            exclude_none (bool): Whether to exclude fields with None values.
            exclude_unset (bool): Whether to exclude fields that are not set.

        Returns:
            dict[str, Any]: dictionary with model data ready for API submission.
        """
        exclude = set() if include_read_only else set(self._meta.read_only_fields)

        return self.model_dump(
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
        Factory method to create a new model instance.

        Args:
            **kwargs: Field values to set.

        Returns:
            A new model instance.
        """
        # TODO save
        return cls(**kwargs)

    def update(self, **kwargs: Any) -> Self:
        """
        Update this model with new values.

        Args:
            **kwargs: New field values.

        Returns:
            Self with updated values.
        """
        # TODO save
        return self.model_copy(update=kwargs)

    @abstractmethod
    def is_new(self) -> bool:
        """
        Check if this model represents a new (unsaved) object.

        Returns:
            True if the model is new, False otherwise.
        """

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.
        """
        return f"{self._meta.name.capitalize()}"


class StandardModel(PaperlessModel, ABC):
    id: int = Field(description="Unique identifier", default=0)

    class Meta(PaperlessModel.Meta[_Self], Generic[_Self]):
        # Fields that should not be modified
        read_only_fields: ClassVar[set[str]] = {"id"}
        whitelist_filtering_params = {
            "id__in",
            "id",
        }

    def is_new(self) -> bool:
        """
        Check if this model represents a new (unsaved) object.

        Returns:
            True if the model is new, False otherwise.
        """
        return self.id == 0

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            A string representation of the model.
        """
        return f"{self._meta.name.capitalize()} #{self.id}"
