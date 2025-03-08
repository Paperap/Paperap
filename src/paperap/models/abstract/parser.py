"""




----------------------------------------------------------------------------

   METADATA:

       File:    parser.py
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

from typing import TYPE_CHECKING, Any, Generic, Union, cast, get_type_hints, overload, get_origin, get_args
from typing_extensions import TypeVar
import types
import datetime
import logging
from decimal import Decimal
from enum import Enum
import dateparser

if TYPE_CHECKING:
    from paperap.models.abstract.model import PaperlessModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_PaperlessModel = TypeVar("_PaperlessModel", bound="PaperlessModel", default="PaperlessModel")


class Parser(Generic[_PaperlessModel]):
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

    model: type[_PaperlessModel]

    def __init__(self, model: type[_PaperlessModel]):
        self.model = model

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
        if target_type is None:
            raise TypeError("Cannot parse to None type")

        if value is None:
            return None

        # Handle generic types (list[T], dict[K, V], set[T], tuple[T, ...])
        origin = get_origin(target_type)
        args = get_args(target_type)

        if target_type is Any:
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
        if issubclass(target_type, Enum):
            return self.parse_enum(value, target_type)

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
            parsed = dateparser.parse(value)
            if parsed is None:
                logger.warning(f"Failed to parse datetime from: {value}")
            return parsed
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
            logger.error(f"Failed to parse enum: {e}")

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
        return data

    def _get_model_fields(self) -> dict[str, type]:
        """
        Get all fields in the model.

        Returns:
            A dictionary of field names and their types.
        """
        hints = get_type_hints(self.model)
        fields = {}

        for field, type_hint in hints.items():
            # Handle Unions (both new syntax `int | None` and `Union[int, None]`)
            if isinstance(type_hint, types.UnionType) or getattr(type_hint, "__origin__", None) is Union:
                type_hint = next(arg for arg in getattr(type_hint, "__args__", ()) if arg is not type(None))

            fields[field] = type_hint

        return fields
