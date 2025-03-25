

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

from paperap.utils import datetime_to_str, parse_filter_params


class TestDatetimeToStr(unittest.TestCase):
    """
    Test the datetime_to_str function.

    Written By claude
    """

    def test_none_input(self) -> None:
        """
        Test that None input returns None.

        Written By claude
        """
        self.assertIsNone(datetime_to_str(None))

    def test_utc_datetime(self) -> None:
        """
        Test conversion of UTC datetime to ISO 8601 string.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56, tzinfo=timezone.utc)
        expected = "2025-03-21T12:34:56Z"
        self.assertEqual(datetime_to_str(dt), expected)

    def test_naive_datetime(self) -> None:
        """
        Test conversion of naive datetime to ISO 8601 string.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56)
        expected = "2025-03-21T12:34:56"
        self.assertEqual(datetime_to_str(dt), expected)

    def test_microseconds(self) -> None:
        """
        Test that microseconds are included in the output.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56, 789000)
        expected = "2025-03-21T12:34:56.789000"
        self.assertEqual(datetime_to_str(dt), expected)

    def test_timezone_conversion(self) -> None:
        """
        Test that +00:00 is converted to Z in the output.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56, tzinfo=timezone.utc)
        result = datetime_to_str(dt)
        self.assertIn("Z", result)
        self.assertNotIn("+00:00", result)


class TestParseFilterParams(unittest.TestCase):
    """
    Test the parse_filter_params function.

    Written By claude
    """

    def test_empty_params(self) -> None:
        """
        Test that empty parameters return an empty dictionary.

        Written By claude
        """
        result = parse_filter_params()
        self.assertEqual(result, {})

    def test_none_values_excluded(self) -> None:
        """
        Test that None values are excluded from the result.

        Written By claude
        """
        result = parse_filter_params(param1="value", param2=None)
        self.assertEqual(result, {"param1": "value"})

    def test_datetime_conversion(self) -> None:
        """
        Test that datetime objects are converted to ISO 8601 strings.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56, tzinfo=timezone.utc)
        result = parse_filter_params(created_at=dt)
        self.assertEqual(result, {"created_at": "2025-03-21T12:34:56Z"})

    def test_list_conversion(self) -> None:
        """
        Test that lists are converted to comma-separated strings.

        Written By claude
        """
        result = parse_filter_params(tags__id__in=[1, 2, 3])
        self.assertEqual(result, {"tags__id__in": "1,2,3"})

    def test_mixed_types(self) -> None:
        """
        Test handling of mixed parameter types.

        Written By claude
        """
        dt = datetime(2025, 3, 21, 12, 34, 56, tzinfo=timezone.utc)
        result = parse_filter_params(
            created_at=dt,
            tags__id__in=[1, 2, 3],
            name="Test Document",
            is_active=True,
            count=42,
            none_param=None
        )

        expected = {
            "created_at": "2025-03-21T12:34:56Z",
            "tags__id__in": "1,2,3",
            "name": "Test Document",
            "is_active": True,
            "count": 42
        }

        self.assertEqual(result, expected)

    def test_list_with_different_types(self) -> None:
        """
        Test that lists with different types are properly converted.

        Written By claude
        """
        result = parse_filter_params(mixed_list=[1, "two", True])
        self.assertEqual(result, {"mixed_list": "1,two,True"})


if __name__ == "__main__":
    unittest.main()
