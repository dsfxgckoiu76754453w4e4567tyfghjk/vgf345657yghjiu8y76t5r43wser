"""Rate limiting service using Redis."""

from datetime import datetime
from typing import Optional
from uuid import UUID

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RateLimiterService:
    """Service for rate limiting API requests using Redis."""

    def __init__(self):
        """Initialize rate limiter service."""
        # Redis connection
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def check_rate_limit(
        self,
        client_id: UUID,
        limit_per_minute: int,
        limit_per_day: int,
    ) -> tuple[bool, dict]:
        """
        Check if a client has exceeded rate limits.

        Uses sliding window algorithm for accurate rate limiting.

        Args:
            client_id: Client ID
            limit_per_minute: Maximum requests per minute
            limit_per_day: Maximum requests per day

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        client_id_str = str(client_id)
        now = datetime.utcnow()

        # Keys for Redis
        minute_key = f"rate_limit:minute:{client_id_str}"
        day_key = f"rate_limit:day:{client_id_str}:{now.strftime('%Y-%m-%d')}"

        # Check per-minute limit
        minute_count = await self.redis.get(minute_key)
        minute_count = int(minute_count) if minute_count else 0

        # Check per-day limit
        day_count = await self.redis.get(day_key)
        day_count = int(day_count) if day_count else 0

        # Determine if request is allowed
        is_allowed = minute_count < limit_per_minute and day_count < limit_per_day

        rate_limit_info = {
            "limit_per_minute": limit_per_minute,
            "limit_per_day": limit_per_day,
            "used_per_minute": minute_count,
            "used_per_day": day_count,
            "remaining_per_minute": max(0, limit_per_minute - minute_count),
            "remaining_per_day": max(0, limit_per_day - day_count),
            "reset_minute": 60 - now.second,  # Seconds until minute resets
            "reset_day": (
                86400
                - (now.hour * 3600 + now.minute * 60 + now.second)  # Seconds until day resets
            ),
        }

        if is_allowed:
            # Increment counters
            await self._increment_counters(minute_key, day_key)

        logger.info(
            "rate_limit_check",
            client_id=client_id_str,
            is_allowed=is_allowed,
            minute_count=minute_count,
            day_count=day_count,
        )

        return is_allowed, rate_limit_info

    async def _increment_counters(self, minute_key: str, day_key: str) -> None:
        """
        Increment rate limit counters.

        Args:
            minute_key: Redis key for per-minute counter
            day_key: Redis key for per-day counter
        """
        # Increment minute counter and set expiry
        await self.redis.incr(minute_key)
        await self.redis.expire(minute_key, 60)  # Expire after 60 seconds

        # Increment day counter and set expiry
        await self.redis.incr(day_key)
        await self.redis.expire(day_key, 86400)  # Expire after 24 hours

    async def reset_limits(self, client_id: UUID) -> None:
        """
        Reset rate limits for a client (admin operation).

        Args:
            client_id: Client ID
        """
        client_id_str = str(client_id)
        now = datetime.utcnow()

        minute_key = f"rate_limit:minute:{client_id_str}"
        day_key = f"rate_limit:day:{client_id_str}:{now.strftime('%Y-%m-%d')}"

        await self.redis.delete(minute_key)
        await self.redis.delete(day_key)

        logger.info("rate_limits_reset", client_id=client_id_str)

    async def get_current_usage(self, client_id: UUID) -> dict:
        """
        Get current rate limit usage for a client.

        Args:
            client_id: Client ID

        Returns:
            Current usage information
        """
        client_id_str = str(client_id)
        now = datetime.utcnow()

        minute_key = f"rate_limit:minute:{client_id_str}"
        day_key = f"rate_limit:day:{client_id_str}:{now.strftime('%Y-%m-%d')}"

        minute_count = await self.redis.get(minute_key)
        minute_count = int(minute_count) if minute_count else 0

        day_count = await self.redis.get(day_key)
        day_count = int(day_count) if day_count else 0

        return {
            "requests_this_minute": minute_count,
            "requests_today": day_count,
            "timestamp": now.isoformat(),
        }

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
