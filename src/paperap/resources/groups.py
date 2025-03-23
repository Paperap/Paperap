

from __future__ import annotations

from paperap.models.user import Group, GroupQuerySet
from paperap.resources.base import StandardResource


class GroupResource(StandardResource[Group, GroupQuerySet]):
    """Resource for managing groups."""

    model_class = Group
    queryset_class = GroupQuerySet
    name: str = "groups"
