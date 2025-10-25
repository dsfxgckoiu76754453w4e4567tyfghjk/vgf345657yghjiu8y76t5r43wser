"""Security middleware for the application."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Protect against SQL injection attacks."""

    # Common SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"('.*OR.*'.*=.*')",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Check for SQL injection patterns."""
        # Check query parameters
        if request.query_params:
            for key, value in request.query_params.items():
                if self._contains_sql_injection(value):
                    logger.warn(
                        "sql_injection_attempt_blocked",
                        path=request.url.path,
                        param=key,
                        value=value[:50],
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid input detected"},
                    )

        # Check request body (for JSON)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if self._contains_sql_injection(body.decode("utf-8")):
                        logger.warn(
                            "sql_injection_attempt_in_body",
                            path=request.url.path,
                        )
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid input detected"},
                        )
                except Exception:
                    pass  # If we can't decode, let it pass (will fail validation later)

        response = await call_next(request)
        return response

    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns."""
        text_upper = text.upper()

        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True

        return False


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Protect against XSS attacks."""

    # Common XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe",
        r"<embed",
        r"<object",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Check for XSS patterns."""
        # Check query parameters
        if request.query_params:
            for key, value in request.query_params.items():
                if self._contains_xss(value):
                    logger.warn(
                        "xss_attempt_blocked",
                        path=request.url.path,
                        param=key,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid input detected"},
                    )

        response = await call_next(request)
        return response

    def _contains_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks."""

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10 MB default
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            max_request_size: Maximum request size in bytes
        """
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next: Callable):
        """Check request size."""
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_request_size:
                logger.warn(
                    "request_too_large",
                    path=request.url.path,
                    size_mb=content_length / (1024 * 1024),
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request body too large (max {self.max_request_size / (1024 * 1024)}MB)"},
                )

        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, app, rate_limiter_service=None):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            rate_limiter_service: RateLimiterService instance
        """
        super().__init__(app)
        self.rate_limiter_service = rate_limiter_service

    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting."""
        if not self.rate_limiter_service:
            # Rate limiting not configured
            return await call_next(request)

        # Extract client identifier (API key, user ID, or IP)
        client_id = self._get_client_id(request)

        if client_id:
            # Check rate limit
            is_allowed, rate_info = await self.rate_limiter_service.check_rate_limit(
                client_id=client_id,
                limit_per_minute=60,  # Default limits
                limit_per_day=10000,
            )

            if not is_allowed:
                logger.warn(
                    "rate_limit_exceeded",
                    client_id=str(client_id),
                    path=request.url.path,
                )

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_info["reset_minute"],
                    },
                    headers={
                        "X-RateLimit-Limit-Minute": str(rate_info["limit_per_minute"]),
                        "X-RateLimit-Limit-Day": str(rate_info["limit_per_day"]),
                        "X-RateLimit-Remaining-Minute": str(rate_info["remaining_per_minute"]),
                        "X-RateLimit-Remaining-Day": str(rate_info["remaining_per_day"]),
                        "X-RateLimit-Reset-Minute": str(rate_info["reset_minute"]),
                        "Retry-After": str(rate_info["reset_minute"]),
                    },
                )

        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request):
        """Extract client identifier from request."""
        # Try to get from API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.client.host if request.client else None
