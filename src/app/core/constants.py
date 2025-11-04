"""Application-wide constants."""

from enum import Enum


class HTTPStatus(str, Enum):
    """HTTP status messages as constants."""

    # Success messages (2xx)
    OK = "OK"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    NO_CONTENT = "NO_CONTENT"

    # Client error messages (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    # Server error messages (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    BAD_GATEWAY = "BAD_GATEWAY"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"


class HTTPStatusDetail(str, Enum):
    """Detailed HTTP status messages."""

    # Authentication & Authorization
    INVALID_CREDENTIALS = "Invalid credentials provided"
    TOKEN_EXPIRED = "Authentication token has expired"
    TOKEN_INVALID = "Authentication token is invalid"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions to access this resource"
    API_KEY_INVALID = "Invalid API key"
    API_KEY_EXPIRED = "API key has expired"
    API_KEY_REVOKED = "API key has been revoked"

    # User-related
    USER_NOT_FOUND = "User not found"
    USER_ALREADY_EXISTS = "User already exists"
    USER_INACTIVE = "User account is inactive"
    EMAIL_ALREADY_REGISTERED = "Email is already registered"

    # Content-related
    CONTENT_NOT_FOUND = "Content not found"
    CONTENT_ALREADY_EXISTS = "Content already exists"
    CONTENT_PENDING_REVIEW = "Content is pending review"
    CONTENT_REJECTED = "Content has been rejected"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later"

    # Database
    DATABASE_ERROR = "Database operation failed"
    DATABASE_CONNECTION_ERROR = "Failed to connect to database"

    # External services
    EXTERNAL_SERVICE_ERROR = "External service error"
    QDRANT_CONNECTION_ERROR = "Failed to connect to Qdrant vector database"
    REDIS_CONNECTION_ERROR = "Failed to connect to Redis cache"
    LLM_API_ERROR = "LLM API request failed"

    # Validation
    INVALID_INPUT = "Invalid input provided"
    VALIDATION_ERROR = "Validation error"
    MISSING_REQUIRED_FIELD = "Required field is missing"


class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    CONTRIBUTOR = "contributor"
    USER = "user"
    ANONYMOUS = "anonymous"


class SubscriptionTier(str, Enum):
    """Subscription tiers for rate limiting."""

    FREE = "free"
    PREMIUM = "premium"
    UNLIMITED = "unlimited"
    TEST = "test"


class ContentStatus(str, Enum):
    """Content submission status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Application metadata
APP_NAME = "Shia Islamic Chatbot"
APP_DESCRIPTION = "Production-grade comprehensive Shia Islamic knowledge chatbot"
API_V1_PREFIX = "/api/v1"

# Database constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_OFFSET = 0

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 3600  # 1 hour
CACHE_TTL_LONG = 86400  # 24 hours

# Request timeouts (seconds)
REQUEST_TIMEOUT_SHORT = 10
REQUEST_TIMEOUT_MEDIUM = 30
REQUEST_TIMEOUT_LONG = 60
