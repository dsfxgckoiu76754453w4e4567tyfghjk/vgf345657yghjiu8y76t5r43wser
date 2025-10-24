"""Environment-aware logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure environment-based logging.

    - Development: DEBUG level, colored output, verbose
    - Test: INFO level, structured JSON
    - Production: WARNING level, JSON, minimal output
    """
    # Determine processors based on environment
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Environment-specific configuration
    if settings.environment == "dev":
        # Development: Colored, human-readable
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
        log_level = logging.DEBUG
    elif settings.environment == "test":
        # Test: Structured JSON
        processors.append(structlog.processors.JSONRenderer())
        log_level = logging.INFO
    else:  # production
        # Production: JSON, minimal
        processors.append(structlog.processors.JSONRenderer())
        log_level = logging.WARNING

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Set third-party loggers to WARNING to reduce noise
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "httpx",
        "httpcore",
        "sqlalchemy",
        "alembic",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
