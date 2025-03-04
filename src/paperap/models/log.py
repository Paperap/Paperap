"""




----------------------------------------------------------------------------

   METADATA:

       File:    log.py
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

from typing import Any, Optional

from pydantic import BaseModel, Field

from paperap.models.base import PaperlessModel


class Log(PaperlessModel):
    """
    Represents a log entry in Paperless-NgX.
    """

    level: str
    message: str
    group: str | None = Field(default=None)
    time: str | None = Field(default=None)  # ISO format date
