"""Admin analytics API endpoints."""

from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.chat import Conversation, Message
from app.models.subscription import (
    GeneratedImage,
    MonthlyUsageQuota,
    Subscription,
)
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


# Response Schemas
class SystemStatsResponse(BaseModel):
    """System-wide statistics."""

    total_users: int
    active_users_30d: int
    total_conversations: int
    total_messages: int
    total_tokens_used: int
    total_images_generated: int
    total_cost_usd: float
    total_cache_savings_usd: float
    cache_hit_rate: float


class PlanDistributionResponse(BaseModel):
    """Plan distribution statistics."""

    plan_type: str
    user_count: int
    percentage: float


class UsageTrendResponse(BaseModel):
    """Usage trends over time."""

    date: str
    messages: int
    tokens: int
    images: int
    cost_usd: float
    cache_savings_usd: float


class TopUsersResponse(BaseModel):
    """Top users by usage."""

    user_id: str
    email: str
    messages_count: int
    tokens_used: int
    images_generated: int
    cost_usd: float
    cache_savings_usd: float


class ModelUsageResponse(BaseModel):
    """Model usage statistics."""

    model: str
    message_count: int
    total_tokens: int
    average_tokens_per_message: float
    total_cost_usd: float


class CachePerformanceResponse(BaseModel):
    """Cache performance metrics."""

    total_messages: int
    cached_messages: int
    cache_hit_rate: float
    total_tokens_cached: int
    total_cache_savings_usd: float
    average_cache_discount_per_message: float


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/system-stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SystemStatsResponse:
    """
    Get system-wide statistics.

    Requires admin role.

    Returns:
    - Total users
    - Active users (30 days)
    - Total conversations and messages
    - Total tokens used
    - Total images generated
    - Total cost and cache savings
    - Overall cache hit rate
    """
    try:
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        # Active users (30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_result = await db.execute(
            select(func.count(func.distinct(Conversation.user_id))).where(
                Conversation.last_message_at >= thirty_days_ago
            )
        )
        active_users = active_users_result.scalar() or 0

        # Total conversations
        total_conversations_result = await db.execute(select(func.count(Conversation.id)))
        total_conversations = total_conversations_result.scalar() or 0

        # Total messages and tokens
        message_stats_result = await db.execute(
            select(
                func.count(Message.id).label("count"),
                func.sum(Message.tokens_used).label("tokens"),
            )
        )
        message_stats = message_stats_result.first()
        total_messages = message_stats.count or 0
        total_tokens = message_stats.tokens or 0

        # Cache statistics
        cache_stats_result = await db.execute(
            select(
                func.count(Message.cached_tokens_read).label("cached_count"),
                func.sum(Message.cache_discount_usd).label("savings"),
            ).where(Message.role == "assistant")
        )
        cache_stats = cache_stats_result.first()
        cached_messages = cache_stats.cached_count or 0
        cache_savings = float(cache_stats.savings or 0.0)

        # Total images
        total_images_result = await db.execute(select(func.count(GeneratedImage.id)))
        total_images = total_images_result.scalar() or 0

        # Total cost
        usage_stats_result = await db.execute(
            select(func.sum(MonthlyUsageQuota.total_cost_usd))
        )
        total_cost = float(usage_stats_result.scalar() or 0.0)

        # Cache hit rate
        cache_hit_rate = (cached_messages / total_messages) if total_messages > 0 else 0.0

        logger.info("system_stats_retrieved", admin_user_id=str(current_user.id))

        return SystemStatsResponse(
            total_users=total_users,
            active_users_30d=active_users,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_tokens_used=int(total_tokens),
            total_images_generated=total_images,
            total_cost_usd=total_cost,
            total_cache_savings_usd=cache_savings,
            cache_hit_rate=cache_hit_rate,
        )

    except Exception as e:
        logger.error("system_stats_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics",
        )


@router.get("/plan-distribution", response_model=List[PlanDistributionResponse])
async def get_plan_distribution(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[PlanDistributionResponse]:
    """
    Get subscription plan distribution.

    Requires admin role.

    Returns user count and percentage per plan.
    """
    try:
        # Get total users
        total_users_result = await db.execute(select(func.count(Subscription.id)))
        total_users = total_users_result.scalar() or 1  # Avoid division by zero

        # Get plan distribution
        result = await db.execute(
            select(
                Subscription.plan_type,
                func.count(Subscription.id).label("count"),
            ).group_by(Subscription.plan_type)
        )

        distribution = []
        for row in result:
            distribution.append(
                PlanDistributionResponse(
                    plan_type=row.plan_type,
                    user_count=row.count,
                    percentage=(row.count / total_users) * 100,
                )
            )

        logger.info("plan_distribution_retrieved", admin_user_id=str(current_user.id))

        return distribution

    except Exception as e:
        logger.error("plan_distribution_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan distribution",
        )


@router.get("/usage-trends", response_model=List[UsageTrendResponse])
async def get_usage_trends(
    days: int = 30,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[UsageTrendResponse]:
    """
    Get usage trends over time.

    - **days**: Number of days to include (default: 30)

    Requires admin role.

    Returns daily usage statistics.
    """
    try:
        # Get monthly usage data
        result = await db.execute(
            select(
                MonthlyUsageQuota.month_year,
                func.sum(MonthlyUsageQuota.messages_used).label("messages"),
                func.sum(MonthlyUsageQuota.tokens_used).label("tokens"),
                func.sum(MonthlyUsageQuota.images_generated).label("images"),
                func.sum(MonthlyUsageQuota.total_cost_usd).label("cost"),
                func.sum(MonthlyUsageQuota.cache_savings_usd).label("savings"),
            ).group_by(MonthlyUsageQuota.month_year)
            .order_by(MonthlyUsageQuota.month_year.desc())
            .limit(12)  # Last 12 months
        )

        trends = []
        for row in result:
            trends.append(
                UsageTrendResponse(
                    date=row.month_year,
                    messages=row.messages or 0,
                    tokens=row.tokens or 0,
                    images=row.images or 0,
                    cost_usd=float(row.cost or 0.0),
                    cache_savings_usd=float(row.savings or 0.0),
                )
            )

        logger.info("usage_trends_retrieved", admin_user_id=str(current_user.id), days=days)

        return trends

    except Exception as e:
        logger.error("usage_trends_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage trends",
        )


@router.get("/top-users", response_model=List[TopUsersResponse])
async def get_top_users(
    limit: int = 10,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[TopUsersResponse]:
    """
    Get top users by usage.

    - **limit**: Number of top users to return (default: 10)

    Requires admin role.

    Returns top users sorted by total cost.
    """
    try:
        # Get current month
        month_year = datetime.utcnow().strftime("%Y-%m")

        # Get top users
        result = await db.execute(
            select(
                MonthlyUsageQuota.user_id,
                User.email,
                MonthlyUsageQuota.messages_used,
                MonthlyUsageQuota.tokens_used,
                MonthlyUsageQuota.images_generated,
                MonthlyUsageQuota.total_cost_usd,
                MonthlyUsageQuota.cache_savings_usd,
            )
            .join(User, MonthlyUsageQuota.user_id == User.id)
            .where(MonthlyUsageQuota.month_year == month_year)
            .order_by(MonthlyUsageQuota.total_cost_usd.desc())
            .limit(limit)
        )

        top_users = []
        for row in result:
            top_users.append(
                TopUsersResponse(
                    user_id=str(row.user_id),
                    email=row.email or "N/A",
                    messages_count=row.messages_used or 0,
                    tokens_used=row.tokens_used or 0,
                    images_generated=row.images_generated or 0,
                    cost_usd=float(row.total_cost_usd or 0.0),
                    cache_savings_usd=float(row.cache_savings_usd or 0.0),
                )
            )

        logger.info("top_users_retrieved", admin_user_id=str(current_user.id), limit=limit)

        return top_users

    except Exception as e:
        logger.error("top_users_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top users",
        )


@router.get("/model-usage", response_model=List[ModelUsageResponse])
async def get_model_usage(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[ModelUsageResponse]:
    """
    Get model usage statistics.

    Requires admin role.

    Returns usage breakdown per model.
    """
    try:
        result = await db.execute(
            select(
                Message.model_used,
                func.count(Message.id).label("count"),
                func.sum(Message.tokens_used).label("total_tokens"),
                func.avg(Message.tokens_used).label("avg_tokens"),
            )
            .where(Message.model_used.isnot(None), Message.role == "assistant")
            .group_by(Message.model_used)
            .order_by(func.count(Message.id).desc())
        )

        model_usage = []
        for row in result:
            model_usage.append(
                ModelUsageResponse(
                    model=row.model_used,
                    message_count=row.count,
                    total_tokens=int(row.total_tokens or 0),
                    average_tokens_per_message=float(row.avg_tokens or 0.0),
                    total_cost_usd=0.0,  # Calculate if needed
                )
            )

        logger.info("model_usage_retrieved", admin_user_id=str(current_user.id))

        return model_usage

    except Exception as e:
        logger.error("model_usage_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model usage",
        )


@router.get("/cache-performance", response_model=CachePerformanceResponse)
async def get_cache_performance(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CachePerformanceResponse:
    """
    Get prompt caching performance metrics.

    Requires admin role.

    Returns detailed caching statistics.
    """
    try:
        result = await db.execute(
            select(
                func.count(Message.id).label("total"),
                func.count(Message.cached_tokens_read).label("cached"),
                func.sum(Message.cached_tokens_read).label("tokens_cached"),
                func.sum(Message.cache_discount_usd).label("total_savings"),
                func.avg(Message.cache_discount_usd).label("avg_discount"),
            ).where(Message.role == "assistant")
        )

        stats = result.first()

        total_messages = stats.total or 0
        cached_messages = stats.cached or 0
        cache_hit_rate = (cached_messages / total_messages) if total_messages > 0 else 0.0
        total_savings = float(stats.total_savings or 0.0)
        avg_discount = float(stats.avg_discount or 0.0)

        logger.info("cache_performance_retrieved", admin_user_id=str(current_user.id))

        return CachePerformanceResponse(
            total_messages=total_messages,
            cached_messages=cached_messages,
            cache_hit_rate=cache_hit_rate,
            total_tokens_cached=int(stats.tokens_cached or 0),
            total_cache_savings_usd=total_savings,
            average_cache_discount_per_message=avg_discount,
        )

    except Exception as e:
        logger.error("cache_performance_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache performance",
        )
