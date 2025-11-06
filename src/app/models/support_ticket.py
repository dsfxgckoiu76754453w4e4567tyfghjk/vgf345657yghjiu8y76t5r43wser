"""Support ticket models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SupportTicket(Base):
    """User support tickets."""

    __tablename__ = "support_tickets"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # User information
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Ticket details
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # technical, content, account, billing, other
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, urgent

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="open"
    )  # open, in_progress, resolved, closed

    # Assignment
    assigned_to_admin_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("system_admins.id"), nullable=True
    )

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    responses: Mapped[list["SupportTicketResponse"]] = relationship(
        "SupportTicketResponse", back_populates="ticket", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "category IN ('technical', 'content', 'account', 'billing', 'other')",
            name="check_ticket_category",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="check_ticket_priority",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed')",
            name="check_ticket_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, subject={self.subject[:30]}, status={self.status})>"


class SupportTicketResponse(Base):
    """Responses to support tickets."""

    __tablename__ = "support_ticket_responses"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("support_tickets.id"), nullable=False)
    responder_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )  # Can be user or admin

    # Response content
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_staff_response: Mapped[bool] = mapped_column(default=False)  # True if from admin/staff

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="responses")

    def __repr__(self) -> str:
        return f"<SupportTicketResponse(id={self.id}, ticket_id={self.ticket_id})>"
