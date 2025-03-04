"""




----------------------------------------------------------------------------

   METADATA:

       File:    __init__.py
       Project: paperap
       Created: 2025-03-04
       Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from paperap.exceptions import APIError, AuthenticationError, PaperlessException, ResourceNotFoundError
from paperap import models
from paperap.client import PaperlessClient

__version__ = "0.1.0"
__all__ = ["PaperlessClient"]
