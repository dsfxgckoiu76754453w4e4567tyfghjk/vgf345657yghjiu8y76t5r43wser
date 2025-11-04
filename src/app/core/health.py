"""Health check and system monitoring."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.core.constants import ServiceStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

# Application start time
_start_time = time.time()


class HealthChecker:
    """System health checker for all dependencies."""

    def __init__(self):
        self._db_engine: AsyncEngine | None = None
        self._redis_client: aioredis.Redis | None = None

    async def check_database(self) -> dict[str, Any]:
        """
        Check PostgreSQL database health.

        Returns:
            dict: Database health status
        """
        try:
            if not self._db_engine:
                self._db_engine = create_async_engine(
                    settings.database_url,
                    pool_size=2,
                    max_overflow=0,
                    pool_pre_ping=True,
                )

            async with self._db_engine.connect() as conn:
                start = time.time()
                await conn.execute(text("SELECT 1"))
                latency_ms = round((time.time() - start) * 1000, 2)

            return {
                "status": ServiceStatus.HEALTHY,
                "latency_ms": latency_ms,
                "message": "Database connection successful",
            }
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return {
                "status": ServiceStatus.UNHEALTHY,
                "latency_ms": None,
                "error": str(e),
            }

    async def check_redis(self) -> dict[str, Any]:
        """
        Check Redis cache health.

        Returns:
            dict: Redis health status
        """
        try:
            if not self._redis_client:
                self._redis_client = aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                )

            start = time.time()
            await self._redis_client.ping()
            latency_ms = round((time.time() - start) * 1000, 2)

            return {
                "status": ServiceStatus.HEALTHY,
                "latency_ms": latency_ms,
                "message": "Redis connection successful",
            }
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return {
                "status": ServiceStatus.UNHEALTHY,
                "latency_ms": None,
                "error": str(e),
            }

    async def check_qdrant(self) -> dict[str, Any]:
        """
        Check Qdrant vector database health.

        Returns:
            dict: Qdrant health status
        """
        try:
            import httpx

            start = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.qdrant_url}/healthz")
                response.raise_for_status()
            latency_ms = round((time.time() - start) * 1000, 2)

            return {
                "status": ServiceStatus.HEALTHY,
                "latency_ms": latency_ms,
                "message": "Qdrant connection successful",
            }
        except Exception as e:
            logger.error("qdrant_health_check_failed", error=str(e))
            return {
                "status": ServiceStatus.UNHEALTHY,
                "latency_ms": None,
                "error": str(e),
            }

    async def check_all_services(self) -> dict[str, Any]:
        """
        Check health of all services concurrently.

        Returns:
            dict: Health status of all services
        """
        # Run all health checks concurrently
        db_check, redis_check, qdrant_check = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_qdrant(),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        services = {
            "database": db_check if not isinstance(db_check, Exception) else {
                "status": ServiceStatus.UNHEALTHY,
                "error": str(db_check)
            },
            "redis": redis_check if not isinstance(redis_check, Exception) else {
                "status": ServiceStatus.UNHEALTHY,
                "error": str(redis_check)
            },
            "qdrant": qdrant_check if not isinstance(qdrant_check, Exception) else {
                "status": ServiceStatus.UNHEALTHY,
                "error": str(qdrant_check)
            },
        }

        # Determine overall status
        statuses = [svc["status"] for svc in services.values()]
        if all(s == ServiceStatus.HEALTHY for s in statuses):
            overall_status = ServiceStatus.HEALTHY
        elif all(s == ServiceStatus.UNHEALTHY for s in statuses):
            overall_status = ServiceStatus.UNHEALTHY
        else:
            overall_status = ServiceStatus.DEGRADED

        return {
            "status": overall_status,
            "services": services,
        }

    async def close(self):
        """Close all health check connections."""
        if self._db_engine:
            await self._db_engine.dispose()
        if self._redis_client:
            await self._redis_client.close()


# Global health checker instance
_health_checker = HealthChecker()


async def get_health_status(check_dependencies: bool = True) -> dict[str, Any]:
    """
    Get application health status.

    Args:
        check_dependencies: Whether to check external dependencies

    Returns:
        dict: Complete health status
    """
    uptime_seconds = int(time.time() - _start_time)
    health_data = {
        "status": ServiceStatus.HEALTHY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "version": settings.app_version,
        "uptime_seconds": uptime_seconds,
    }

    if check_dependencies:
        services_health = await _health_checker.check_all_services()
        health_data["status"] = services_health["status"]
        health_data["services"] = services_health["services"]

    return health_data


async def cleanup_health_checker():
    """Cleanup health checker resources on shutdown."""
    await _health_checker.close()
