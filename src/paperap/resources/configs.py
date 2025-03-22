"""
----------------------------------------------------------------------------

   METADATA:

       File:    configs.py
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

from paperap.models.config import Config
from paperap.resources.base import StandardResource


class ConfigResource(StandardResource[Config]):
    """Resource for managing configs."""

    model_class = Config
    name: str = "configs"
