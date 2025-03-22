"""
----------------------------------------------------------------------------

   METADATA:

       File:    __init__.py
        Project: paperap
       Created: 2025-03-04
        Version: 0.0.8
       Author:  Jess Mann
       Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from paperap import models
from paperap.client import PaperlessClient
from paperap.exceptions import APIError, AuthenticationError, PaperapError, ResourceNotFoundError
from paperap.plugins.manager import PluginManager

__version__ = "0.1.0"
__all__ = ["PaperlessClient"]
