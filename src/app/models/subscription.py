"""Subscription and plan models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Subscription(Base):
    """User subscriptions."""

    __tablename__ = "subscriptions"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Plan details
    plan_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # free, premium, unlimited, enterprise
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # active, cancelled, expired, trial
    billing_cycle: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # monthly, yearly

    # Pricing
    amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Period tracking
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Trial
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Payment integration
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "plan_type IN ('free', 'premium', 'unlimited', 'enterprise')",
            name="check_plan_type",
        ),
        CheckConstraint(
            "status IN ('active', 'cancelled', 'expired', 'trial')",
            name="check_status",
        ),
        CheckConstraint(
            "billing_cycle IN ('monthly', 'yearly')",
            name="check_billing_cycle",
        ),
        UniqueConstraint("user_id", name="unique_user_subscription"),
    )

    def __repr__(self) -> str:
        return f"<Subscription(user_id={self.user_id}, plan={self.plan_type}, status={self.status})>"


class PlanLimit(Base):
    """Plan limits and features."""

    __tablename__ = "plan_limits"

    # Primary Key
    plan_type: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Usage limits
    max_messages_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    max_tokens_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    max_images_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    max_documents_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    max_audio_minutes_per_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Feature flags
    web_search_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    image_generation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    pdf_processing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_processing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_caching_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    advanced_models_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Limits
    presets_limit: Mapped[int] = mapped_column(Integer, default=0)
    max_context_length: Mapped[int] = mapped_column(Integer, default=4096)

    # Support
    priority_support: Mapped[bool] = mapped_column(Boolean, default=False)

    # Pricing
    monthly_price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    yearly_price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PlanLimit(plan_type={self.plan_type})>"


class MonthlyUsageQuota(Base):
    """Monthly usage tracking per user."""

    __tablename__ = "monthly_usage_quotas"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Period
    month_year: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., "2025-11"

    # Usage counters
    messages_used: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    images_generated: Mapped[int] = mapped_column(Integer, default=0)
    documents_processed: Mapped[int] = mapped_column(Integer, default=0)
    audio_minutes_used: Mapped[int] = mapped_column(Integer, default=0)

    # Cost tracking
    total_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.0)
    cache_savings_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "month_year", name="unique_user_month_quota"),
    )

    def __repr__(self) -> str:
        return f"<MonthlyUsageQuota(user_id={self.user_id}, period={self.month_year})>"


class GeneratedImage(Base):
    """Track generated images."""

    __tablename__ = "generated_images"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("conversations.id"), nullable=True
    )

    # Image details
    prompt: Mapped[str] = mapped_column(String(2000), nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # Image storage
    image_data_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # base64
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # external URL

    # Configuration
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    modalities: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cost tracking
    generation_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<GeneratedImage(id={self.id}, user_id={self.user_id})>"


class ModelPreset(Base):
    """User-defined model presets."""

    __tablename__ = "model_presets"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # Nullable for org presets

    # Preset identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Configuration
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    top_p: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Advanced configuration
    extra_model_config: Mapped[Optional[dict]] = mapped_column(
        String, nullable=True
    )  # JSONB for all params
    provider_preferences: Mapped[Optional[dict]] = mapped_column(
        String, nullable=True
    )  # JSONB

    # Sharing
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="unique_user_preset_slug"),
    )

    def __repr__(self) -> str:
        return f"<ModelPreset(slug={self.slug}, model={self.model})>"
