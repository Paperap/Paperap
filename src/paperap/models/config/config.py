"""




----------------------------------------------------------------------------

   METADATA:

       File:    config.py
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

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from paperap.models.abstract.model import StandardModel


class Config(StandardModel):
    user_args: str | None = None
    output_type: str | None = None
    pages: str | None = None
    language: str | None = None
    mode: str | None = None
    skip_archive_file: bool | None = None
    image_dpi: int | None = None
    unpaper_clean: bool | None = None
    deskew: bool
    rotate_pages: bool
    rotate_pages_threshold: int | None = None
    max_image_pixels: int | None = None
    color_conversion_strategy: str | None = None
    app_title: str
    app_logo: str
