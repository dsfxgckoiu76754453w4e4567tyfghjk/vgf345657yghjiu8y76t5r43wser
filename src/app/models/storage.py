"""File storage models for tracking MinIO uploads."""

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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class StoredFile(Base):
    """Files stored in MinIO object storage."""

    __tablename__ = "stored_files"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Ownership
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    conversation_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )

    # File identification
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # MinIO storage details
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # File metadata
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # image, document, audio, video, other
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # File attributes
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For images
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For images
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For audio/video

    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    access_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=True)
    processing_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pending, processing, completed, failed

    # Security
    is_scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    scan_result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # clean, infected, error

    # Usage tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Cost tracking
    storage_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "file_type IN ('image', 'document', 'audio', 'video', 'other')",
            name="check_file_type",
        ),
        CheckConstraint("file_size_bytes >= 0", name="check_file_size"),
        CheckConstraint("download_count >= 0", name="check_download_count"),
    )

    def __repr__(self) -> str:
        return f"<StoredFile(id={self.id}, filename={self.filename}, bucket={self.bucket})>"


class UserStorageQuota(Base):
    """Track user storage quotas and usage."""

    __tablename__ = "user_storage_quotas"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Quota limits (in bytes)
    quota_limit_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Current usage (in bytes)
    total_used_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Usage breakdown by type
    images_used_bytes: Mapped[int] = mapped_column(Integer, default=0)
    documents_used_bytes: Mapped[int] = mapped_column(Integer, default=0)
    audio_used_bytes: Mapped[int] = mapped_column(Integer, default=0)
    other_used_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # File counts
    total_files: Mapped[int] = mapped_column(Integer, default=0)

    # Cost tracking
    total_storage_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("quota_limit_bytes >= 0", name="check_quota_limit"),
        CheckConstraint("total_used_bytes >= 0", name="check_total_used"),
        CheckConstraint("total_files >= 0", name="check_total_files"),
    )

    def __repr__(self) -> str:
        return f"<UserStorageQuota(user_id={self.user_id}, used={self.total_used_bytes}, limit={self.quota_limit_bytes})>"

    @property
    def usage_percentage(self) -> float:
        """Calculate storage usage percentage."""
        if self.quota_limit_bytes == 0:
            return 0.0
        return (self.total_used_bytes / self.quota_limit_bytes) * 100

    @property
    def remaining_bytes(self) -> int:
        """Calculate remaining storage space."""
        return max(0, self.quota_limit_bytes - self.total_used_bytes)

    @property
    def is_quota_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.total_used_bytes >= self.quota_limit_bytes
