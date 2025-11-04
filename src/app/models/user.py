"""User and authentication models."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """Main users table for authentication and profile management."""

    __tablename__ = "users"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Authentication fields (email/password OR Google OAuth)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_picture_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Religious preferences
    marja_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="fa")

    # Account status
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    account_type: Mapped[str] = mapped_column(
        String(20), default="free"
    )  # anonymous, free, premium, unlimited, test

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    linked_providers: Mapped[list["LinkedAuthProvider"]] = relationship(
        "LinkedAuthProvider", back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings", back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(email IS NOT NULL AND password_hash IS NOT NULL) OR "
            "(google_id IS NOT NULL) OR "
            "(account_type = 'anonymous' AND email IS NULL AND google_id IS NULL)",
            name="check_auth_method",
        ),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class OTPCode(Base):
    """OTP verification codes for email verification and password reset."""

    __tablename__ = "otp_codes"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # OTP details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email_verification, password_reset

    # Status tracking
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Link to user (nullable for new registrations)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="check_otp_purpose",
        ),
    )

    def __repr__(self) -> str:
        return f"<OTPCode(email={self.email}, purpose={self.purpose})>"


class UserSession(Base):
    """User sessions for JWT or refresh tokens."""

    __tablename__ = "user_sessions"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Session identification
    session_token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(500), unique=True, nullable=True
    )

    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Session lifecycle
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"


class LinkedAuthProvider(Base):
    """Cross-platform authentication linking (Email ↔ Google OAuth)."""

    __tablename__ = "linked_auth_providers"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Provider details
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email, google, apple, github
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Link status
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # The original sign-up method
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="linked_providers")

    # Constraints
    __table_args__ = (UniqueConstraint("user_id", "provider_type", name="uq_user_provider"),)

    def __repr__(self) -> str:
        return f"<LinkedAuthProvider(user_id={self.user_id}, provider={self.provider_type})>"


class UserSettings(Base):
    """User settings and preferences."""

    __tablename__ = "user_settings"

    # Primary Key (one-to-one with User)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    # UI preferences
    theme: Mapped[str] = mapped_column(String(20), default="light")  # light, dark, auto
    font_size: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # small, medium, large

    # Chat preferences
    default_chat_mode: Mapped[str] = mapped_column(
        String(50), default="standard"
    )  # standard, fast, scholarly, deep_search, filtered
    auto_play_quranic_audio: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notification settings
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Privacy settings
    allow_data_for_training: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_leaderboard: Mapped[bool] = mapped_column(Boolean, default=False)

    # Rate limiting tier
    rate_limit_tier: Mapped[str] = mapped_column(String(50), default="free")

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, theme={self.theme})>"
