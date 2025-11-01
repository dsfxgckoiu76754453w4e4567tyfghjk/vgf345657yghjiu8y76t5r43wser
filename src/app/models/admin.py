"""Admin and system administration models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
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
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, nullable=False)

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
    assigned_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
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
    admin_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

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
        PG_UUID(as_uuid=True), nullable=True
    )
    related_ticket_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    related_chunk_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
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
