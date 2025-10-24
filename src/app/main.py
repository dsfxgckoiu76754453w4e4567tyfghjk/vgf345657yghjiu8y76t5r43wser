"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

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

    yield

    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade comprehensive Shia Islamic knowledge chatbot",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict: Status message
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version,
    }


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        dict: Welcome message
    """
    return {
        "message": "Shia Islamic Chatbot API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled in production",
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
            content={"detail": "INTERNAL_SERVER_ERROR"},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "INTERNAL_SERVER_ERROR",
                "error": str(exc),
                "type": type(exc).__name__,
            },
        )


# TODO: Add routers
# from app.api.v1 import auth, users, chat
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
