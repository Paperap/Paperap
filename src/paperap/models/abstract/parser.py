"""
----------------------------------------------------------------------------

   METADATA:

       File:    parser.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

import datetime
import logging
import types
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Union, cast, get_args, get_origin, get_type_hints, overload

import dateparser
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from paperap.models.abstract.model import BaseModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_BaseModel = TypeVar("_BaseModel", bound="BaseModel", default="BaseModel")


class Parser(Generic[_BaseModel]):
    """
    Parser for converting API data into model instances.

    Args:
        model: The model class to parse data into.

    Returns:
        A new instance of Parser.

    Raises:
        TypeError: If the target type is unsupported.

    Examples:
        # Create a parser for a Document model
        parser = Parser(Document)

    """

    model: type[_BaseModel]

    def __init__(self, model: type[_BaseModel]):
        self.model = model
        super().__init__()

    @property
    def _meta(self) -> "BaseModel.Meta":
        return self.model._meta # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access

    def parse(self, value: Any, target_type: type[_T]) -> _T | None:
        """
        Parse a value into the specified target type.

        Args:
            value: The value to parse.
            target_type: The type to parse the value into.

        Returns:
            The parsed value, or None if parsing fails.

        Raises:
            TypeError: If the target type is unsupported.

        Examples:
            # Parse a string into an integer
            result = parser.parse("123", int)

        """
        if target_type is types.NoneType:
            raise TypeError("Cannot parse to None type")

        if value is None:
            return None

        # Handle generic types (list[T], dict[K, V], set[T], tuple[T, ...])
        origin = get_origin(target_type)
        args = get_args(target_type)

        if str(target_type) == "typing.Any":
            return value
        if origin is list:
            return cast(_T, [self.parse(item, args[0]) for item in value])
        if origin is set:
            return cast(_T, {self.parse(item, args[0]) for item in value})
        if origin is tuple:
            return cast(_T, tuple(self.parse(item, arg) for item, arg in zip(value, args)))
        if origin is dict:
            key_type, value_type = args
            return cast(_T, {self.parse(k, key_type): self.parse(v, value_type) for k, v in value.items()})
        if target_type is str:
            return str(value)  # type: ignore
        if target_type is int:
            return self.parse_int(value)
        if target_type is float:
            return self.parse_float(value)
        if target_type is bool:
            return self.parse_bool(value)
        if target_type is datetime.datetime:
            return self.parse_datetime(value)  # type: ignore
        if target_type is datetime.date:
            return self.parse_date(value)  # type: ignore
        if target_type is type and issubclass(target_type, Enum):
            return self.parse_enum(value, target_type)

        # Allow subclasses to implement custom logic
        print(f'Calling parse_other on {value} (type {type(value)}) with target_type {target_type} (type {type(target_type)})')
        print(f'Origin: {origin}, args: {args}')
        return self.parse_other(value, target_type)

    def parse_other(self, value: Any, target_type: type[_T]) -> _T | None:
        """
        Parse a value into the specified target type.
        
        Subclasses may implement this. Raises a TypeError by default.
        """
        raise TypeError(f"Unsupported type: {target_type}")


    @overload
    def parse_datetime(self, value: str) -> datetime.datetime | None: ...

    @overload
    def parse_datetime(self, value: None) -> None: ...

    @overload
    def parse_datetime(self, value: datetime.datetime) -> datetime.datetime: ...

    def parse_datetime(self, value: str | datetime.datetime | None) -> datetime.datetime | None:
        """
        Parse a value into a datetime.

        Args:
            value: The value to parse.

        Returns:
            The parsed datetime, or None if parsing fails.

        Examples:
            # Parse a string into a datetime
            result = parser.parse_datetime("2025-03-04T12:00:00Z")

        """
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            try:
                parsed = dateparser.parse(value)
                if parsed is None:
                    logger.warning("Failed to parse datetime from: %s", value)
                return parsed
            except Exception as e:
                logger.warning("Error parsing datetime '%s': %s", value, e)
                return None
        return None

    @overload
    def parse_date(self, value: str) -> datetime.date | None: ...

    @overload
    def parse_date(self, value: None) -> None: ...

    @overload
    def parse_date(self, value: datetime.datetime) -> datetime.date: ...

    def parse_date(self, value: str | datetime.datetime | None) -> datetime.date | None:
        """
        Parse a value into a date.

        Args:
            value: The value to parse.

        Returns:
            The parsed date, or None if parsing fails.

        Examples:
            # Parse a string into a date
            result = parser.parse_date("2025-03-04")

        """
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value

        parsed_datetime = self.parse_datetime(value)
        if isinstance(parsed_datetime, datetime.datetime):
            return parsed_datetime.date()
        return parsed_datetime

    @overload
    def parse_enum(self, value: Enum, enum_type: type[Enum]) -> Enum: ...

    @overload
    def parse_enum(self, value: str | int, enum_type: type[Enum]) -> Enum | None: ...

    @overload
    def parse_enum(self, value: None, enum_type: type[Enum]) -> None: ...

    def parse_enum(self, value: Enum | str | int | None, enum_type: type[Enum]) -> Enum | None:
        """
        Parse a value into an enum.

        Args:
            value: The value to parse.
            enum_type: The enum type to parse the value into.

        Returns:
            The parsed enum, or None if parsing fails.

        Examples:
            # Parse a string into an enum
            result = parser.parse_enum("ENUM_VALUE", MyEnum)

        """
        if value is None:
            return None

        try:
            if isinstance(value, Enum):
                return value
            if isinstance(value, str):
                return enum_type[value]
            if isinstance(value, int):
                return enum_type(value)
        except (KeyError, ValueError) as e:
            logger.error("Failed to parse enum: %s", e)

        return None

    @overload
    def parse_bool(self, value: bool) -> bool: ...

    @overload
    def parse_bool(self, value: str | int) -> bool | None: ...

    @overload
    def parse_bool(self, value: None) -> None: ...

    def parse_bool(self, value: str | int | bool | None) -> bool | None:
        """
        Parse a value into a boolean.

        Args:
            value: The value to parse.

        Returns:
            The parsed boolean, or None if parsing fails.

        Examples:
            # Parse a string into a boolean
            result = parser.parse_bool("true")

        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ["true", "1"]:
                return True
            if value.lower() in ["false", "0"]:
                return False
            raise ValueError(f"Invalid boolean value: {value}")

        if isinstance(value, int):
            if value in [0, 1]:
                return bool(value)
            raise ValueError(f"Invalid boolean value: {value}")

        raise TypeError(f"Unsupported type: {type(value)}")

    @overload
    def parse_int(self, value: int | float | Decimal) -> int: ...

    @overload
    def parse_int(self, value: str) -> int | None: ...

    @overload
    def parse_int(self, value: None) -> None: ...

    def parse_int(self, value: int | float | Decimal | str | None) -> int | None:
        """
        Parse a value into an integer.

        Args:
            value: The value to parse.

        Returns:
            The parsed integer, or None if parsing fails.

        Examples:
            # Parse a string into an integer
            result = parser.parse_int("123")

        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, Decimal)):
            return int(value)

        raise TypeError(f"Unsupported type: {type(value)}")

    @overload
    def parse_float(self, value: float | int | Decimal) -> float: ...

    @overload
    def parse_float(self, value: str) -> float | None: ...

    @overload
    def parse_float(self, value: None) -> None: ...

    def parse_float(self, value: int | float | Decimal | str | None) -> float | None:
        """
        Parse a value into a float.

        Args:
            value: The value to parse.

        Returns:
            The parsed float, or None if parsing fails.

        Examples:
            # Parse a string into a float
            result = parser.parse_float("123.45")

        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, Decimal)):
            return float(value)

        raise TypeError(f"Unsupported type: {type(value)}")

    def parse_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a dictionary of data into the appropriate types.

        Args:
            data: The data to parse.

        Returns:
            The parsed data.

        Examples:
            # Parse a dictionary of data
            parsed_data = parser.parse_data(api_data)

        """
        fields = self._get_model_fields()
        for field, value in data.items():
            if field in fields:
                data[field] = self.parse(value, fields[field])

        return self.transform_input_data(data)

    def transform_input_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform the data before it is validated and parsed.

        Subclasses can override this method to transform the data before it is validated and parsed.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        """
        for key, attrib in self._meta.field_map.items():
            # Change {key} to {attrib}
            if key in data:
                data[attrib] = data.pop(key)
        return data

    def transform_output_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform the data before it is serialized.

        Subclasses can override this method to transform the data before it is serialized.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        """
        for key, attrib in self._meta.field_map.items():
            # Change {attrib} to {key}
            if key in data:
                data[key] = data.pop(attrib)
        return data

    def _get_model_fields(self) -> dict[str, type]:
        """
        Get all fields in the model.

        Returns:
            A dictionary of field names and their types.

        """
        # Use a class-level cache to improve performance
        if cache := self.model.Meta.__type_hints_cache__:
            return cache
        
        hints = self.model.__annotations__
        fields : dict[str, type] = {}

        for field, type_hint in hints.items():
            # Handle Unions (both new syntax `int | None` and `Union[int, None]`)
            if isinstance(type_hint, types.UnionType) or getattr(type_hint, "__origin__", None) is Union:
                type_hint = next(arg for arg in getattr(type_hint, "__args__", ()) if arg is not type(None))

            fields[field] = type_hint
            
        # Cache the processed type hints
        self.model.Meta.__type_hints_cache__ = fields
        return fields
