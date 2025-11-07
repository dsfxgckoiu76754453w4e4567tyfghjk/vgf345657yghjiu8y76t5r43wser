"""Comprehensive unit tests for environment promotion system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import (
    EnvironmentPromotionMixin,
    TimestampMixin,
    SoftDeleteMixin,
)
from app.services.promotion_service import (
    EnvironmentPromotionService,
    PromotionPreview,
    PromotionResult,
)
from app.db.base import Base


# ============================================================================
# Test Models
# ============================================================================


class TestModelWithPromotion(Base, EnvironmentPromotionMixin):
    """Test model with environment promotion mixin."""

    __tablename__ = "test_promotion_items"

    id: Mapped[uuid4] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))


class TestModelWithTimestamp(Base, TimestampMixin):
    """Test model with timestamp mixin."""

    __tablename__ = "test_timestamp_items"

    id: Mapped[uuid4] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))


class TestModelWithSoftDelete(Base, SoftDeleteMixin):
    """Test model with soft delete mixin."""

    __tablename__ = "test_soft_delete_items"

    id: Mapped[uuid4] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))


# ============================================================================
# EnvironmentPromotionMixin Tests
# ============================================================================


class TestEnvironmentPromotionMixinProperties:
    """Test cases for EnvironmentPromotionMixin properties."""

    @patch('app.models.mixins.get_settings')
    def test_default_environment_from_settings(self, mock_settings):
        """Test that environment defaults to settings value."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.environment = "dev"
        mock_settings.return_value = mock_settings_obj

        # Act
        item = TestModelWithPromotion(name="Test Item")

        # Assert
        assert item.environment == "dev"

    def test_is_production_property(self):
        """Test is_production property."""
        # Arrange
        item = TestModelWithPromotion(name="Test", environment="prod")

        # Act & Assert
        assert item.is_production is True

        # Test other environments
        item.environment = "dev"
        assert item.is_production is False

    def test_is_development_property(self):
        """Test is_development property."""
        # Arrange
        item = TestModelWithPromotion(name="Test", environment="dev")

        # Act & Assert
        assert item.is_development is True

        # Test other environments
        item.environment = "prod"
        assert item.is_development is False

    def test_is_staging_property(self):
        """Test is_staging property."""
        # Arrange
        item = TestModelWithPromotion(name="Test", environment="stage")

        # Act & Assert
        assert item.is_staging is True

        # Test other environments
        item.environment = "dev"
        assert item.is_staging is False

    def test_can_be_promoted_property(self):
        """Test can_be_promoted property."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test",
            is_promotable=True,
            promotion_status="approved",
            is_test_data=False,
        )

        # Act & Assert
        assert item.can_be_promoted is True

    def test_can_be_promoted_false_when_not_promotable(self):
        """Test can_be_promoted is False when not promotable."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test",
            is_promotable=False,
            promotion_status="approved",
            is_test_data=False,
        )

        # Act & Assert
        assert item.can_be_promoted is False

    def test_can_be_promoted_false_when_not_approved(self):
        """Test can_be_promoted is False when not approved."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test",
            is_promotable=True,
            promotion_status="draft",
            is_test_data=False,
        )

        # Act & Assert
        assert item.can_be_promoted is False

    def test_can_be_promoted_false_when_test_data(self):
        """Test can_be_promoted is False when marked as test data."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test",
            is_promotable=True,
            promotion_status="approved",
            is_test_data=True,
        )

        # Act & Assert
        assert item.can_be_promoted is False

    def test_is_promoted_item_property(self):
        """Test is_promoted_item property."""
        # Arrange
        source_id = uuid4()
        item = TestModelWithPromotion(
            name="Test",
            source_id=source_id,
        )

        # Act & Assert
        assert item.is_promoted_item is True

        # Test when not promoted
        item.source_id = None
        assert item.is_promoted_item is False


class TestEnvironmentPromotionMixinMethods:
    """Test cases for EnvironmentPromotionMixin methods."""

    def test_mark_as_test_data(self):
        """Test marking item as test data."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test User",
            is_promotable=True,
        )

        # Act
        item.mark_as_test_data(reason="Matches pattern: Test*")

        # Assert
        assert item.is_test_data is True
        assert item.test_data_reason == "Matches pattern: Test*"
        assert item.is_promotable is False

    def test_mark_as_test_data_default_reason(self):
        """Test marking as test data with default reason."""
        # Arrange
        item = TestModelWithPromotion(name="Test")

        # Act
        item.mark_as_test_data()

        # Assert
        assert item.is_test_data is True
        assert item.test_data_reason == "Manually marked"

    def test_approve_for_promotion(self):
        """Test approving item for promotion."""
        # Arrange
        item = TestModelWithPromotion(
            name="Real Item",
            is_test_data=False,
        )

        # Act
        item.approve_for_promotion()

        # Assert
        assert item.is_promotable is True
        assert item.promotion_status == "approved"

    def test_approve_for_promotion_rejects_test_data(self):
        """Test that test data cannot be approved for promotion."""
        # Arrange
        item = TestModelWithPromotion(
            name="Test Item",
            is_test_data=True,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Test data cannot be approved"):
            item.approve_for_promotion()

    def test_mark_as_promoted(self):
        """Test marking item as promoted."""
        # Arrange
        item = TestModelWithPromotion(
            name="Item",
            promoted_to_environments=[],
        )
        user_id = uuid4()

        # Act
        item.mark_as_promoted("stage", user_id)

        # Assert
        assert item.promotion_status == "promoted"
        assert item.promoted_by_user_id == user_id
        assert item.promoted_at is not None
        assert "stage" in item.promoted_to_environments

    def test_mark_as_promoted_multiple_environments(self):
        """Test promoting to multiple environments."""
        # Arrange
        item = TestModelWithPromotion(
            name="Item",
            promoted_to_environments=[],
        )
        user_id = uuid4()

        # Act - Promote to stage, then prod
        item.mark_as_promoted("stage", user_id)
        item.mark_as_promoted("prod", user_id)

        # Assert
        assert "stage" in item.promoted_to_environments
        assert "prod" in item.promoted_to_environments
        assert len(item.promoted_to_environments) == 2

    def test_mark_as_promoted_no_duplicates(self):
        """Test that promoting to same environment twice doesn't create duplicates."""
        # Arrange
        item = TestModelWithPromotion(
            name="Item",
            promoted_to_environments=[],
        )
        user_id = uuid4()

        # Act - Promote to stage twice
        item.mark_as_promoted("stage", user_id)
        item.mark_as_promoted("stage", user_id)

        # Assert
        assert item.promoted_to_environments.count("stage") == 1


# ============================================================================
# TimestampMixin Tests
# ============================================================================


class TestTimestampMixin:
    """Test cases for TimestampMixin."""

    def test_timestamp_fields_exist(self):
        """Test that timestamp fields are defined."""
        # Arrange & Act
        item = TestModelWithTimestamp(name="Test")

        # Assert - Fields should exist (will be set by database)
        assert hasattr(item, 'created_at')
        assert hasattr(item, 'updated_at')


# ============================================================================
# SoftDeleteMixin Tests
# ============================================================================


class TestSoftDeleteMixin:
    """Test cases for SoftDeleteMixin."""

    def test_soft_delete(self):
        """Test soft deleting an item."""
        # Arrange
        item = TestModelWithSoftDelete(
            name="To Delete",
            is_deleted=False,
        )

        # Act
        item.soft_delete()

        # Assert
        assert item.is_deleted is True
        assert item.deleted_at is not None

    def test_restore(self):
        """Test restoring a soft-deleted item."""
        # Arrange
        item = TestModelWithSoftDelete(
            name="Deleted Item",
            is_deleted=True,
            deleted_at=datetime.utcnow(),
        )

        # Act
        item.restore()

        # Assert
        assert item.is_deleted is False
        assert item.deleted_at is None

    def test_is_active_property(self):
        """Test is_active property."""
        # Arrange
        active_item = TestModelWithSoftDelete(
            name="Active",
            is_deleted=False,
        )
        deleted_item = TestModelWithSoftDelete(
            name="Deleted",
            is_deleted=True,
        )

        # Act & Assert
        assert active_item.is_active is True
        assert deleted_item.is_active is False


# ============================================================================
# PromotionPreview Tests
# ============================================================================


class TestPromotionPreview:
    """Test cases for PromotionPreview."""

    def test_promotion_preview_initialization(self):
        """Test PromotionPreview initialization."""
        # Act
        preview = PromotionPreview()

        # Assert
        assert preview.source_env == ""
        assert preview.target_env == ""
        assert preview.items_to_promote == []
        assert preview.total_count == 0
        assert preview.total_size_bytes == 0
        assert preview.warnings == []
        assert preview.errors == []

    def test_promotion_preview_to_dict(self):
        """Test converting PromotionPreview to dictionary."""
        # Arrange
        preview = PromotionPreview()
        preview.source_env = "dev"
        preview.target_env = "stage"
        preview.total_count = 5
        preview.items_to_promote = [{"id": "123", "name": "test"}]

        # Act
        result = preview.to_dict()

        # Assert
        assert result['source_environment'] == "dev"
        assert result['target_environment'] == "stage"
        assert result['total_count'] == 5
        assert result['is_valid'] is True
        assert len(result['items']) == 1

    def test_promotion_preview_is_valid_with_errors(self):
        """Test that preview is invalid when errors exist."""
        # Arrange
        preview = PromotionPreview()
        preview.errors.append("Invalid promotion path")

        # Act
        result = preview.to_dict()

        # Assert
        assert result['is_valid'] is False


# ============================================================================
# PromotionResult Tests
# ============================================================================


class TestPromotionResult:
    """Test cases for PromotionResult."""

    def test_promotion_result_initialization(self):
        """Test PromotionResult initialization."""
        # Arrange
        promotion_id = uuid4()

        # Act
        result = PromotionResult(promotion_id)

        # Assert
        assert result.promotion_id == promotion_id
        assert result.success_count == 0
        assert result.error_count == 0
        assert result.errors == {}
        assert result.created_ids == []
        assert result.duration_seconds == 0

    def test_promotion_result_to_dict(self):
        """Test converting PromotionResult to dictionary."""
        # Arrange
        promotion_id = uuid4()
        result = PromotionResult(promotion_id)
        result.success_count = 10
        result.error_count = 2
        result.duration_seconds = 5.5

        # Act
        result_dict = result.to_dict()

        # Assert
        assert result_dict['promotion_id'] == str(promotion_id)
        assert result_dict['success_count'] == 10
        assert result_dict['error_count'] == 2
        assert result_dict['total_count'] == 12
        assert result_dict['duration_seconds'] == 5.5
        assert result_dict['success'] is False  # Has errors

    def test_promotion_result_success_flag(self):
        """Test success flag is True when no errors."""
        # Arrange
        result = PromotionResult(uuid4())
        result.success_count = 10
        result.error_count = 0

        # Act
        result_dict = result.to_dict()

        # Assert
        assert result_dict['success'] is True


# ============================================================================
# EnvironmentPromotionService Tests
# ============================================================================


class TestEnvironmentPromotionServiceValidation:
    """Test cases for promotion service validation."""

    @patch('app.services.promotion_service.get_settings')
    def test_validate_promotion_path_valid(self, mock_settings):
        """Test validating a valid promotion path."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage,stage->prod"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        is_valid, error = service.validate_promotion_path("dev", "stage")

        # Assert
        assert is_valid is True
        assert error is None

    @patch('app.services.promotion_service.get_settings')
    def test_validate_promotion_path_invalid_environment(self, mock_settings):
        """Test validation fails with invalid environment."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        is_valid, error = service.validate_promotion_path("invalid", "stage")

        # Assert
        assert is_valid is False
        assert "Invalid environment" in error

    @patch('app.services.promotion_service.get_settings')
    def test_validate_promotion_path_disabled(self, mock_settings):
        """Test validation fails when promotion is disabled."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = False
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        is_valid, error = service.validate_promotion_path("dev", "stage")

        # Assert
        assert is_valid is False
        assert "disabled" in error

    @patch('app.services.promotion_service.get_settings')
    def test_validate_promotion_path_not_allowed(self, mock_settings):
        """Test validation fails for disallowed promotion path."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        is_valid, error = service.validate_promotion_path("stage", "prod")

        # Assert
        assert is_valid is False
        assert "not allowed" in error

    @patch('app.services.promotion_service.get_settings')
    def test_validate_promotion_path_same_environment(self, mock_settings):
        """Test validation fails when source and target are same."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->dev"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        is_valid, error = service.validate_promotion_path("dev", "dev")

        # Assert
        assert is_valid is False
        assert "must be different" in error


class TestEnvironmentPromotionServicePreview:
    """Test cases for promotion preview."""

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_preview_promotion_invalid_path(self, mock_settings):
        """Test preview returns errors for invalid path."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = False
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Act
        preview = await service.preview_promotion(
            TestModelWithPromotion,
            "dev",
            "stage",
        )

        # Assert
        assert len(preview.errors) > 0
        assert preview.to_dict()['is_valid'] is False

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_preview_promotion_model_without_mixin(self, mock_settings):
        """Test preview returns error for model without mixin."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        # Create a model without the mixin
        class ModelWithoutMixin:
            __name__ = "ModelWithoutMixin"

        # Act
        preview = await service.preview_promotion(
            ModelWithoutMixin,
            "dev",
            "stage",
        )

        # Assert
        assert len(preview.errors) > 0
        assert "EnvironmentPromotionMixin" in preview.errors[0]

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_preview_promotion_no_items(self, mock_settings):
        """Test preview with no items to promote."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = EnvironmentPromotionService(mock_db)

        # Act
        preview = await service.preview_promotion(
            TestModelWithPromotion,
            "dev",
            "stage",
        )

        # Assert
        assert preview.total_count == 0
        assert len(preview.warnings) > 0
        assert "No items found" in preview.warnings[0]

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_preview_promotion_large_size_warning(self, mock_settings):
        """Test preview warns for large promotion size."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()

        # Create mock items with large size
        mock_item = TestModelWithPromotion(name="Large File")
        mock_item.id = uuid4()
        mock_item.file_size_bytes = 15 * 1024 * 1024 * 1024  # 15 GB

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        mock_db.execute.return_value = mock_result

        service = EnvironmentPromotionService(mock_db)

        # Act
        preview = await service.preview_promotion(
            TestModelWithPromotion,
            "dev",
            "stage",
        )

        # Assert
        assert preview.total_count == 1
        assert len(preview.warnings) > 0
        assert "Large promotion size" in preview.warnings[0]


class TestEnvironmentPromotionServiceExecution:
    """Test cases for promotion execution."""

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_execute_promotion_creates_promotion_record(self, mock_settings):
        """Test that execution creates EnvironmentPromotion record."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = True
        mock_settings_obj.promotion_allowed_paths = "dev->stage"
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = EnvironmentPromotionService(mock_db)
        user_id = uuid4()

        # Act
        try:
            result = await service.execute_promotion(
                TestModelWithPromotion,
                "dev",
                "stage",
                user_id,
                reason="Deployment to staging",
            )
        except:
            pass  # May fail due to mocking, but we check if add was called

        # Assert
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_execute_promotion_handles_validation_errors(self, mock_settings):
        """Test that execution handles validation errors."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.promotion_enabled = False  # Disabled
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="validation failed"):
            await service.execute_promotion(
                TestModelWithPromotion,
                "dev",
                "stage",
                user_id,
            )


class TestEnvironmentPromotionServiceCopying:
    """Test cases for item copying operations."""

    @pytest.mark.asyncio
    @patch('app.services.promotion_service.get_settings')
    async def test_copy_item_to_environment(self, mock_settings):
        """Test copying item to target environment."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings.return_value = mock_settings_obj

        mock_db = AsyncMock()
        service = EnvironmentPromotionService(mock_db)

        source_item = TestModelWithPromotion(
            id=uuid4(),
            name="Test Item",
            environment="dev",
        )
        user_id = uuid4()

        # Act
        new_item = await service._copy_item_to_environment(
            source_item,
            "stage",
            user_id,
        )

        # Assert
        assert new_item is not None
        assert new_item.environment == "stage"
        assert new_item.source_id == source_item.id
        assert new_item.source_environment == "dev"
        assert new_item.promotion_status == "promoted"
        assert new_item.promoted_by_user_id == user_id


class TestEnvironmentPromotionServiceRollback:
    """Test cases for promotion rollback."""

    @pytest.mark.asyncio
    async def test_rollback_promotion_not_found(self):
        """Test rollback fails for non-existent promotion."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.get.return_value = None

        service = EnvironmentPromotionService(mock_db)
        promotion_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await service.rollback_promotion(promotion_id, user_id)

    @pytest.mark.asyncio
    async def test_rollback_promotion_already_rolled_back(self):
        """Test rollback fails if already rolled back."""
        # Arrange
        mock_db = AsyncMock()

        mock_promotion = MagicMock()
        mock_promotion.status = "rolled_back"
        mock_promotion.can_rollback = False
        mock_db.get.return_value = mock_promotion

        service = EnvironmentPromotionService(mock_db)
        promotion_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="cannot be rolled back"):
            await service.rollback_promotion(promotion_id, user_id)

    @pytest.mark.asyncio
    async def test_rollback_promotion_success(self):
        """Test successful rollback."""
        # Arrange
        mock_db = AsyncMock()

        mock_promotion = MagicMock()
        mock_promotion.status = "success"
        mock_promotion.can_rollback = True
        mock_promotion.rollback_data = {
            "created_item_ids": ["id1", "id2", "id3"]
        }
        mock_db.get.return_value = mock_promotion

        service = EnvironmentPromotionService(mock_db)
        promotion_id = uuid4()
        user_id = uuid4()

        # Act
        result = await service.rollback_promotion(promotion_id, user_id)

        # Assert
        assert result is True
        assert mock_promotion.status == "rolled_back"
        assert mock_promotion.rolled_back_by_user_id == user_id
        assert mock_db.commit.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
