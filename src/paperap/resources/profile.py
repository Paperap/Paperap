"""
Profile Resource Module.

This module provides the ProfileResource class for managing user profiles in Paperless-NgX.
It extends the StandardResource class to provide standard CRUD operations for profile management.

The profile resource allows access to user profile settings and preferences in the
Paperless-NgX system, including notification settings, display preferences, and other
user-specific configurations.
"""

from __future__ import annotations

from paperap.models.profile import Profile, ProfileQuerySet
from paperap.resources.base import BaseResource, StandardResource


class ProfileResource(StandardResource[Profile, ProfileQuerySet]):
    """
    Resource for managing user profiles in Paperless-NgX.

    This class provides methods to interact with the profile-related endpoints
    of the Paperless-NgX API. It allows for retrieving, creating, updating,
    and deleting user profiles, as well as querying profiles with various filters.

    User profiles contain settings and preferences specific to each user in the
    Paperless-NgX system, such as display preferences, notification settings,
    and other user-specific configurations.

    Attributes:
        model_class (Type[Profile]): The Profile model class used for serialization/deserialization.
        queryset_class (Type[ProfileQuerySet]): The ProfileQuerySet class used for querying profiles.
        name (str): The resource name used in API endpoints (typically "profile").

    Example:
        To use this resource, instantiate a PaperlessClient and access
        the profiles resource:

        >>> client = PaperlessClient()
        >>> # Get all profiles
        >>> profiles = client.profiles.all()
        >>> for profile in profiles:
        >>>     print(f"Profile ID: {profile.id}, Owner: {profile.owner}")
        >>>
        >>> # Get a specific profile by ID
        >>> my_profile = client.profiles.get(1)
        >>>
        >>> # Update a profile
        >>> my_profile.settings = {"theme": "dark"}
        >>> my_profile.save()

    """

    model_class = Profile
    queryset_class = ProfileQuerySet
    name: str = "profile"
