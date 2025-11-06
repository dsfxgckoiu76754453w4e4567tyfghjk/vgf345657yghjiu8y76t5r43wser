"""External API client models for third-party integration."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ExternalAPIClient(Base):
    """Third-party API clients with granular controls."""

    __tablename__ = "external_api_clients"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Client identification
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # API credentials
    api_key_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # NEVER store plain-text
    api_key_prefix: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # For display (e.g., "sk_live_abc")

    # Status and controls (NEW in v3.0 - super-admin dashboard)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, suspended, banned
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banned_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )  # References system_admins
    banned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    suspension_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Rate limiting (custom per client)
    tier: Mapped[str] = mapped_column(
        String(50), default="basic"
    )  # basic, standard, premium, enterprise
    custom_requests_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_requests_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_requests_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_requests_per_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Usage tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    # Current period (for quota reset)
    current_period_requests: Mapped[int] = mapped_column(Integer, default=0)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Permissions
    allowed_features: Mapped[dict] = mapped_column(
        JSONB, default=list
    )  # ["chat", "rag", "ahkam", "hadith"]
    allowed_models: Mapped[dict] = mapped_column(JSONB, default=list)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Admin tracking
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    usage_logs: Mapped[list["APIUsageLog"]] = relationship(
        "APIUsageLog", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ExternalAPIClient(client_name={self.client_name}, tier={self.tier})>"


class APIUsageLog(Base):
    """Detailed usage tracking for external API clients."""

    __tablename__ = "api_usage_logs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Request details
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # GET, POST, etc.
    request_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response details
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Token usage
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    # Features used
    feature_used: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # chat, rag, ahkam, hadith
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Error tracking
    error_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    client: Mapped["ExternalAPIClient"] = relationship(
        "ExternalAPIClient", back_populates="usage_logs"
    )

    def __repr__(self) -> str:
        return f"<APIUsageLog(client_id={self.client_id}, endpoint={self.endpoint})>"


# Alias for backward compatibility
ExternalAPIUsageLog = APIUsageLog
