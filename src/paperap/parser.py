"""*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    parser.py                                                                                            *
*        Project: paperap                                                                                            *
*        Created: 2025-03-01                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-01     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************"""

from __future__ import annotations

import datetime
import logging
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast, get_type_hints, overload, get_origin, get_args
import types

import dateparser

if TYPE_CHECKING:
    from paperap.models.base import PaperlessModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class Parser:
    model: type["PaperlessModel"]

    def __init__(self, model: type["PaperlessModel"]):
        self.model = model

    def parse(self, value: Any, target_type: type[_T]) -> _T | None:
        if target_type is None:
            raise TypeError("Cannot parse to None type")

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
        if value is None:
            return None

        if isinstance(value, (str, int, float, Decimal)):
            return float(value)

        raise TypeError(f"Unsupported type: {type(value)}")

    def parse_data(self, data: dict[str, Any]) -> dict[str, Any]:
        fields = self._get_model_fields()
        for field, value in data.items():
            if field in fields:
                data[field] = self.parse(value, fields[field])
        return data

    def _get_model_fields(self) -> dict[str, type]:
        """Get all fields in the model."""
        hints = get_type_hints(self.model)
        fields = {}

        for field, type_hint in hints.items():
            # Handle Unions (both new syntax `int | None` and `Union[int, None]`)
            if isinstance(type_hint, types.UnionType) or getattr(type_hint, "__origin__", None) is Union:
                type_hint = next(arg for arg in getattr(type_hint, "__args__", ()) if arg is not type(None))

            fields[field] = type_hint

        return fields
