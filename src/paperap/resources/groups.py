"""
----------------------------------------------------------------------------

   METADATA:

       File:    groups.py
        Project: paperap
       Created: 2025-03-21
        Version: 0.0.9
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-21     By Jess Mann

"""

from __future__ import annotations

from paperap.models.user import Group, GroupQuerySet
from paperap.resources.base import StandardResource


class GroupResource(StandardResource[Group, GroupQuerySet]):
    """Resource for managing groups."""

    model_class = Group
    queryset_class = GroupQuerySet
    name: str = "groups"
