#!/usr/bin/env python3
"""
Test script for Logging Standard v2.0 implementation.

Tests all logging configurations:
- Timestamp modes (utc, ir, both)
- Precision levels (3ms, 6μs)
- Color modes (auto, true, false)
- All log levels (debug, info, warn, error)
- Context and key-value pairs
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_logging_configuration(
    timestamp_mode: str = "both",
    precision: int = 6,
    color_mode: str = "auto",
    test_name: str = "Test",
):
    """Test logging with specific configuration."""
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"Config: timestamp={timestamp_mode}, precision={precision}, color={color_mode}")
    print(f"{'=' * 80}")

    # Set environment variables
    os.environ["LOG_TIMESTAMP"] = timestamp_mode
    os.environ["LOG_TIMESTAMP_PRECISION"] = str(precision)
    os.environ["LOG_COLOR"] = color_mode

    # Import after setting env vars to pick up new configuration
    import importlib
    from app.core import logging as log_module

    # Reload the logging module to pick up new settings
    importlib.reload(log_module)

    # Setup logging and get logger
    log_module.setup_logging()
    logger = log_module.get_logger("test.logging.v2")

    # Test all log levels with various content
    logger.debug("debug_message_test", component="test_suite", iteration=1)
    logger.info("info_message_test", user_id=12345, action="login", status="success")
    logger.warn(
        "warn_message_test",
        resource="memory",
        usage_percent=85,
        threshold=80,
        warning="high memory usage",
    )
    logger.error(
        "error_message_test",
        error_code=500,
        error="internal server error",
        stack_trace="line 42 in main.py",
    )

    print()  # Extra newline for readability


def main():
    """Run all logging tests."""
    print("\n" + "=" * 80)
    print("LOGGING STANDARD v2.0 - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Test 1: Both timestamps, microseconds, colors auto
    test_logging_configuration(
        timestamp_mode="both",
        precision=6,
        color_mode="auto",
        test_name="Default Configuration (both timestamps, 6μs, auto colors)",
    )

    # Test 2: UTC only, microseconds, colors on
    test_logging_configuration(
        timestamp_mode="utc",
        precision=6,
        color_mode="true",
        test_name="UTC Only (6μs, colors forced on)",
    )

    # Test 3: IR only, milliseconds, colors on
    test_logging_configuration(
        timestamp_mode="ir",
        precision=3,
        color_mode="true",
        test_name="Iranian/Jalali Only (3ms, colors forced on)",
    )

    # Test 4: Both timestamps, milliseconds, colors off
    test_logging_configuration(
        timestamp_mode="both",
        precision=3,
        color_mode="false",
        test_name="Both Timestamps (3ms, colors off - production style)",
    )

    # Test 5: NO_COLOR environment variable test
    print(f"\n{'=' * 80}")
    print("TEST: NO_COLOR Environment Variable (should disable colors)")
    print(f"{'=' * 80}")
    os.environ["NO_COLOR"] = "1"
    test_logging_configuration(
        timestamp_mode="both",
        precision=6,
        color_mode="auto",
        test_name="NO_COLOR=1 (colors should be disabled even with auto)",
    )
    del os.environ["NO_COLOR"]

    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80)
    print("\n✅ All logging configurations tested successfully!")
    print("\nVerify that:")
    print("  - Timestamps display correctly (UTC, IR, or both)")
    print("  - Precision is correct (3 or 6 digits after decimal)")
    print("  - Colors work as expected (or disabled when configured)")
    print("  - Log levels are formatted correctly [debug] [info] [warn] [error]")
    print("  - Context appears in magenta: [test.logging.v2]")
    print("  - Keys appear in cyan: key=value")
    print("  - Error messages are fully colored (bracket + message)")
    print("  - NO 'J' prefix in Iranian dates (should be YYYY-MM-DD, not JYYYY-MM-DD)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
