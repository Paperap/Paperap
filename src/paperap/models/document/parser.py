"""
----------------------------------------------------------------------------

   METADATA:

       File:    parser.py
        Project: paperap
       Created: 2025-03-08
        Version: 0.0.4
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-08     By Jess Mann

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast, override

from typing_extensions import TypeVar

from paperap.models.abstract.parser import Parser

if TYPE_CHECKING:
    from paperap.models.document.model import Document


class CustomFieldDict(TypedDict):
    field: int
    value: Any


_T = TypeVar("_T")


class DocumentParser(Parser["Document"]):
    """
    Parser for Document model instances.

    Provides methods to parse various types of data into Document model instances.
    """
    
    @override
    def parse_other(self, value: Any, target_type: type[_T]) -> _T | None:
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
        if target_type is CustomFieldDict:
            try:
                # I can't see why cast is necessary here. TODO
                return cast(_T, CustomFieldDict(field=int(value["field"]), value=value["value"]))
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid custom field: {value}") from e

        if target_type.__name__ == "DocumentNote":
            # Conditionally import DocumentNote (TODO: This is a hack to avoid a circular import)
            if not hasattr(self, "_document_note_class"):
                from paperap.models.document.model import DocumentNote  # pylint: disable=import-outside-toplevel

                self._document_note_class = DocumentNote # type: ignore # pylint: disable=attribute-defined-outside-init
            return cast(_T, self._document_note_class.from_dict(value))

        return super().parse_other(value, target_type)
