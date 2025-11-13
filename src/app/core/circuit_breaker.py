"""
Circuit Breaker pattern implementation for external API calls.

Prevents cascading failures when external services are down.
Automatically opens circuit after failure threshold, then allows
periodic retries to check if service recovered.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Optional, TypeVar, Any

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation for async functions.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Configuration:
    - failure_threshold: Number of failures before opening
    - recovery_timeout: Seconds before trying half-open
    - success_threshold: Successes needed to close from half-open
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name (for logging)
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Successes needed to close circuit
            timeout_seconds: Request timeout in seconds
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now(timezone.utc)

        logger.info(
            "circuit_breaker_initialized",
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        # Check if we should transition to half-open
        if self.state == CircuitState.OPEN and self.last_failure_time:
            time_since_failure = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
            if time_since_failure >= self.recovery_timeout:
                self._transition_to_half_open()
                return False

        return self.state == CircuitState.OPEN

    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN."""
        logger.info(
            "circuit_breaker_half_open",
            name=self.name,
            previous_state=self.state.value,
        )
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.now(timezone.utc)

    def _transition_to_open(self):
        """Transition to OPEN state."""
        logger.warning(
            "circuit_breaker_opened",
            name=self.name,
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
        )
        self.state = CircuitState.OPEN
        self.last_failure_time = datetime.now(timezone.utc)
        self.last_state_change = datetime.now(timezone.utc)

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        logger.info(
            "circuit_breaker_closed",
            name=self.name,
            success_count=self.success_count,
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now(timezone.utc)

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                "circuit_breaker_success",
                name=self.name,
                success_count=self.success_count,
                needed=self.success_threshold,
            )

            # Enough successes to close circuit
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        logger.warning(
            "circuit_breaker_failure",
            name=self.name,
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
            state=self.state.value,
        )

        # Open circuit if threshold reached
        if self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

    async def call(
        self,
        func: Callable[..., Any],
        *args,
        fallback: Optional[Callable[..., Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func

        Returns:
            Function result or fallback result

        Raises:
            CircuitBreakerError: If circuit is open and no fallback
        """
        # Check if circuit is open
        if self.is_open:
            logger.warning(
                "circuit_breaker_request_blocked",
                name=self.name,
                state=self.state.value,
            )

            if fallback:
                logger.info(
                    "circuit_breaker_using_fallback",
                    name=self.name,
                )
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)

            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout_seconds
            )
            self.record_success()
            return result

        except asyncio.TimeoutError as e:
            logger.error(
                "circuit_breaker_timeout",
                name=self.name,
                timeout=self.timeout_seconds,
            )
            self.record_failure()
            raise

        except Exception as e:
            logger.error(
                "circuit_breaker_error",
                name=self.name,
                error=str(e),
                error_type=type(e).__name__,
            )
            self.record_failure()
            raise

    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker registry."""
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
    ) -> CircuitBreaker:
        """
        Get existing or create new circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before recovery attempt
            success_threshold: Successes needed to close
            timeout_seconds: Request timeout

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
            )

        return self._breakers[name]

    def get_all_states(self) -> list[dict]:
        """Get states of all circuit breakers."""
        return [breaker.get_state() for breaker in self._breakers.values()]


# Global registry
circuit_breaker_registry = CircuitBreakerRegistry()
