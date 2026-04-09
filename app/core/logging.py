"""Logging configuration for the application."""
import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure application logging.

    Args:
        level: Log level override (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger("conversation_ai")
    logger.setLevel(getattr(logging, log_level.upper()))

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"conversation_ai.{name}")


# Default logger instance
logger = setup_logging()