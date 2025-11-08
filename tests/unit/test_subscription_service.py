"""Unit tests for subscription service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription, PlanLimit, MonthlyUsageQuota


class TestCreateSubscription:
    """Test subscription creation."""

    @pytest.mark.asyncio
    async def test_create_free_subscription(self):
        """Test creating a free subscription."""
        service = SubscriptionService()
        user_id = uuid4()

        # Mock database session
        mock_db = AsyncMock()

        # Mock existing subscription check (none exists)
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_existing_result

        # Mock plan limit lookup
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="free",
            max_messages_per_month=100,
            max_tokens_per_month=100000,
            max_images_per_month=10,
            max_documents_per_month=10,
            max_audio_minutes_per_month=10,
            monthly_price_usd=0.0,
            yearly_price_usd=0.0,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        # Set up execute to return different results for different queries
        mock_db.execute.side_effect = [mock_existing_result, mock_plan_result]

        subscription = await service.create_subscription(
            user_id=user_id, db=mock_db, plan_type="free"
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(self):
        """Test creating subscription with trial period."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing subscription check
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_existing_result

        # Mock plan limit lookup
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium",
            max_messages_per_month=1000,
            max_tokens_per_month=1000000,
            max_images_per_month=100,
            max_documents_per_month=100,
            max_audio_minutes_per_month=100,
            monthly_price_usd=9.99,
            yearly_price_usd=99.99,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        mock_db.execute.side_effect = [mock_existing_result, mock_plan_result]

        subscription = await service.create_subscription(
            user_id=user_id, db=mock_db, plan_type="premium", trial_days=7
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_already_exists(self):
        """Test creating subscription when one already exists."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing subscription (user already has one)
        mock_existing_result = MagicMock()
        mock_existing = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type="free",
            status="active",
            billing_cycle="monthly",
            amount_usd=0.0,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
        )
        mock_existing_result.scalar_one_or_none.return_value = mock_existing
        mock_db.execute.return_value = mock_existing_result

        with pytest.raises(ValueError, match="User already has an active subscription"):
            await service.create_subscription(user_id=user_id, db=mock_db)

    @pytest.mark.asyncio
    async def test_create_subscription_invalid_plan(self):
        """Test creating subscription with invalid plan type."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock no existing subscription
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        # Mock plan not found
        mock_plan_result = MagicMock()
        mock_plan_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_existing_result, mock_plan_result]

        with pytest.raises(ValueError, match="Plan type 'invalid' not found"):
            await service.create_subscription(
                user_id=user_id, db=mock_db, plan_type="invalid"
            )


class TestUsageTracking:
    """Test usage tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_usage_new_quota(self):
        """Test tracking usage creates new quota."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock no existing quota
        mock_quota_result = MagicMock()
        mock_quota_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_quota_result

        quota = await service.track_usage(
            user_id=user_id,
            db=mock_db,
            messages=1,
            tokens=100,
            cost_usd=0.001,
            cache_savings_usd=0.0005,
        )

        # Verify new quota was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_usage_existing_quota(self):
        """Test tracking usage updates existing quota."""
        service = SubscriptionService()
        user_id = uuid4()
        month_year = datetime.utcnow().strftime("%Y-%m")

        mock_db = AsyncMock()

        # Mock existing quota
        mock_quota_result = MagicMock()
        existing_quota = MagicMock()
        existing_quota.messages_used = 10
        existing_quota.tokens_used = 1000
        existing_quota.images_generated = 2
        existing_quota.documents_processed = 1
        existing_quota.audio_minutes_used = 5
        existing_quota.total_cost_usd = 0.05
        existing_quota.cache_savings_usd = 0.01
        mock_quota_result.scalar_one_or_none.return_value = existing_quota
        mock_db.execute.return_value = mock_quota_result

        quota = await service.track_usage(
            user_id=user_id,
            db=mock_db,
            messages=1,
            tokens=100,
            images=1,
            cost_usd=0.002,
            cache_savings_usd=0.001,
        )

        # Verify quota was updated (not added)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_usage_limits(self):
        """Test checking usage against limits."""
        service = SubscriptionService()
        user_id = uuid4()
        month_year = datetime.utcnow().strftime("%Y-%m")

        mock_db = AsyncMock()

        # Mock subscription
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type="premium",
            status="active",
            billing_cycle="monthly",
            amount_usd=9.99,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        # Mock plan limits
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium",
            max_messages_per_month=1000,
            max_tokens_per_month=1000000,
            max_images_per_month=100,
            max_documents_per_month=100,
            max_audio_minutes_per_month=100,
            monthly_price_usd=9.99,
            yearly_price_usd=99.99,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        # Mock usage quota
        mock_quota_result = MagicMock()
        mock_quota = MagicMock()
        mock_quota.messages_used = 100
        mock_quota.tokens_used = 50000
        mock_quota.images_generated = 10
        mock_quota.documents_processed = 5
        mock_quota.audio_minutes_used = 20
        mock_quota.total_cost_usd = 0.5
        mock_quota.cache_savings_usd = 0.1
        mock_quota_result.scalar_one_or_none.return_value = mock_quota

        mock_db.execute.side_effect = [
            mock_sub_result,
            mock_plan_result,
            mock_quota_result,
        ]

        limits = await service.check_usage_limits(user_id=user_id, db=mock_db)

        # Verify usage stats
        assert limits["messages"]["used"] == 100
        assert limits["messages"]["limit"] == 1000
        assert limits["messages"]["remaining"] == 900
        assert limits["tokens"]["used"] == 50000
        assert limits["total_cost_usd"] == 0.5
        assert limits["cache_savings_usd"] == 0.1


class TestSubscriptionManagement:
    """Test subscription management operations."""

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self):
        """Test cancelling subscription at period end."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing subscription
        mock_sub_result = MagicMock()
        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription.plan_type = "premium"
        mock_subscription.status = "active"
        mock_subscription.cancel_at_period_end = False
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_sub_result

        subscription = await service.cancel_subscription(
            user_id=user_id, db=mock_db, at_period_end=True
        )

        # Verify subscription was updated
        assert mock_subscription.cancel_at_period_end == True
        assert mock_subscription.status == "active"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(self):
        """Test cancelling subscription immediately."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing subscription
        mock_sub_result = MagicMock()
        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription.status = "active"
        mock_subscription.cancelled_at = None
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_sub_result

        subscription = await service.cancel_subscription(
            user_id=user_id, db=mock_db, at_period_end=False
        )

        # Verify subscription was cancelled
        assert mock_subscription.status == "cancelled"
        assert mock_subscription.cancelled_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_subscription_change_plan(self):
        """Test updating subscription to change plan."""
        service = SubscriptionService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing subscription
        mock_sub_result = MagicMock()
        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription.plan_type = "free"
        mock_subscription.billing_cycle = "monthly"
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        # Mock new plan limits
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium",
            max_messages_per_month=1000,
            max_tokens_per_month=1000000,
            max_images_per_month=100,
            max_documents_per_month=100,
            max_audio_minutes_per_month=100,
            monthly_price_usd=9.99,
            yearly_price_usd=99.99,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        mock_db.execute.side_effect = [mock_sub_result, mock_plan_result]

        subscription = await service.update_subscription(
            user_id=user_id, db=mock_db, plan_type="premium"
        )

        # Verify plan was changed
        assert mock_subscription.plan_type == "premium"
        assert mock_subscription.amount_usd == 9.99
        mock_db.commit.assert_called_once()


class TestPlanLimits:
    """Test plan limit operations."""

    @pytest.mark.asyncio
    async def test_get_plan_limits(self):
        """Test getting plan limits."""
        service = SubscriptionService()

        mock_db = AsyncMock()

        # Mock plan limits
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium",
            max_messages_per_month=1000,
            max_tokens_per_month=1000000,
            max_images_per_month=100,
            max_documents_per_month=100,
            max_audio_minutes_per_month=100,
            monthly_price_usd=9.99,
            yearly_price_usd=99.99,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan
        mock_db.execute.return_value = mock_plan_result

        plan = await service.get_plan_limits(plan_type="premium", db=mock_db)

        assert plan.plan_type == "premium"
        assert plan.max_messages_per_month == 1000

    @pytest.mark.asyncio
    async def test_list_all_plans(self):
        """Test listing all available plans."""
        service = SubscriptionService()

        mock_db = AsyncMock()

        # Mock multiple plans
        mock_result = MagicMock()
        mock_plans = [
            PlanLimit(plan_type="free", monthly_price_usd=0.0, yearly_price_usd=0.0, max_messages_per_month=100, max_tokens_per_month=100000, max_images_per_month=10, max_documents_per_month=10, max_audio_minutes_per_month=10),
            PlanLimit(plan_type="premium", monthly_price_usd=9.99, yearly_price_usd=99.99, max_messages_per_month=1000, max_tokens_per_month=1000000, max_images_per_month=100, max_documents_per_month=100, max_audio_minutes_per_month=100),
        ]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_plans
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        plans = await service.list_all_plans(db=mock_db)

        assert len(plans) == 2
        assert plans[0].plan_type == "free"
        assert plans[1].plan_type == "premium"
