"""Admin and system administration models."""

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
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SystemAdmin(Base):
    """System administrators with role-based permissions."""

    __tablename__ = "system_admins"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    # Admin role and permissions
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # super_admin, content_admin, support_admin, scholar_reviewer
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    # Specific capabilities per role
    can_access_dashboard: Mapped[bool] = mapped_column(Boolean, default=True)
    can_modify_content: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)
    can_approve_chunking: Mapped[bool] = mapped_column(Boolean, default=False)
    can_answer_tickets: Mapped[bool] = mapped_column(Boolean, default=False)
    can_review_responses: Mapped[bool] = mapped_column(Boolean, default=False)

    # Admin status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    assigned_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("system_admins.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tasks: Mapped[list["AdminTask"]] = relationship(
        "AdminTask", back_populates="admin", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin', 'content_admin', 'support_admin', 'scholar_reviewer')",
            name="check_admin_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<SystemAdmin(id={self.id}, role={self.role})>"


class AdminTask(Base):
    """Admin task assignments and tracking."""

    __tablename__ = "admin_tasks"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("system_admins.id"), nullable=False)

    # Task details
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # chunk_review, ticket_response, content_upload, quality_review
    task_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, urgent

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, in_progress, completed, cancelled

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Related entities
    related_document_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    related_ticket_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("support_tickets.id"), nullable=True
    )
    related_chunk_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("document_chunks.id"), nullable=True
    )

    # Performance tracking
    completion_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )  # 0.00 to 1.00

    # Relationships
    admin: Mapped["SystemAdmin"] = relationship("SystemAdmin", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<AdminTask(id={self.id}, type={self.task_type}, status={self.status})>"


class AdminAPIKey(Base):
    """Admin API keys for programmatic access."""

    __tablename__ = "admin_api_keys"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Key details
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    permissions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Status and expiration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<AdminAPIKey(id={self.id}, name={self.key_name})>"


class AdminActivityLog(Base):
    """Log of all admin activities for audit trail."""

    __tablename__ = "admin_activity_logs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Activity details
    admin_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AdminActivityLog(id={self.id}, action={self.action})>"


class ContentModerationLog(Base):
    """Log of content moderation actions."""

    __tablename__ = "content_moderation_logs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Moderation details
    moderator_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # approve, reject, flag
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ContentModerationLog(id={self.id}, action={self.action})>"
