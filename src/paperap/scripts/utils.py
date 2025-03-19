"""




----------------------------------------------------------------------------

METADATA:

File:    utils.py
        Project: paperap
Created: 2025-03-18
        Version: 0.0.8
Author:  Jess Mann
Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

LAST MODIFIED:

2025-03-18     By Jess Mann

"""

import logging
from typing import override

import colorlog


def setup_logging() -> logging.Logger:
    """
    Set up logging with colored output.
    """
    logging.basicConfig(level=logging.ERROR)

    # Define a custom formatter class
    class CustomFormatter(colorlog.ColoredFormatter):
        @override
        def format(self, record):
            self._style._fmt = "(%(log_color)s%(levelname)s%(reset)s) %(message)s"
            return super().format(record)

    # Configure colored logging with the custom formatter
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        CustomFormatter(
            # Initial format string (will be overridden in the formatter)
            "",
            log_colors={
                "DEBUG": "green",
                "INFO": "blue",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.ERROR)

    app_logger = logging.getLogger(__name__)
    app_logger.setLevel(logging.INFO)

    # Suppress logs from the 'requests' library below ERROR level
    # logging.getLogger("urllib3").setLevel(logging.ERROR)
    # logging.getLogger("requests").setLevel(logging.ERROR)

    return app_logger
