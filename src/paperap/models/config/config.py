"""
Configuration model for Paperless-NgX system settings.

This module provides the Config model class for interacting with the Paperless-NgX
configuration API endpoint. It allows retrieving and modifying system-wide settings
that control document processing, OCR behavior, and application appearance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paperap.models.abstract.model import StandardModel


class Config(StandardModel):
    """
    Model representing Paperless-NgX system configuration settings.

    This model provides access to system-wide configuration settings that control
    document processing, OCR behavior, and application appearance. These settings
    correspond to those available in the Paperless-NgX admin interface.

    Attributes:
        user_args (str | None): Custom arguments passed to the OCR engine.
        output_type (str | None): Default output format for OCR results (e.g., "pdfa", "pdf").
        pages (str | None): Page range specification for OCR processing (e.g., "1,3-5").
        language (str | None): Default OCR language code (e.g., "eng", "deu").
        mode (str | None): OCR processing mode (e.g., "skip", "redo", "force").
        skip_archive_file (bool | None): Whether to skip creating archive files.
        image_dpi (int | None): DPI setting for image processing.
        unpaper_clean (bool | None): Whether to use unpaper for document cleaning.
        deskew (bool): Whether to automatically deskew (straighten) documents.
        rotate_pages (bool): Whether to automatically rotate pages to the correct orientation.
        rotate_pages_threshold (int | None): Confidence threshold for automatic page rotation.
        max_image_pixels (int | None): Maximum number of pixels to process in images.
        color_conversion_strategy (str | None): Strategy for color conversion (e.g., "none", "grayscale").
        app_title (str): Custom title for the Paperless-NgX web application.
        app_logo (str): Custom logo path for the Paperless-NgX web application.

    Examples:
        Retrieve current system configuration:

        ```python
        config = client.config.get()
        print(f"Current OCR language: {config.language}")
        ```

        Update system configuration:

        ```python
        config = client.config.get()
        config.language = "eng+deu"  # Set OCR to use English and German
        config.deskew = True         # Enable automatic document straightening
        config.save()
        ```

    """

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
