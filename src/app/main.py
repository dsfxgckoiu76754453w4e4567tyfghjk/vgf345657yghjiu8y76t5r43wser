"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.constants import (
    APP_DESCRIPTION,
    API_V1_PREFIX,
    HTTPStatus,
    HTTPStatusDetail,
)
from app.core.health import cleanup_health_checker, get_health_status
from app.core.logging import get_logger, setup_logging
from app.core.startup import startup_checks
from app.core.stats import get_application_stats

# Set up logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_startup",
        environment=settings.environment,
        debug=settings.debug,
    )

    # Run startup checks
    try:
        await startup_checks()
    except Exception as e:
        logger.error("startup_checks_failed", error=str(e))
        if settings.is_production:
            raise

    yield

    # Shutdown
    logger.info("application_shutdown")
    await cleanup_health_checker()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=APP_DESCRIPTION,
    docs_url="/docs" if settings.show_docs else None,
    redoc_url="/redoc" if settings.show_docs else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure this properly in production
    )

# ============================================================================
# PROMETHEUS METRICS INSTRUMENTATION
# ============================================================================

# Initialize Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=False,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the app with default metrics
instrumentator.instrument(app)


@app.get("/metrics")
def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response: Prometheus metrics in text format
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check(
    check_services: bool = Query(
        default=True,
        description="Whether to check external service dependencies"
    )
) -> dict[str, Any]:
    """
    Health check endpoint with optional dependency checks.

    Args:
        check_services: If True, checks database, Redis, and Qdrant health

    Returns:
        dict: Comprehensive health status
    """
    try:
        health_data = await get_health_status(check_dependencies=check_services)
        return health_data
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@app.get("/stats")
async def stats_endpoint() -> dict[str, Any]:
    """
    Application statistics endpoint.

    Returns:
        dict: Application statistics including database and config info

    Note:
        Only available in development and test environments
    """
    if settings.is_production:
        return JSONResponse(
            status_code=403,
            content={"detail": HTTPStatusDetail.INSUFFICIENT_PERMISSIONS}
        )

    try:
        stats = await get_application_stats()
        return stats
    except Exception as e:
        logger.error("stats_endpoint_failed", error=str(e))
        return {
            "error": str(e),
        }


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint.

    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Shia Islamic Chatbot API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.show_docs else "disabled",
        "health": "/health",
        "api": API_V1_PREFIX,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.

    Args:
        request: The request object
        exc: The exception

    Returns:
        JSONResponse: Error response
    """
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        exc_info=exc,
    )

    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": HTTPStatus.INTERNAL_SERVER_ERROR},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": HTTPStatus.INTERNAL_SERVER_ERROR,
                "error": str(exc),
                "type": type(exc).__name__,
            },
        )


# Include API routers
from app.api.v1 import api_router

app.include_router(api_router, prefix=API_V1_PREFIX)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
