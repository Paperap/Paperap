

from __future__ import annotations

from paperap.models.profile import Profile, ProfileQuerySet
from paperap.resources.base import StandardResource


class ProfileResource(StandardResource[Profile, ProfileQuerySet]):
    """Resource for managing profiles."""

    model_class = Profile
    queryset_class = ProfileQuerySet
    name: str = "profiles"
