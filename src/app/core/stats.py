"""Application statistics and metrics."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_database_stats() -> dict[str, Any]:
    """
    Get database statistics.

    Returns:
        dict: Database statistics
    """
    try:
        engine = create_async_engine(
            settings.database_url,
            pool_size=2,
            max_overflow=0,
        )

        async with engine.connect() as conn:
            # Get database size
            result = await conn.execute(
                text(
                    "SELECT pg_size_pretty(pg_database_size(:db_name)) as size"
                ),
                {"db_name": settings.database_name}
            )
            db_size = result.scalar()

            # Get connection count
            result = await conn.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = :db_name"
                ),
                {"db_name": settings.database_name}
            )
            connections = result.scalar()

            # Get table counts
            result = await conn.execute(
                text(
                    """
                    SELECT
                        'users' as table_name, COUNT(*) as count FROM users
                    UNION ALL
                    SELECT
                        'api_keys' as table_name, COUNT(*) as count FROM api_keys
                    UNION ALL
                    SELECT
                        'content_submissions' as table_name, COUNT(*) as count FROM content_submissions
                    """
                )
            )
            table_counts = {row[0]: row[1] for row in result.fetchall()}

        await engine.dispose()

        return {
            "database_size": db_size,
            "active_connections": connections,
            "table_counts": table_counts,
        }
    except Exception as e:
        logger.error("failed_to_get_database_stats", error=str(e))
        return {
            "error": str(e)
        }


async def get_application_stats() -> dict[str, Any]:
    """
    Get comprehensive application statistics.

    Returns:
        dict: Application statistics
    """
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "version": settings.app_version,
        "database": await get_database_stats(),
        "configuration": {
            "debug_mode": settings.debug,
            "log_level": settings.log_level,
            "database_pool_size": settings.database_pool_size,
            "rate_limits": {
                "anonymous": settings.rate_limit_anonymous,
                "free": settings.rate_limit_free,
                "premium": settings.rate_limit_premium,
                "unlimited": settings.rate_limit_unlimited,
            },
        },
    }

    return stats
