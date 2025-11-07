"""Test data detection utilities.

Automatically detect test/dummy data based on patterns.
Prevents test data from being promoted between environments.
"""

import re
from typing import Optional

from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.logging import get_logger
from app.db.base import Base

logger = get_logger(__name__)


class TestDataDetector:
    """
    Automatically detect test/dummy data based on common patterns.

    Applied on:
    - Data creation (optional)
    - Promotion review (mandatory)
    - Manual scans (scheduled jobs)
    """

    # ========================================================================
    # Test Patterns
    # ========================================================================

    TEST_PATTERNS = [
        # Generic test keywords
        r"\btest\b",
        r"\bdemo\b",
        r"\bdummy\b",
        r"\bsample\b",
        r"\bexample\b",
        r"\bdebug\b",
        r"\bfoo\b",
        r"\bbar\b",
        r"\bbaz\b",
        r"\bqux\b",

        # Common test names (English)
        r"john\s*doe",
        r"jane\s*doe",
        r"test\s*user",
        r"admin\s*test",
        r"user\s*test",
        r"demo\s*user",

        # Common test names (Persian/Arabic)
        r"تست",  # test in Persian
        r"آزمایش",  # test in Persian
        r"نمونه",  # sample in Persian

        # Email patterns
        r"test@test\.com",
        r"test@example\.com",
        r"demo@.*",
        r".*@test\..*",
        r".*@example\..*",

        # Sequential/numeric patterns
        r"^test\d+$",
        r"^user\d+$",
        r"^demo\d+$",

        # Lorem ipsum
        r"lorem\s*ipsum",
        r"dolor\s*sit\s*amet",

        # Placeholder text
        r"asdf",
        r"qwerty",
        r"123456",

        # Development markers
        r"dev-test",
        r"staging-test",
        r"qa-test",
    ]

    @classmethod
    def is_test_data(
        cls,
        text: str,
        case_sensitive: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Check if text contains test data patterns.

        Args:
            text: Text to check
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            (is_test, reason) - reason explains which pattern matched

        Examples:
            >>> TestDataDetector.is_test_data("John Doe")
            (True, "Matches test pattern: john\\s*doe")

            >>> TestDataDetector.is_test_data("Real User")
            (False, None)
        """
        if not text:
            return False, None

        # Normalize text
        text_to_check = text if case_sensitive else text.lower().strip()

        # Check each pattern
        for pattern in cls.TEST_PATTERNS:
            flags = 0 if case_sensitive else re.IGNORECASE
            if re.search(pattern, text_to_check, flags):
                return True, f"Matches test pattern: {pattern}"

        return False, None

    @classmethod
    def check_model(cls, model: Base) -> tuple[bool, Optional[str]]:
        """
        Check if a model instance contains test data.

        Scans all string fields for test patterns.

        Args:
            model: SQLAlchemy model instance

        Returns:
            (is_test, reason) - reason includes field name and pattern

        Examples:
            >>> user = User(email="test@test.com", full_name="Real Name")
            >>> TestDataDetector.check_model(user)
            (True, "Field 'email': Matches test pattern: test@test\\.com")
        """
        # Get all string columns from model
        checkable_fields = []

        for column in model.__table__.columns:
            if isinstance(column.type, String):
                checkable_fields.append(column.name)

        # Check each field
        for field_name in checkable_fields:
            value = getattr(model, field_name, None)

            if value:
                is_test, reason = cls.is_test_data(str(value))

                if is_test:
                    return True, f"Field '{field_name}': {reason}"

        return False, None

    @classmethod
    async def scan_and_mark_test_data(
        cls,
        db: AsyncSession,
        model_class: type[Base],
        environment: str,
        batch_size: int = 100
    ) -> dict:
        """
        Scan all records in environment and mark test data.

        Run this as a maintenance job to keep test data detection up to date.

        Args:
            db: Database session
            model_class: Model class to scan
            environment: Environment to scan (dev, stage, prod)
            batch_size: Number of records to process at once

        Returns:
            Statistics dict with scan results

        Examples:
            >>> stats = await TestDataDetector.scan_and_mark_test_data(
            ...     db, User, "dev"
            ... )
            >>> print(stats)
            {
                "scanned": 150,
                "marked_as_test": 45,
                "already_marked": 10,
                "errors": 0
            }
        """
        results = {
            "model": model_class.__name__,
            "environment": environment,
            "scanned": 0,
            "marked_as_test": 0,
            "already_marked": 0,
            "errors": 0,
        }

        try:
            # Check if model has EnvironmentPromotionMixin
            if not hasattr(model_class, 'environment'):
                logger.warning(
                    "model_missing_environment_mixin",
                    model=model_class.__name__
                )
                return results

            # Count already marked test data
            already_marked = await db.scalar(
                select(func.count(model_class.id)).where(
                    model_class.environment == environment,
                    model_class.is_test_data == True  # noqa: E712
                )
            )
            results["already_marked"] = already_marked or 0

            # Get all unmarked records in this environment
            records = await db.execute(
                select(model_class).where(
                    model_class.environment == environment,
                    model_class.is_test_data == False  # noqa: E712
                ).limit(batch_size)
            )

            for record in records.scalars():
                results["scanned"] += 1

                try:
                    # Check if test data
                    is_test, reason = cls.check_model(record)

                    if is_test:
                        # Mark as test data
                        record.is_test_data = True
                        record.test_data_reason = reason
                        record.is_promotable = False  # Test data can't be promoted

                        results["marked_as_test"] += 1

                        logger.info(
                            "test_data_detected",
                            model=model_class.__name__,
                            id=str(record.id),
                            environment=environment,
                            reason=reason
                        )

                except Exception as e:
                    results["errors"] += 1
                    logger.error(
                        "test_data_scan_error",
                        model=model_class.__name__,
                        record_id=str(record.id) if hasattr(record, 'id') else "unknown",
                        error=str(e)
                    )

            # Commit changes
            await db.commit()

            logger.info(
                "test_data_scan_completed",
                model=model_class.__name__,
                environment=environment,
                **results
            )

        except Exception as e:
            logger.error(
                "test_data_scan_failed",
                model=model_class.__name__,
                environment=environment,
                error=str(e)
            )
            results["errors"] += 1

        return results

    @classmethod
    def add_custom_pattern(cls, pattern: str):
        """
        Add a custom test data pattern.

        Useful for organization-specific test patterns.

        Args:
            pattern: Regex pattern to add

        Examples:
            >>> TestDataDetector.add_custom_pattern(r"company-test-\d+")
        """
        if pattern not in cls.TEST_PATTERNS:
            cls.TEST_PATTERNS.append(pattern)
            logger.info("custom_test_pattern_added", pattern=pattern)

    @classmethod
    def remove_pattern(cls, pattern: str):
        """Remove a test data pattern."""
        if pattern in cls.TEST_PATTERNS:
            cls.TEST_PATTERNS.remove(pattern)
            logger.info("test_pattern_removed", pattern=pattern)


# ========================================================================
# Convenience Functions
# ========================================================================

def is_test_data(text: str) -> bool:
    """Quick check if text is test data."""
    is_test, _ = TestDataDetector.is_test_data(text)
    return is_test


async def scan_environment_for_test_data(
    db: AsyncSession,
    model_classes: list[type[Base]],
    environment: str
) -> dict:
    """
    Scan multiple models in an environment for test data.

    Args:
        db: Database session
        model_classes: List of model classes to scan
        environment: Environment to scan

    Returns:
        Combined statistics from all scans
    """
    total_results = {
        "environment": environment,
        "models_scanned": 0,
        "total_scanned": 0,
        "total_marked": 0,
        "total_errors": 0,
        "details": []
    }

    for model_class in model_classes:
        result = await TestDataDetector.scan_and_mark_test_data(
            db, model_class, environment
        )

        total_results["models_scanned"] += 1
        total_results["total_scanned"] += result["scanned"]
        total_results["total_marked"] += result["marked_as_test"]
        total_results["total_errors"] += result["errors"]
        total_results["details"].append(result)

    return total_results
