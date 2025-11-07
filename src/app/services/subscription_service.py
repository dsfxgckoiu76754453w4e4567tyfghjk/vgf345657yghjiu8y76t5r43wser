"""Subscription and usage management service."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import (
    MonthlyUsageQuota,
    PlanLimit,
    Subscription,
)

logger = get_logger(__name__)


class SubscriptionService:
    """
    Service for managing subscriptions and usage.

    Features:
    - Subscription lifecycle management
    - Plan upgrades/downgrades
    - Usage tracking and quota enforcement
    - Cost tracking with cache savings
    - Trial management
    """

    async def create_subscription(
        self,
        user_id: UUID,
        db: AsyncSession,
        plan_type: str = "free",
        billing_cycle: str = "monthly",
        trial_days: int | None = None,
    ) -> Subscription:
        """
        Create a new subscription for a user.

        Args:
            user_id: User ID
            db: Database session
            plan_type: Plan type (free, premium, unlimited, enterprise)
            billing_cycle: Billing cycle (monthly, yearly)
            trial_days: Optional trial period in days

        Returns:
            Created Subscription

        Raises:
            ValueError: If user already has a subscription or plan not found
        """
        # Check if user already has subscription
        existing = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already has an active subscription")

        # Get plan limits to validate plan and get pricing
        result = await db.execute(
            select(PlanLimit).where(PlanLimit.plan_type == plan_type)
        )
        plan_limit = result.scalar_one_or_none()

        if not plan_limit:
            raise ValueError(f"Plan type '{plan_type}' not found")

        # Determine pricing based on billing cycle
        amount_usd = (
            plan_limit.monthly_price_usd
            if billing_cycle == "monthly"
            else plan_limit.yearly_price_usd
        )

        # Set period dates
        current_period_start = datetime.utcnow()
        if billing_cycle == "monthly":
            current_period_end = current_period_start + timedelta(days=30)
        else:
            current_period_end = current_period_start + timedelta(days=365)

        # Set trial if applicable
        trial_ends_at = None
        status = "active"
        if trial_days and trial_days > 0:
            trial_ends_at = current_period_start + timedelta(days=trial_days)
            status = "trial"

        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            status=status,
            billing_cycle=billing_cycle,
            amount_usd=amount_usd,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            trial_ends_at=trial_ends_at,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "subscription_created",
            user_id=str(user_id),
            plan_type=plan_type,
            status=status,
        )

        return subscription

    async def get_subscription(
        self, user_id: UUID, db: AsyncSession
    ) -> Subscription | None:
        """Get user's subscription."""
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_subscription(
        self,
        user_id: UUID,
        db: AsyncSession,
        plan_type: str | None = None,
        status: str | None = None,
        **updates: Any,
    ) -> Subscription:
        """
        Update a subscription.

        Args:
            user_id: User ID
            db: Database session
            plan_type: New plan type (triggers upgrade/downgrade)
            status: New status
            **updates: Additional fields to update

        Returns:
            Updated Subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = await self.get_subscription(user_id, db)
        if not subscription:
            raise ValueError("Subscription not found")

        # Handle plan change
        if plan_type and plan_type != subscription.plan_type:
            subscription = await self._change_plan(subscription, plan_type, db)

        # Update status
        if status:
            subscription.status = status
            if status == "cancelled":
                subscription.cancelled_at = datetime.utcnow()

        # Update other fields
        for key, value in updates.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "subscription_updated",
            user_id=str(user_id),
            plan_type=subscription.plan_type,
            status=subscription.status,
        )

        return subscription

    async def cancel_subscription(
        self, user_id: UUID, db: AsyncSession, at_period_end: bool = True
    ) -> Subscription:
        """Cancel a subscription."""
        subscription = await self.get_subscription(user_id, db)
        if not subscription:
            raise ValueError("Subscription not found")

        if at_period_end:
            subscription.cancel_at_period_end = True
            subscription.status = "active"  # Remains active until period end
        else:
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.utcnow()

        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "subscription_cancelled",
            user_id=str(user_id),
            at_period_end=at_period_end,
        )

        return subscription

    async def track_usage(
        self,
        user_id: UUID,
        db: AsyncSession,
        messages: int = 0,
        tokens: int = 0,
        images: int = 0,
        documents: int = 0,
        audio_minutes: int = 0,
        cost_usd: float = 0.0,
        cache_savings_usd: float = 0.0,
    ) -> MonthlyUsageQuota:
        """
        Track user usage for the current month.

        Args:
            user_id: User ID
            db: Database session
            messages: Number of messages
            tokens: Number of tokens
            images: Number of images generated
            documents: Number of documents processed
            audio_minutes: Minutes of audio processed
            cost_usd: Cost in USD
            cache_savings_usd: Cache savings in USD

        Returns:
            Updated MonthlyUsageQuota
        """
        month_year = datetime.utcnow().strftime("%Y-%m")

        # Get or create quota
        result = await db.execute(
            select(MonthlyUsageQuota).where(
                MonthlyUsageQuota.user_id == user_id,
                MonthlyUsageQuota.month_year == month_year,
            )
        )
        quota = result.scalar_one_or_none()

        if quota:
            # Update existing quota
            quota.messages_used += messages
            quota.tokens_used += tokens
            quota.images_generated += images
            quota.documents_processed += documents
            quota.audio_minutes_used += audio_minutes
            quota.total_cost_usd += cost_usd
            quota.cache_savings_usd += cache_savings_usd
        else:
            # Create new quota
            quota = MonthlyUsageQuota(
                user_id=user_id,
                month_year=month_year,
                messages_used=messages,
                tokens_used=tokens,
                images_generated=images,
                documents_processed=documents,
                audio_minutes_used=audio_minutes,
                total_cost_usd=cost_usd,
                cache_savings_usd=cache_savings_usd,
            )
            db.add(quota)

        await db.commit()
        await db.refresh(quota)

        return quota

    async def get_usage_quota(
        self, user_id: UUID, db: AsyncSession, month_year: str | None = None
    ) -> MonthlyUsageQuota | None:
        """Get user's usage quota for a specific month."""
        if not month_year:
            month_year = datetime.utcnow().strftime("%Y-%m")

        result = await db.execute(
            select(MonthlyUsageQuota).where(
                MonthlyUsageQuota.user_id == user_id,
                MonthlyUsageQuota.month_year == month_year,
            )
        )
        return result.scalar_one_or_none()

    async def check_usage_limits(
        self, user_id: UUID, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Check user's current usage against plan limits.

        Returns:
            Dictionary with usage status and limits
        """
        subscription = await self.get_subscription(user_id, db)
        if not subscription:
            raise ValueError("No active subscription found")

        # Get plan limits
        result = await db.execute(
            select(PlanLimit).where(PlanLimit.plan_type == subscription.plan_type)
        )
        plan_limit = result.scalar_one_or_none()

        if not plan_limit:
            raise ValueError(f"Plan limits not found for {subscription.plan_type}")

        # Get current usage
        quota = await self.get_usage_quota(user_id, db)

        if not quota:
            # No usage yet this month
            return {
                "messages": {"used": 0, "limit": plan_limit.max_messages_per_month, "remaining": plan_limit.max_messages_per_month},
                "tokens": {"used": 0, "limit": plan_limit.max_tokens_per_month, "remaining": plan_limit.max_tokens_per_month},
                "images": {"used": 0, "limit": plan_limit.max_images_per_month, "remaining": plan_limit.max_images_per_month},
                "documents": {"used": 0, "limit": plan_limit.max_documents_per_month, "remaining": plan_limit.max_documents_per_month},
                "audio_minutes": {"used": 0, "limit": plan_limit.max_audio_minutes_per_month, "remaining": plan_limit.max_audio_minutes_per_month},
                "total_cost_usd": quota.total_cost_usd if quota else 0.0,
                "cache_savings_usd": quota.cache_savings_usd if quota else 0.0,
            }

        return {
            "messages": {
                "used": quota.messages_used,
                "limit": plan_limit.max_messages_per_month,
                "remaining": max(0, plan_limit.max_messages_per_month - quota.messages_used),
            },
            "tokens": {
                "used": quota.tokens_used,
                "limit": plan_limit.max_tokens_per_month,
                "remaining": max(0, plan_limit.max_tokens_per_month - quota.tokens_used),
            },
            "images": {
                "used": quota.images_generated,
                "limit": plan_limit.max_images_per_month,
                "remaining": max(0, plan_limit.max_images_per_month - quota.images_generated),
            },
            "documents": {
                "used": quota.documents_processed,
                "limit": plan_limit.max_documents_per_month,
                "remaining": max(0, plan_limit.max_documents_per_month - quota.documents_processed),
            },
            "audio_minutes": {
                "used": quota.audio_minutes_used,
                "limit": plan_limit.max_audio_minutes_per_month,
                "remaining": max(0, plan_limit.max_audio_minutes_per_month - quota.audio_minutes_used),
            },
            "total_cost_usd": quota.total_cost_usd,
            "cache_savings_usd": quota.cache_savings_usd,
        }

    async def _change_plan(
        self, subscription: Subscription, new_plan_type: str, db: AsyncSession
    ) -> Subscription:
        """Handle plan upgrade or downgrade."""
        # Get new plan limits
        result = await db.execute(
            select(PlanLimit).where(PlanLimit.plan_type == new_plan_type)
        )
        new_plan = result.scalar_one_or_none()

        if not new_plan:
            raise ValueError(f"Plan type '{new_plan_type}' not found")

        # Update subscription
        subscription.plan_type = new_plan_type
        subscription.amount_usd = (
            new_plan.monthly_price_usd
            if subscription.billing_cycle == "monthly"
            else new_plan.yearly_price_usd
        )

        logger.info(
            "plan_changed",
            user_id=str(subscription.user_id),
            old_plan=subscription.plan_type,
            new_plan=new_plan_type,
        )

        return subscription

    async def get_plan_limits(self, plan_type: str, db: AsyncSession) -> PlanLimit | None:
        """Get limits for a specific plan."""
        result = await db.execute(
            select(PlanLimit).where(PlanLimit.plan_type == plan_type)
        )
        return result.scalar_one_or_none()

    async def list_all_plans(self, db: AsyncSession) -> list[PlanLimit]:
        """List all available plans."""
        result = await db.execute(select(PlanLimit).order_by(PlanLimit.monthly_price_usd))
        return list(result.scalars().all())


# Global service instance
subscription_service = SubscriptionService()
