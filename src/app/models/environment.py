"""Environment and promotion tracking models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class EnvironmentPromotion(Base):
    """
    Audit log for all environment promotions.

    Tracks when content is promoted from one environment to another.
    Supports rollback functionality.
    """

    __tablename__ = "environment_promotions"

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Promotion metadata
    promotion_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: rag_documents, audio_files, config, multi"
    )

    source_environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Source: dev, stage, prod"
    )

    target_environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Target: dev, stage, prod"
    )

    # What was promoted
    items_promoted: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Details of promoted items with IDs and counts"
    )
    # Example:
    # {
    #   "document_ids": ["uuid1", "uuid2"],
    #   "file_ids": ["uuid3"],
    #   "total_count": 3,
    #   "types": {
    #     "documents": 2,
    #     "files": 1
    #   }
    # }

    # Execution details
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        default="pending",
        comment="Status: pending, in_progress, success, failed, rolled_back"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Promotion execution time"
    )

    # Results
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of items successfully promoted"
    )

    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of items that failed"
    )

    errors: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error details for failed items"
    )
    # Example:
    # {
    #   "doc_uuid1": "Vector copy failed: connection timeout",
    #   "file_uuid2": "MinIO upload failed: bucket not found"
    # }

    # Audit
    promoted_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User who executed the promotion"
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Reason for promotion"
    )

    # Rollback support
    can_rollback: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this promotion can be rolled back"
    )

    rollback_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Data needed for rollback (IDs created in target)"
    )
    # Example:
    # {
    #   "created_document_ids": ["uuid1", "uuid2"],
    #   "created_file_ids": ["uuid3"],
    #   "created_vector_ids": ["uuid4"]
    # }

    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    rolled_back_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<EnvironmentPromotion("
            f"id={self.id}, "
            f"{self.source_environment}→{self.target_environment}, "
            f"status={self.status}, "
            f"items={self.success_count}"
            f")>"
        )


class EnvironmentAccessLog(Base):
    """
    Audit log for cross-environment access.

    Tracks when users access different environments for debugging/testing.
    """

    __tablename__ = "environment_access_logs"

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # User and environment
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Environment accessed: dev, stage, prod"
    )

    # Access details
    access_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: login, test_account_create, data_access, api_call"
    )

    access_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Why accessing this environment (required for prod)"
    )

    # Additional context
    access_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional access context"
    )

    def __repr__(self) -> str:
        return (
            f"<EnvironmentAccessLog("
            f"user_id={self.user_id}, "
            f"environment={self.environment}, "
            f"type={self.access_type}"
            f")>"
        )


class DeveloperAction(Base):
    """
    Audit log for all developer actions in stage/prod environments.

    Tracks privileged developer actions like test account creation.
    """

    __tablename__ = "developer_actions"

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Developer and environment
    developer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Developer who performed the action"
    )

    environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Environment: dev, stage, prod"
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action: create_test_account, delete_test_account, access_user_data, etc."
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Justification for the action (required)"
    )

    details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional action details"
    )
    # Example:
    # {
    #   "test_user_id": "uuid",
    #   "test_user_email": "test@test.com",
    #   "expires_at": "2024-01-01T00:00:00Z"
    # }

    # Audit context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Result
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether action succeeded"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Error message if action failed"
    )

    def __repr__(self) -> str:
        return (
            f"<DeveloperAction("
            f"developer_id={self.developer_id}, "
            f"environment={self.environment}, "
            f"action={self.action}"
            f")>"
        )
