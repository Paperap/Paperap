"""




----------------------------------------------------------------------------

   METADATA:

       File:    queryset.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
import logging
from paperap.models.abstract.queryset import QuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.profile.model import Profile

logger = logging.getLogger(__name__)


class ProfileQuerySet(StandardQuerySet["Profile"]):
    """
    A lazy-loaded, chainable query interface for Profile resources in Paperless NGX.

    Provides pagination, filtering, and caching functionality similar to Django's QuerySet.
    Designed to be lazy - only fetching data when it's actually needed.

    Examples:
        >>> profiles = ProfileQuerySet()
        >>> profiles = profiles.email("example@example.com")
        >>> for profile in profiles:
        >>>     print(profile.first_name)
    """

    def email(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """Filter by email.

        Args:
            value: The email to filter by.
            exact: Whether to filter by an exact match.
            case_insensitive: Whether the match should be case insensitive.

        Returns:
            A new ProfileQuerySet instance with the filter applied.

        Examples:
            >>> profiles = ProfileQuerySet()
            >>> profiles = profiles.email("example@example.com")
        Filter by email.

        Args:
            email: The email to filter by.
            exact: Whether to filter by an exact match.

        Returns:
            A new ProfileQuerySet instance with the filter applied.
        """Filter by first name.

        Args:
            value: The first name to filter by.
            exact: Whether to filter by an exact match.
            case_insensitive: Whether the match should be case insensitive.

        Returns:
            A new ProfileQuerySet instance with the filter applied.

        Examples:
            >>> profiles = ProfileQuerySet()
            >>> profiles = profiles.first_name("John")
        return self.filter_field_by_str("email", value, exact=exact, case_insensitive=case_insensitive)

    def first_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """Filter by last name.

        Args:
            value: The last name to filter by.
            exact: Whether to filter by an exact match.
            case_insensitive: Whether the match should be case insensitive.

        Returns:
            A new ProfileQuerySet instance with the filter applied.

        Examples:
            >>> profiles = ProfileQuerySet()
            >>> profiles = profiles.last_name("Doe")
        Filter by first name.

        Args:
            first_name: The first name to filter by.
            exact: Whether to filter by an exact match.

        Returns:
            A new ProfileQuerySet instance with the filter applied.
        """Filter by has usable password.

        Args:
            value: Whether the profile should have a usable password.

        Returns:
            A new ProfileQuerySet instance with the filter applied.

        Examples:
            >>> profiles = ProfileQuerySet()
            >>> profiles = profiles.has_usable_password(True)
        return self.filter_field_by_str("first_name", value, exact=exact, case_insensitive=case_insensitive)

    def last_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """
        Filter by last name.

        Args:
            last_name: The last name to filter by.
            exact: Whether to filter by an exact match.

        Returns:
            A new ProfileQuerySet instance with the filter applied.
        """
        return self.filter_field_by_str("last_name", value, exact=exact, case_insensitive=case_insensitive)

    def has_usable_password(self, value: bool = True) -> ProfileQuerySet:
        """
        Filter by has usable password.

        Args:
            has_usable_password: The has usable password to filter by.

        Returns:
            A new ProfileQuerySet instance with the filter applied.
        """
        return self.filter(has_usable_password=value)
