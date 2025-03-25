"""
Profiles Resource Module.

This module provides the ProfileResource class for managing user profiles in Paperless-NgX.
It extends the StandardResource class to provide standard CRUD operations for profile management.

The profile resource allows access to user profile settings and preferences in the
Paperless-NgX system, including notification settings, display preferences, and other
user-specific configurations.
"""

from __future__ import annotations

from paperap.models.profile import Profile, ProfileQuerySet
from paperap.resources.base import StandardResource


class ProfileResource(StandardResource[Profile, ProfileQuerySet]):
    """
    Resource for managing user profiles in Paperless-NgX.

    This class provides methods for interacting with the profiles API endpoint,
    including retrieving, updating, and deleting user profile resources. Each user
    in Paperless-NgX has an associated profile that contains user-specific settings
    and preferences.

    Attributes:
        model_class (type): The Profile model class used for instantiating profile objects.
        queryset_class (type): The ProfileQuerySet class used for query operations.
        name (str): The resource name used in API endpoints ('profiles').

    Examples:
        Get the current user's profile:

        >>> profile = client.profiles().first()
        >>> print(f"User settings: {profile.settings}")

        Update profile settings:

        >>> profile = client.profiles().get(1)
        >>> profile.update(settings={"notifications_enabled": True})
        >>> profile.save()

    """

    model_class = Profile
    queryset_class = ProfileQuerySet
    name: str = "profiles"
