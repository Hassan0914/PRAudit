"""Centralized logging setup for PRAudit."""

import logging
import sys
from typing import Optional
from app.core.config import settings


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Create and configure a named logger.

    Args:
        name: The module or component name for the logger.
        level: Optional log level override (e.g. 'DEBUG', 'INFO').

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
