"""
Custom logging configuration following the Logging Standard v2.0.

Logging Format:
    [timestamp][level] message [context] key=value...

Example:
    [2025-11-04 16:00:49.458807 UTC][1404-08-14 19:30:49.458807 IR][info] scheduler_started [__main__] jobs=2

Note: Iranian timestamps use Jalali calendar format YYYY-MM-DD (NO 'J' prefix)
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

import jdatetime
import pytz
import structlog
from structlog.types import EventDict, Processor

from app.core.config import settings


# ANSI color codes following Logging Standard v2.0
class Colors:
    """ANSI color codes for terminal output (Standard v2.0)."""

    # Timestamp colors (bright variants for better visibility)
    UTC = "\033[96m"  # Bright Cyan (96)
    IR = "\033[94m"  # Bright Blue (94)

    # Level colors
    DEBUG = "\033[90m"  # Bright Black/Gray (90)
    INFO = "\033[92m"  # Bright Green (92)
    WARN = "\033[93m"  # Bright Yellow (93)
    ERROR = "\033[91m"  # Bright Red (91)

    # Context and key colors
    CONTEXT = "\033[95m"  # Bright Magenta (95)
    KEY = "\033[36m"  # Cyan (36)

    # Reset
    RESET = "\033[0m"

    @staticmethod
    def should_use_colors() -> bool:
        """
        Determine if colors should be used.

        Colors are disabled when:
        - Not running in a TTY
        - NO_COLOR environment variable is set
        - LOG_COLOR is explicitly set to 'false'
        - Running in Docker/Kubernetes (detected via env vars)
        - Output is redirected
        """
        # Check NO_COLOR environment variable (standard: https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Check LOG_COLOR setting
        log_color = os.environ.get("LOG_COLOR", "auto").lower()
        if log_color == "false":
            return False
        if log_color == "true":
            return True

        # Check if running in Docker/Kubernetes
        if os.environ.get("KUBERNETES_SERVICE_HOST") or os.path.exists("/.dockerenv"):
            return False

        # Auto-detect: only use colors if stdout is a TTY
        return sys.stdout.isatty()


def add_dual_timestamps(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add UTC and/or Iranian (Jalali) timestamps to the log event.

    Format:
        UTC: [YYYY-MM-DD HH:MM:SS.μs UTC]
        IR:  [YYYY-MM-DD HH:MM:SS.μs IR]  (NO 'J' prefix!)

    Configuration:
        LOG_TIMESTAMP: 'utc' | 'ir' | 'both' (default: 'both')
        LOG_TIMESTAMP_PRECISION: 3 (ms) or 6 (μs) (default: 6)
    """
    # Get configuration
    timestamp_mode = os.environ.get("LOG_TIMESTAMP", "both").lower()
    precision = int(os.environ.get("LOG_TIMESTAMP_PRECISION", "6"))

    now_utc = datetime.now(timezone.utc)

    # UTC timestamp with configurable precision
    if timestamp_mode in ("utc", "both"):
        utc_str = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")
        # Truncate microseconds to desired precision
        if precision == 3:  # milliseconds
            utc_str = utc_str[:-3]  # Remove last 3 digits
        # precision == 6 keeps all 6 digits (microseconds)
        event_dict["timestamp_utc"] = f"{utc_str} UTC"

    # Iranian timestamp (UTC+3:30)
    if timestamp_mode in ("ir", "both"):
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

        # Format: YYYY-MM-DD HH:MM:SS.μs IR (NO 'J' prefix!)
        ir_str = jalali.strftime("%Y-%m-%d %H:%M:%S.%f")
        # Truncate microseconds to desired precision
        if precision == 3:  # milliseconds
            ir_str = ir_str[:-3]  # Remove last 3 digits
        # precision == 6 keeps all 6 digits (microseconds)
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
    Custom renderer that outputs logs in Logging Standard v2.0 format.

    Format: [timestamp][level] message [context] key=value...

    Colors (v2.0):
        - UTC timestamp: Bright Cyan (96)
        - IR timestamp: Bright Blue (94)
        - debug: Gray (90)
        - info: Bright Green (92)
        - warn: Bright Yellow (93)
        - error: Bright Red (91) - applied to both bracket AND message
        - context: Bright Magenta (95)
        - keys: Cyan (36)
    """

    def __init__(self, colors: bool = True):
        """
        Initialize the renderer.

        Args:
            colors: Enable ANSI colors (auto-disabled based on environment)
        """
        self._colors_enabled = colors and Colors.should_use_colors()

    def __call__(self, logger: Any, name: str, event_dict: EventDict) -> str:
        """Render the log event to a string."""
        # Extract components
        utc = event_dict.pop("timestamp_utc", None)
        ir = event_dict.pop("timestamp_ir", None)
        level = event_dict.pop("level", "info")
        logger_name = event_dict.pop("logger", "")
        event = event_dict.pop("event", "")

        # Build the timestamp prefix (no spaces between brackets)
        prefix_parts = []

        if utc:
            if self._colors_enabled:
                prefix_parts.append(f"{Colors.UTC}[{utc}]{Colors.RESET}")
            else:
                prefix_parts.append(f"[{utc}]")

        if ir:
            if self._colors_enabled:
                prefix_parts.append(f"{Colors.IR}[{ir}]{Colors.RESET}")
            else:
                prefix_parts.append(f"[{ir}]")

        prefix = "".join(prefix_parts)

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

        # Build the message (for error level, color the message too)
        if self._colors_enabled and level == "error":
            message = f"{Colors.ERROR}{event}{Colors.RESET}"
        else:
            message = event

        # Build the rest of the log line with spaces
        parts = [message]

        # Logger name/context (if present) in magenta
        if logger_name:
            if self._colors_enabled:
                parts.append(f"{Colors.CONTEXT}[{logger_name}]{Colors.RESET}")
            else:
                parts.append(f"[{logger_name}]")

        # Key-value pairs (remaining fields) with cyan keys
        for key, value in sorted(event_dict.items()):
            # Skip internal structlog fields
            if key.startswith("_"):
                continue

            if self._colors_enabled:
                # Color the key in cyan, leave value default
                parts.append(f"{Colors.KEY}{key}={Colors.RESET}{value}")
            else:
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
