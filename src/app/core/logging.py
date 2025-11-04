"""
Custom logging configuration following the project standard.

Logging Format:
    [UTC][IR][level] message [logger] key=value...

Example:
    [2025-11-04 16:00:49.458807 UTC][1404-08-14 19:30:49.458807 IR][info] scheduler_started [__main__] jobs=2
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

import jdatetime
import pytz
import structlog
from structlog.types import EventDict, Processor

from app.core.config import settings


# ANSI color codes (16-color standard for max compatibility)
class Colors:
    """ANSI 16-color codes for terminal output."""

    # Timestamp colors
    UTC = "\033[36m"  # Cyan
    IR = "\033[34m"  # Blue

    # Level colors
    DEBUG = "\033[90m"  # Gray
    INFO = "\033[32m"  # Green
    WARN = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red

    # Reset
    RESET = "\033[0m"

    @staticmethod
    def is_tty() -> bool:
        """Check if stdout is a TTY (terminal)."""
        return sys.stdout.isatty()


def add_dual_timestamps(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add both UTC and Iranian (Jalali) timestamps to the log event.

    Format:
        UTC: [YYYY-MM-DD HH:MM:SS.μs UTC]
        IR:  [JYYYY-JMM-JDD HH:MM:SS.μs IR]
    """
    now_utc = datetime.now(timezone.utc)

    # UTC timestamp with microseconds
    utc_str = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")  # Keep all 6 digits (microseconds)
    event_dict["timestamp_utc"] = f"{utc_str} UTC"

    # Iranian timestamp (UTC+3:30)
    iran_tz = pytz.timezone("Asia/Tehran")
    now_iran = now_utc.astimezone(iran_tz)

    # Convert to Jalali calendar
    jalali = jdatetime.datetime.fromgregorian(
        year=now_iran.year,
        month=now_iran.month,
        day=now_iran.day,
        hour=now_iran.hour,
        minute=now_iran.minute,
        second=now_iran.second,
        microsecond=now_iran.microsecond,
    )

    # Format: JYYYY-JMM-JDD HH:MM:SS.μs IR with microseconds
    ir_str = jalali.strftime("%Y-%m-%d %H:%M:%S.%f")  # Keep all 6 digits (microseconds)
    event_dict["timestamp_ir"] = f"{ir_str} IR"

    return event_dict


def format_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Format log level to lowercase without padding: [debug]/[info]/[warn]/[error]."""
    level = event_dict.get("level", "info")
    # Map WARNING to warn for consistency
    if level.upper() == "WARNING":
        level = "warn"
    event_dict["level"] = level.lower()
    return event_dict


class CustomConsoleRenderer:
    """
    Custom renderer that outputs logs in the project standard format.

    Format: [UTC][IR][level] message [logger] key=value...
    """

    def __init__(self, colors: bool = True):
        """
        Initialize the renderer.

        Args:
            colors: Enable ANSI colors (auto-disabled if not TTY)
        """
        self._colors_enabled = colors and Colors.is_tty()

    def __call__(self, logger: Any, name: str, event_dict: EventDict) -> str:
        """Render the log event to a string."""
        # Extract components
        utc = event_dict.pop("timestamp_utc", "")
        ir = event_dict.pop("timestamp_ir", "")
        level = event_dict.pop("level", "info")
        logger_name = event_dict.pop("logger", "")
        event = event_dict.pop("event", "")

        # Build the timestamp and level prefix (no spaces between brackets)
        if self._colors_enabled:
            prefix = f"{Colors.UTC}[{utc}]{Colors.RESET}{Colors.IR}[{ir}]{Colors.RESET}"
        else:
            prefix = f"[{utc}][{ir}]"

        # Level with color
        level_color = {
            "debug": Colors.DEBUG,
            "info": Colors.INFO,
            "warn": Colors.WARN,
            "error": Colors.ERROR,
        }.get(level, "")

        if self._colors_enabled and level_color:
            prefix += f"{level_color}[{level}]{Colors.RESET}"
        else:
            prefix += f"[{level}]"

        # Build the rest of the log line with spaces
        parts = [event]

        # Logger name (if present)
        if logger_name:
            parts.append(f"[{logger_name}]")

        # Key-value pairs (remaining fields)
        for key, value in sorted(event_dict.items()):
            # Skip internal structlog fields
            if key.startswith("_"):
                continue
            parts.append(f"{key}={value}")

        # Combine prefix and parts
        return prefix + " " + " ".join(parts)


class JSONRenderer:
    """JSON renderer for production/test environments."""

    def __call__(self, logger: Any, name: str, event_dict: EventDict) -> str:
        """Render the log event as JSON."""
        import json

        return json.dumps(event_dict, default=str)


def setup_logging() -> None:
    """
    Configure logging with the project standard.

    Format: [UTC][IR][level] message [logger] key=value...

    - Development: Colored console output with dual timestamps
    - Test: JSON output for structured logging
    - Production: JSON output with minimal verbosity
    """
    # Base processors (always applied)
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_dual_timestamps,  # Add UTC and IR timestamps
        format_log_level,  # Format level consistently
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Environment-specific configuration
    if settings.environment == "dev":
        # Development: Colored console with custom format
        processors.append(CustomConsoleRenderer(colors=True))
        log_level = logging.DEBUG
    elif settings.environment == "test":
        # Test: Structured JSON
        processors.append(JSONRenderer())
        log_level = logging.INFO
    else:  # production
        # Production: JSON, minimal
        processors.append(JSONRenderer())
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
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_login", user_id=123, ip="1.2.3.4")
        [2025-11-04 16:00:49.458807 UTC][1404-08-14 19:30:49.458807 IR][info] user_login [app.auth] user_id=123 ip=1.2.3.4
    """
    return structlog.get_logger(name)
