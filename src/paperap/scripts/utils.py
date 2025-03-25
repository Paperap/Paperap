"""
Utility functions for Paperap command-line scripts.

This module provides common utilities used across Paperap CLI scripts,
including logging setup and progress bar interfaces.
"""

import logging
from typing import Any, Protocol, override

import colorlog


class ProgressBar(Protocol):
    """
    Protocol defining the interface for progress bar implementations.

    This protocol defines the expected interface for progress bar objects,
    compatible with libraries like alive-progress. It allows for dependency
    injection of different progress bar implementations.

    Attributes:
        total: The total number of items to process.

    """

    total: int

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """
        Update the progress bar.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        """
        ...

    def text(self, text: str) -> None:
        """
        Set the text displayed alongside the progress bar.

        Args:
            text: The text to display.

        """
        ...


def setup_logging() -> logging.Logger:
    """
    Set up logging with colored output for CLI applications.

    Configures a root logger with colored output using the colorlog package.
    Sets appropriate log levels for the application and third-party libraries.

    Returns:
        A configured logger instance for the application.

    Example:
        ```python
        logger = setup_logging()
        logger.info("Starting application")
        logger.error("An error occurred")
        ```

    """
    logging.basicConfig(level=logging.ERROR)

    # Define a custom formatter class
    class CustomFormatter(colorlog.ColoredFormatter):
        @override
        def format(self, record: logging.LogRecord) -> str:
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
