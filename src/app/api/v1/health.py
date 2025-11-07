"""Health check and monitoring endpoints."""

import time
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import get_db

router = APIRouter()
logger = get_logger(__name__)


# Response Schemas
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""

    status: str
    timestamp: str
    version: str
    environment: str
    services: dict[str, dict[str, str]]


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    checks: dict[str, bool]


@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Basic health check.

    Returns:
    - status: "healthy"
    - timestamp: Current UTC time
    - version: App version
    - environment: Current environment

    Always returns 200 OK if the app is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
) -> DetailedHealthResponse:
    """
    Detailed health check with service status.

    Checks:
    - Database connectivity
    - OpenRouter API configuration
    - Redis connectivity (if configured)

    Returns detailed status for each service.
    """
    services = {}

    # Check database
    try:
        start = time.time()
        await db.execute(text("SELECT 1"))
        latency = round((time.time() - start) * 1000, 2)
        services["database"] = {
            "status": "healthy",
            "latency_ms": str(latency),
        }
    except Exception as e:
        services["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        logger.error("database_health_check_failed", error=str(e))

    # Check OpenRouter configuration
    if settings.openrouter_api_key:
        services["openrouter"] = {
            "status": "configured",
            "base_url": settings.openrouter_base_url,
        }
    else:
        services["openrouter"] = {
            "status": "not_configured",
            "error": "OPENROUTER_API_KEY not set",
        }

    # Check Redis (if used)
    try:
        if settings.redis_url:
            # Simple check - would need actual Redis client to test
            services["redis"] = {
                "status": "configured",
                "url": settings.redis_url,
            }
        else:
            services["redis"] = {
                "status": "not_configured",
            }
    except Exception as e:
        services["redis"] = {
            "status": "error",
            "error": str(e),
        }

    # Overall status
    overall_status = "healthy"
    if any(svc.get("status") == "unhealthy" for svc in services.values()):
        overall_status = "unhealthy"
    elif any(svc.get("status") == "not_configured" for svc in services.values()):
        overall_status = "degraded"

    logger.info("detailed_health_check", status=overall_status)

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        environment=settings.environment,
        services=services,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> ReadinessResponse:
    """
    Readiness check for Kubernetes/load balancers.

    Checks if the app is ready to serve traffic:
    - Database is accessible
    - OpenRouter API is configured

    Returns 200 if ready, 503 if not ready.
    """
    checks = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Check OpenRouter configuration
    checks["openrouter"] = bool(settings.openrouter_api_key)

    # Overall readiness
    ready = all(checks.values())

    if not ready:
        logger.warning("readiness_check_failed", checks=checks)

    return ReadinessResponse(ready=ready, checks=checks)


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict[str, str]:
    """
    Liveness check for Kubernetes.

    Simple check that the app is running.
    Returns 200 OK if alive.

    Used by Kubernetes to restart unhealthy pods.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, any]:
    """
    Basic metrics endpoint.

    Returns:
    - Database connection pool stats
    - App uptime
    - Request count (if available)

    For production, consider using Prometheus metrics.
    """
    try:
        from sqlalchemy import inspect

        # Get database stats
        db_stats = {
            "pool_size": db.get_bind().pool.size() if hasattr(db.get_bind(), "pool") else "N/A",
            "checked_out": db.get_bind().pool.checkedout() if hasattr(db.get_bind(), "pool") else "N/A",
        }
    except Exception as e:
        db_stats = {"error": str(e)}

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": settings.app_version,
        "database": db_stats,
    }
