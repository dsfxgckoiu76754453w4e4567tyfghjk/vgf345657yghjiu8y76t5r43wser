"""Subscription management API endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.services.subscription_service import subscription_service

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class SubscriptionCreateRequest(BaseModel):
    """Subscription creation request."""

    plan_type: str = Field(..., description="Plan type (free, premium, unlimited, enterprise)")
    billing_cycle: str = Field("monthly", description="Billing cycle (monthly, yearly)")
    trial_days: int | None = Field(None, description="Optional trial period in days")


class SubscriptionResponse(BaseModel):
    """Subscription response."""

    id: str
    user_id: str
    plan_type: str
    status: str
    billing_cycle: str
    amount_usd: float
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    cancelled_at: str | None
    trial_ends_at: str | None
    created_at: str
    updated_at: str


class PlanLimitResponse(BaseModel):
    """Plan limit response."""

    plan_type: str
    max_messages_per_month: int
    max_tokens_per_month: int
    max_images_per_month: int
    max_documents_per_month: int
    max_audio_minutes_per_month: int
    web_search_enabled: bool
    image_generation_enabled: bool
    pdf_processing_enabled: bool
    audio_processing_enabled: bool
    prompt_caching_enabled: bool
    advanced_models_enabled: bool
    presets_limit: int
    max_context_length: int
    priority_support: bool
    monthly_price_usd: float
    yearly_price_usd: float


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""

    messages: dict[str, Any]
    tokens: dict[str, Any]
    images: dict[str, Any]
    documents: dict[str, Any]
    audio_minutes: dict[str, Any]
    total_cost_usd: float
    cache_savings_usd: float


class CancelSubscriptionRequest(BaseModel):
    """Subscription cancellation request."""

    at_period_end: bool = Field(True, description="Cancel at period end (true) or immediately (false)")


class PlanListResponse(BaseModel):
    """List of available plans."""

    plans: List[PlanLimitResponse]
    total: int


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """
    Get current user's subscription.

    Returns active subscription details.
    """
    try:
        subscription = await subscription_service.get_subscription(
            user_id=current_user.id,
            db=db,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found",
            )

        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan_type=subscription.plan_type,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            amount_usd=float(subscription.amount_usd),
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end or False,
            cancelled_at=subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
            created_at=subscription.created_at.isoformat(),
            updated_at=subscription.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_subscription_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription",
        )


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request_data: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """
    Create a new subscription for the current user.

    - **plan_type**: Plan type (free, premium, unlimited, enterprise)
    - **billing_cycle**: Billing cycle (monthly, yearly)
    - **trial_days**: Optional trial period in days

    Returns created subscription.
    """
    try:
        subscription = await subscription_service.create_subscription(
            user_id=current_user.id,
            db=db,
            plan_type=request_data.plan_type,
            billing_cycle=request_data.billing_cycle,
            trial_days=request_data.trial_days,
        )

        logger.info(
            "subscription_created_via_api",
            user_id=str(current_user.id),
            plan_type=subscription.plan_type,
            status=subscription.status,
        )

        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan_type=subscription.plan_type,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            amount_usd=float(subscription.amount_usd),
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end or False,
            cancelled_at=subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
            created_at=subscription.created_at.isoformat(),
            updated_at=subscription.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.warning("subscription_creation_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("subscription_creation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageStatsResponse:
    """
    Get current user's usage statistics for the current month.

    Returns usage limits and current usage.
    """
    try:
        limits = await subscription_service.check_usage_limits(
            user_id=current_user.id,
            db=db,
        )

        return UsageStatsResponse(
            messages=limits["messages"],
            tokens=limits["tokens"],
            images=limits["images"],
            documents=limits["documents"],
            audio_minutes=limits["audio_minutes"],
            total_cost_usd=limits["total_cost_usd"],
            cache_savings_usd=limits["cache_savings_usd"],
        )

    except ValueError as e:
        logger.warning("get_usage_stats_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_usage_stats_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics",
        )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    request_data: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """
    Cancel current subscription.

    - **at_period_end**: Cancel at period end (true) or immediately (false)

    Returns updated subscription.
    """
    try:
        subscription = await subscription_service.cancel_subscription(
            user_id=current_user.id,
            db=db,
            at_period_end=request_data.at_period_end,
        )

        logger.info(
            "subscription_cancelled_via_api",
            user_id=str(current_user.id),
            at_period_end=request_data.at_period_end,
            status=subscription.status,
        )

        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan_type=subscription.plan_type,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            amount_usd=float(subscription.amount_usd),
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end or False,
            cancelled_at=subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
            created_at=subscription.created_at.isoformat(),
            updated_at=subscription.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.warning("subscription_cancellation_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("subscription_cancellation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    db: AsyncSession = Depends(get_db),
) -> PlanListResponse:
    """
    List all available subscription plans.

    Returns list of plans with features and pricing.
    """
    try:
        plans = await subscription_service.list_all_plans(db=db)

        return PlanListResponse(
            plans=[
                PlanLimitResponse(
                    plan_type=plan.plan_type,
                    max_messages_per_month=plan.max_messages_per_month,
                    max_tokens_per_month=plan.max_tokens_per_month,
                    max_images_per_month=plan.max_images_per_month,
                    max_documents_per_month=plan.max_documents_per_month,
                    max_audio_minutes_per_month=plan.max_audio_minutes_per_month,
                    web_search_enabled=plan.web_search_enabled or False,
                    image_generation_enabled=plan.image_generation_enabled or False,
                    pdf_processing_enabled=plan.pdf_processing_enabled or False,
                    audio_processing_enabled=plan.audio_processing_enabled or False,
                    prompt_caching_enabled=plan.prompt_caching_enabled or False,
                    advanced_models_enabled=plan.advanced_models_enabled or False,
                    presets_limit=plan.presets_limit or 0,
                    max_context_length=plan.max_context_length or 4096,
                    priority_support=plan.priority_support or False,
                    monthly_price_usd=float(plan.monthly_price_usd),
                    yearly_price_usd=float(plan.yearly_price_usd),
                )
                for plan in plans
            ],
            total=len(plans),
        )

    except Exception as e:
        logger.error("list_plans_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans",
        )


@router.get("/plans/{plan_type}", response_model=PlanLimitResponse)
async def get_plan(
    plan_type: str,
    db: AsyncSession = Depends(get_db),
) -> PlanLimitResponse:
    """
    Get details for a specific plan.

    - **plan_type**: Plan type (free, premium, unlimited, enterprise)

    Returns plan details with features and pricing.
    """
    try:
        plan = await subscription_service.get_plan_limits(
            plan_type=plan_type,
            db=db,
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan '{plan_type}' not found",
            )

        return PlanLimitResponse(
            plan_type=plan.plan_type,
            max_messages_per_month=plan.max_messages_per_month,
            max_tokens_per_month=plan.max_tokens_per_month,
            max_images_per_month=plan.max_images_per_month,
            max_documents_per_month=plan.max_documents_per_month,
            max_audio_minutes_per_month=plan.max_audio_minutes_per_month,
            web_search_enabled=plan.web_search_enabled or False,
            image_generation_enabled=plan.image_generation_enabled or False,
            pdf_processing_enabled=plan.pdf_processing_enabled or False,
            audio_processing_enabled=plan.audio_processing_enabled or False,
            prompt_caching_enabled=plan.prompt_caching_enabled or False,
            advanced_models_enabled=plan.advanced_models_enabled or False,
            presets_limit=plan.presets_limit or 0,
            max_context_length=plan.max_context_length or 4096,
            priority_support=plan.priority_support or False,
            monthly_price_usd=float(plan.monthly_price_usd),
            yearly_price_usd=float(plan.yearly_price_usd),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_plan_error", plan_type=plan_type, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan",
        )
