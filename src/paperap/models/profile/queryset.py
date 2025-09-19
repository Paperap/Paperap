"""
Provide query interface for Profile resources in Paperless-NGX.

This module contains the ProfileQuerySet class which extends StandardQuerySet
to provide profile-specific filtering methods for efficient querying of user
profiles in the Paperless-NGX system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.profile.model import Profile

logger = logging.getLogger(__name__)


class ProfileQuerySet(StandardQuerySet["Profile"]):
    """
    Implement a lazy-loaded, chainable query interface for Profile resources.

    Extends StandardQuerySet to provide profile-specific filtering methods,
    allowing for efficient querying of user profiles in the Paperless-NGX system.
    Following the lazy-loading pattern, data is only fetched when actually needed.

    Attributes:
        Inherits all attributes from StandardQuerySet.

    Examples:
        Get all profiles:
            >>> profiles = client.profiles()

        Filter profiles by email:
            >>> profiles = client.profiles().email("example@example.com")

        Iterate through results:
            >>> for profile in profiles:
            >>>     print(profile.first_name)

    """

    def email(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """
        Filter profiles by email address.

        Args:
            value: The email address or pattern to filter by.
            exact: Whether to filter by an exact match (True) or partial match (False).
                Defaults to True.
            case_insensitive: Whether the match should be case insensitive.
                Defaults to True.

        Returns:
            A new ProfileQuerySet instance with the email filter applied.

        Examples:
            Exact match (default):
                >>> profiles = client.profiles().email("john.doe@gmail.com")

            Partial match (contains):
                >>> profiles = client.profiles().email("gmail.com", exact=False)

            Case-sensitive match:
                >>> profiles = client.profiles().email("John.Doe@gmail.com", case_insensitive=False)

        """
        return self.filter_field_by_str("email", value, exact=exact, case_insensitive=case_insensitive)

    def first_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """
        Filter profiles by first name.

        Args:
            value: The first name or pattern to filter by.
            exact: Whether to filter by an exact match (True) or partial match (False).
                Defaults to True.
            case_insensitive: Whether the match should be case insensitive.
                Defaults to True.

        Returns:
            A new ProfileQuerySet instance with the first name filter applied.

        Examples:
            Exact match (default):
                >>> profiles = client.profiles().first_name("John")

            Partial match (contains):
                >>> profiles = client.profiles().first_name("Jo", exact=False)

            Case-sensitive match:
                >>> profiles = client.profiles().first_name("John", case_insensitive=False)

        """
        return self.filter_field_by_str("first_name", value, exact=exact, case_insensitive=case_insensitive)

    def last_name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> ProfileQuerySet:
        """
        Filter profiles by last name.

        Args:
            value: The last name or pattern to filter by.
            exact: Whether to filter by an exact match (True) or partial match (False).
                Defaults to True.
            case_insensitive: Whether the match should be case insensitive.
                Defaults to True.

        Returns:
            A new ProfileQuerySet instance with the last name filter applied.

        Examples:
            Exact match (default):
                >>> profiles = client.profiles().last_name("Doe")

            Partial match (contains):
                >>> profiles = client.profiles().last_name("Do", exact=False)

            Case-sensitive match:
                >>> profiles = client.profiles().last_name("Doe", case_insensitive=False)

        """
        return self.filter_field_by_str("last_name", value, exact=exact, case_insensitive=case_insensitive)

    def has_usable_password(self, value: bool = True) -> ProfileQuerySet:
        """
        Filter profiles by whether they have a usable password.

        Distinguish between local user accounts and those authenticated through
        external systems (like OAuth or LDAP) based on password usability.

        Args:
            value: True to find profiles with usable passwords, False to find
                profiles without usable passwords. Defaults to True.

        Returns:
            A new ProfileQuerySet instance with the password usability filter applied.

        Examples:
            Find profiles with usable passwords (local accounts):
                >>> profiles = client.profiles().has_usable_password()

            Find profiles without usable passwords (external auth):
                >>> profiles = client.profiles().has_usable_password(False)

        """
        return self.filter(has_usable_password=value)
