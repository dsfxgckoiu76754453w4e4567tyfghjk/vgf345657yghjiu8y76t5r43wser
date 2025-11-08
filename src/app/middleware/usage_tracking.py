"""Usage tracking middleware for automatic usage logging."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage.

    Logs:
    - Request path and method
    - Response status
    - Response time
    - User ID (if authenticated)
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and track usage."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Extract user ID if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)

        # Log usage
        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
        )

        # Add custom headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
