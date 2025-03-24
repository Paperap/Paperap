"""
Module for configuration resource management.

This module provides the ConfigResource class, a specialized resource for handling
configuration objects within the Paperless-NgX API. It encapsulates common CRUD operations and
offers a consistent interface for interacting with configuration settings.

Example:
    from paperap.resources.configs import ConfigResource
    config_resource = ConfigResource(client)
    config = config_resource.get(1)
    print(config)

"""

from __future__ import annotations
from paperap.models.config import Config
from paperap.resources.base import StandardResource


class ConfigResource(StandardResource[Config]):
    """
    Resource for managing configuration objects.

    This class provides a concrete implementation of StandardResource to handle configuration (Config)
    objects in a Paperless-NgX system. It encapsulates common CRUD operations, ensuring that configuration
    settings can be reliably created, retrieved, updated, and deleted with minimal configuration.

    Attributes:
        model_class (Type[Config]): The model class representing configuration objects.
        name (str): The API endpoint name used to access configuration-related resources.

    Example:
        >>> from paperap.resources.configs import ConfigResource
        >>> config_resource = ConfigResource(client)
        >>> config = config_resource.get(1)
        >>> print(config)

    """

    model_class = Config
    name: str = "configs"
