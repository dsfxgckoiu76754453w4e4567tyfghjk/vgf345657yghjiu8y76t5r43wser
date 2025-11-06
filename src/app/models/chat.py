"""Chat and conversation models."""

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


class Conversation(Base):
    """User conversations/chat sessions."""

    __tablename__ = "conversations"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # Nullable for truly anonymous

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_title_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    mode: Mapped[str] = mapped_column(
        String(50), default="standard"
    )  # standard, fast, scholarly, deep_search, filtered

    # Privacy settings
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_truly_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(is_truly_anonymous = TRUE AND user_id IS NULL) OR (is_truly_anonymous = FALSE)",
            name="check_anonymous_logic",
        ),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, mode={self.mode})>"


class Message(Base):
    """Chat messages in conversations."""

    __tablename__ = "messages"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), nullable=False)

    # Message identification
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # LLM processing details (only for assistant messages)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_purpose: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Detailed token tracking
    input_tokens_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_user_prompt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_system_prompt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_rag_context: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_web_search_results: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_tool_outputs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_memory_context: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens_other: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Output tokens
    output_tokens_generated: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens_citations: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens_suggestions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Total tokens
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    # Response quality metadata
    response_quality_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    has_citations: Mapped[bool] = mapped_column(Boolean, default=False)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Processing metadata
    llm_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    processing_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Message status
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_stopped_by_user: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    feedbacks: Mapped[list["MessageFeedback"]] = relationship(
        "MessageFeedback", back_populates="message", cascade="all, delete-orphan"
    )
    edit_history: Mapped[list["MessageEditHistory"]] = relationship(
        "MessageEditHistory", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class MessageEditHistory(Base):
    """Message edit history tracking."""

    __tablename__ = "message_edit_history"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id"), nullable=False)

    # Edit details
    previous_content: Mapped[str] = mapped_column(Text, nullable=False)
    new_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp
    edited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="edit_history")

    def __repr__(self) -> str:
        return f"<MessageEditHistory(message_id={self.message_id})>"


class MessageFeedback(Base):
    """User feedback on messages."""

    __tablename__ = "message_feedback"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Feedback type
    feedback_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # like, dislike, stop_generation

    # Detailed feedback (for dislikes)
    dislike_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Context
    was_helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="feedbacks")

    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(feedback_text) <= 5000", name="check_feedback_text_length"),
    )

    def __repr__(self) -> str:
        return f"<MessageFeedback(message_id={self.message_id}, type={self.feedback_type})>"
