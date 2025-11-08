"""Model mixins for common functionality across models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.config import get_settings

settings = get_settings()


class EnvironmentPromotionMixin:
    """
    Mixin for environment-aware models with promotion support.

    Apply to ALL models that need environment isolation and/or promotion between environments.

    Key Features:
    - Environment tracking (dev, stage, prod)
    - Test data detection and marking
    - Promotion support for approved content
    - Audit trail for promoted items

    Usage:
        class MyModel(Base, EnvironmentPromotionMixin):
            __tablename__ = "my_table"
            # ... your fields
    """

    # ========================================================================
    # Environment Tracking
    # ========================================================================

    environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        default=lambda: settings.environment,
        comment="Environment: dev, stage, prod"
    )

    # ========================================================================
    # Test Data Detection
    # ========================================================================

    is_test_data: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="True if this is test/dummy data (auto-detected or manually marked)"
    )

    test_data_reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Why marked as test data (e.g., 'matches pattern: John Doe')"
    )

    # ========================================================================
    # Promotion Support
    # ========================================================================

    is_promotable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Can this item be promoted between environments?"
    )

    promotion_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="draft",
        index=True,
        comment="draft, approved, promoted, deprecated"
    )

    promoted_from_environment: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Original environment where this was created"
    )

    promoted_to_environments: Mapped[list] = mapped_column(
        ARRAY(String),
        default=list,
        comment="Promotion history: ['dev', 'stage', 'prod']"
    )

    promoted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this item was promoted"
    )

    promoted_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="User who approved the promotion"
    )

    # ========================================================================
    # Source Tracking (for promoted items)
    # ========================================================================

    source_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID in source environment (for linking promoted items)"
    )

    source_environment: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Where this was promoted from"
    )

    # ========================================================================
    # Helper Properties
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if this is production data."""
        return self.environment == "prod"

    @property
    def is_development(self) -> bool:
        """Check if this is development data."""
        return self.environment == "dev"

    @property
    def is_staging(self) -> bool:
        """Check if this is staging data."""
        return self.environment == "stage"

    @property
    def can_be_promoted(self) -> bool:
        """Check if this item can be promoted."""
        return (
            self.is_promotable
            and self.promotion_status == "approved"
            and not self.is_test_data
        )

    @property
    def is_promoted_item(self) -> bool:
        """Check if this item was promoted from another environment."""
        return self.source_id is not None

    def mark_as_test_data(self, reason: str = "Manually marked"):
        """Mark this item as test data."""
        self.is_test_data = True
        self.test_data_reason = reason
        self.is_promotable = False  # Test data can't be promoted

    def approve_for_promotion(self):
        """Approve this item for promotion to next environment."""
        if self.is_test_data:
            raise ValueError("Test data cannot be approved for promotion")

        self.is_promotable = True
        self.promotion_status = "approved"

    def mark_as_promoted(
        self,
        target_environment: str,
        promoted_by_user_id: UUID
    ):
        """Mark this item as promoted."""
        self.promotion_status = "promoted"
        self.promoted_at = datetime.utcnow()
        self.promoted_by_user_id = promoted_by_user_id

        if target_environment not in self.promoted_to_environments:
            self.promoted_to_environments.append(target_environment)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Soft delete flag"
    )

    def soft_delete(self):
        """Mark as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore soft-deleted item."""
        self.is_deleted = False
        self.deleted_at = None

    @property
    def is_active(self) -> bool:
        """Check if item is active (not deleted)."""
        return not self.is_deleted
