

from __future__ import annotations

from paperap.models.config import Config
from paperap.resources.base import StandardResource


class ConfigResource(StandardResource[Config]):
    """Resource for managing configs."""

    model_class = Config
    name: str = "configs"
