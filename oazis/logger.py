"""Centralized Loguru configuration."""

import sys
from loguru import logger


def configure_logging(debug: bool = False) -> None:
    """Configure Loguru sinks and formatting."""
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        level=level,
        backtrace=debug,
        diagnose=debug,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}",
    )

