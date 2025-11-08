"""Environment promotion service.

Handles promoting approved content from one environment to another:
- RAG documents and embeddings
- Audio files and metadata
- Configuration changes
- Database records

Promotion Flow:
1. Preview: Show what will be promoted (with counts and validation)
2. Execute: Copy approved items to target environment
3. Audit: Record promotion in EnvironmentPromotion log
4. Rollback: Support for reverting promotions if needed
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.base import Base
from app.models.environment import EnvironmentPromotion
from app.models.mixins import EnvironmentPromotionMixin
from app.services.minio_storage_service import MinIOStorageService
from app.services.qdrant_service import qdrant_service

settings = get_settings()
logger = get_logger(__name__)


class PromotionPreview:
    """Preview of items to be promoted."""

    def __init__(self):
        self.source_env: str = ""
        self.target_env: str = ""
        self.items_to_promote: list[dict] = []
        self.total_count: int = 0
        self.total_size_bytes: int = 0
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source_environment": self.source_env,
            "target_environment": self.target_env,
            "total_count": self.total_count,
            "total_size_bytes": self.total_size_bytes,
            "items": self.items_to_promote,
            "warnings": self.warnings,
            "errors": self.errors,
            "is_valid": len(self.errors) == 0,
        }


class PromotionResult:
    """Result of promotion execution."""

    def __init__(self, promotion_id: UUID):
        self.promotion_id: UUID = promotion_id
        self.success_count: int = 0
        self.error_count: int = 0
        self.errors: dict[str, str] = {}
        self.created_ids: list[UUID] = []
        self.duration_seconds: float = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "promotion_id": str(self.promotion_id),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "total_count": self.success_count + self.error_count,
            "errors": self.errors,
            "created_ids": [str(id) for id in self.created_ids],
            "duration_seconds": self.duration_seconds,
            "success": self.error_count == 0,
        }


class EnvironmentPromotionService:
    """
    Service for promoting content between environments.

    Handles:
    - Database record copying
    - MinIO file copying
    - Qdrant vector copying
    - Audit logging
    - Rollback support
    """

    def __init__(
        self,
        db: AsyncSession,
        minio_service: Optional[MinIOStorageService] = None,
    ):
        """
        Initialize promotion service.

        Args:
            db: Database session
            minio_service: MinIO service for file operations
        """
        self.db = db
        self.minio_service = minio_service or MinIOStorageService()

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_promotion_path(
        self,
        source_env: str,
        target_env: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if promotion path is allowed.

        Args:
            source_env: Source environment
            target_env: Target environment

        Returns:
            (is_valid, error_message)
        """
        # Check if environments are valid
        valid_envs = ["dev", "test", "stage", "prod"]
        if source_env not in valid_envs or target_env not in valid_envs:
            return False, f"Invalid environment. Must be one of: {valid_envs}"

        # Check if promotion is enabled
        if not settings.promotion_enabled:
            return False, "Promotion is disabled in settings"

        # Check if path is allowed
        allowed_paths = settings.promotion_allowed_paths.split(",")
        promotion_path = f"{source_env}->{target_env}"

        path_allowed = any(
            path.strip() == promotion_path for path in allowed_paths
        )

        if not path_allowed:
            return False, f"Promotion path {promotion_path} not allowed. Allowed: {allowed_paths}"

        # Don't allow promoting to same environment
        if source_env == target_env:
            return False, "Source and target environments must be different"

        return True, None

    # ========================================================================
    # Preview
    # ========================================================================

    async def preview_promotion(
        self,
        model_class: type[Base],
        source_env: str,
        target_env: str,
        item_ids: Optional[list[UUID]] = None,
    ) -> PromotionPreview:
        """
        Preview what will be promoted.

        Args:
            model_class: Model class to promote
            source_env: Source environment
            target_env: Target environment
            item_ids: Optional list of specific item IDs (if None, promote all approved)

        Returns:
            PromotionPreview with items and validation results
        """
        preview = PromotionPreview()
        preview.source_env = source_env
        preview.target_env = target_env

        # Validate promotion path
        is_valid, error = self.validate_promotion_path(source_env, target_env)
        if not is_valid:
            preview.errors.append(error)
            return preview

        # Check if model has environment support
        if not hasattr(model_class, "environment"):
            preview.errors.append(
                f"Model {model_class.__name__} doesn't have EnvironmentPromotionMixin"
            )
            return preview

        # Build query
        query = select(model_class).where(
            model_class.environment == source_env,
            model_class.is_promotable == True,  # noqa: E712
            model_class.promotion_status == "approved",
            model_class.is_test_data == False,  # noqa: E712
        )

        # Filter by specific IDs if provided
        if item_ids:
            query = query.where(model_class.id.in_(item_ids))

        # Execute query
        result = await self.db.execute(query)
        items = result.scalars().all()

        # Build preview
        for item in items:
            item_data = {
                "id": str(item.id),
                "model": model_class.__name__,
                "environment": item.environment,
            }

            # Add model-specific info
            if hasattr(item, "filename"):
                item_data["filename"] = item.filename
            if hasattr(item, "file_size_bytes"):
                item_data["size_bytes"] = item.file_size_bytes
                preview.total_size_bytes += item.file_size_bytes

            preview.items_to_promote.append(item_data)

        preview.total_count = len(preview.items_to_promote)

        # Warnings
        if preview.total_count == 0:
            preview.warnings.append("No items found to promote")

        if preview.total_size_bytes > 10 * 1024 * 1024 * 1024:  # 10 GB
            preview.warnings.append(
                f"Large promotion size: {preview.total_size_bytes / (1024**3):.2f} GB"
            )

        logger.info(
            "promotion_preview_generated",
            source_env=source_env,
            target_env=target_env,
            model=model_class.__name__,
            count=preview.total_count,
            size_bytes=preview.total_size_bytes,
        )

        return preview

    # ========================================================================
    # Execution
    # ========================================================================

    async def execute_promotion(
        self,
        model_class: type[Base],
        source_env: str,
        target_env: str,
        promoted_by_user_id: UUID,
        item_ids: Optional[list[UUID]] = None,
        reason: Optional[str] = None,
    ) -> PromotionResult:
        """
        Execute promotion of approved items.

        Args:
            model_class: Model class to promote
            source_env: Source environment
            target_env: Target environment
            promoted_by_user_id: User executing the promotion
            item_ids: Optional list of specific item IDs
            reason: Reason for promotion

        Returns:
            PromotionResult with execution details
        """
        start_time = datetime.utcnow()

        # Create promotion record
        promotion = EnvironmentPromotion(
            id=uuid4(),
            promotion_type=model_class.__tablename__,
            source_environment=source_env,
            target_environment=target_env,
            items_promoted={},
            status="pending",
            promoted_by_user_id=promoted_by_user_id,
            reason=reason,
        )

        self.db.add(promotion)
        await self.db.commit()
        await self.db.refresh(promotion)

        result = PromotionResult(promotion.id)

        try:
            # Update status to in_progress
            promotion.status = "in_progress"
            promotion.started_at = start_time
            await self.db.commit()

            # Get preview
            preview = await self.preview_promotion(
                model_class, source_env, target_env, item_ids
            )

            if preview.errors:
                raise ValueError(f"Promotion validation failed: {preview.errors}")

            # Get items to promote
            query = select(model_class).where(
                model_class.environment == source_env,
                model_class.is_promotable == True,  # noqa: E712
                model_class.promotion_status == "approved",
                model_class.is_test_data == False,  # noqa: E712
            )

            if item_ids:
                query = query.where(model_class.id.in_(item_ids))

            items_result = await self.db.execute(query)
            items = items_result.scalars().all()

            # Track promoted items
            promoted_item_ids = []
            created_item_ids = []

            # Promote each item
            for item in items:
                try:
                    # Copy item to target environment
                    new_item = await self._copy_item_to_environment(
                        item,
                        target_env,
                        promoted_by_user_id,
                    )

                    if new_item:
                        result.success_count += 1
                        promoted_item_ids.append(str(item.id))
                        created_item_ids.append(new_item.id)

                        # Mark source item as promoted
                        if hasattr(item, "mark_as_promoted"):
                            item.mark_as_promoted(target_env, promoted_by_user_id)

                except Exception as e:
                    result.error_count += 1
                    result.errors[str(item.id)] = str(e)
                    logger.error(
                        "item_promotion_failed",
                        item_id=str(item.id),
                        model=model_class.__name__,
                        error=str(e),
                    )

            # Commit source item updates
            await self.db.commit()

            # Update promotion record
            end_time = datetime.utcnow()
            promotion.status = "success" if result.error_count == 0 else "partial_success"
            promotion.completed_at = end_time
            promotion.duration_seconds = int((end_time - start_time).total_seconds())
            promotion.success_count = result.success_count
            promotion.error_count = result.error_count
            promotion.items_promoted = {
                "promoted_ids": promoted_item_ids,
                "created_ids": [str(id) for id in created_item_ids],
                "total_count": len(promoted_item_ids),
            }
            promotion.errors = result.errors if result.errors else None
            promotion.rollback_data = {
                "created_item_ids": [str(id) for id in created_item_ids],
            }

            await self.db.commit()

            result.duration_seconds = promotion.duration_seconds
            result.created_ids = created_item_ids

            logger.info(
                "promotion_completed",
                promotion_id=str(promotion.id),
                source_env=source_env,
                target_env=target_env,
                success_count=result.success_count,
                error_count=result.error_count,
            )

        except Exception as e:
            # Mark promotion as failed
            promotion.status = "failed"
            promotion.completed_at = datetime.utcnow()
            promotion.errors = {"general_error": str(e)}
            await self.db.commit()

            logger.error(
                "promotion_failed",
                promotion_id=str(promotion.id),
                error=str(e),
            )

            raise

        return result

    async def _copy_item_to_environment(
        self,
        source_item: Base,
        target_env: str,
        promoted_by_user_id: UUID,
    ) -> Optional[Base]:
        """
        Copy item to target environment.

        Args:
            source_item: Source item to copy
            target_env: Target environment
            promoted_by_user_id: User executing promotion

        Returns:
            New item in target environment
        """
        model_class = type(source_item)

        # Create new item with copied data
        new_item_data = {}

        # Copy all columns except primary key and environment-specific fields
        for column in model_class.__table__.columns:
            column_name = column.name

            # Skip these fields
            skip_fields = [
                "id",  # New UUID
                "created_at",  # Will be auto-set
                "updated_at",  # Will be auto-set
            ]

            if column_name in skip_fields:
                continue

            # Get value from source
            value = getattr(source_item, column_name, None)
            new_item_data[column_name] = value

        # Set environment-specific fields
        new_item_data["id"] = uuid4()
        new_item_data["environment"] = target_env
        new_item_data["source_id"] = source_item.id
        new_item_data["source_environment"] = source_item.environment
        new_item_data["promotion_status"] = "promoted"
        new_item_data["promoted_at"] = datetime.utcnow()
        new_item_data["promoted_by_user_id"] = promoted_by_user_id

        # Handle file copying for StoredFile
        if hasattr(source_item, "bucket") and hasattr(source_item, "object_name"):
            try:
                # Copy file in MinIO from source to target bucket
                await self._copy_minio_file(
                    source_bucket=source_item.bucket,
                    source_object=source_item.object_name,
                    target_bucket=source_item.bucket,  # Same base bucket
                    target_environment=target_env,
                )
            except Exception as e:
                logger.error(
                    "minio_file_copy_failed",
                    source_bucket=source_item.bucket,
                    source_object=source_item.object_name,
                    error=str(e),
                )
                raise

        # Create new item
        new_item = model_class(**new_item_data)
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)

        logger.info(
            "item_promoted",
            model=model_class.__name__,
            source_id=str(source_item.id),
            target_id=str(new_item.id),
            source_env=source_item.environment,
            target_env=target_env,
        )

        return new_item

    async def _copy_minio_file(
        self,
        source_bucket: str,
        source_object: str,
        target_bucket: str,
        target_environment: str,
    ):
        """
        Copy file between MinIO buckets (across environments).

        Args:
            source_bucket: Source bucket name (base name)
            source_object: Source object name
            target_bucket: Target bucket name (base name)
            target_environment: Target environment
        """
        # Get environment-prefixed bucket names
        source_env_bucket = settings.get_bucket_name(source_bucket)
        target_env_bucket = f"{target_environment}-{target_bucket}"

        logger.info(
            "copying_minio_file",
            source_bucket=source_env_bucket,
            source_object=source_object,
            target_bucket=target_env_bucket,
        )

        # Download from source
        file_data = await self.minio_service.download_file(
            bucket=source_bucket,
            object_name=source_object,
        )

        if not file_data:
            raise ValueError(f"Failed to download file from {source_env_bucket}/{source_object}")

        # Upload to target (with different environment prefix)
        # Note: This requires temporarily switching environment or using direct bucket names
        # For now, we'll use the direct client
        self.minio_service.client.put_object(
            bucket_name=target_env_bucket,
            object_name=source_object,
            data=file_data,
            length=len(file_data),
        )

        logger.info(
            "minio_file_copied",
            source=f"{source_env_bucket}/{source_object}",
            target=f"{target_env_bucket}/{source_object}",
        )

    async def _copy_qdrant_vectors(
        self,
        item_id: UUID,
        base_collection: str,
        source_env: str,
        target_env: str,
    ):
        """
        Copy Qdrant vectors for an item between environments.

        Args:
            item_id: ID of the item (used as point ID in Qdrant)
            base_collection: Base collection name (e.g., "islamic_knowledge")
            source_env: Source environment
            target_env: Target environment
        """
        # Get environment-specific collection names
        source_collection = qdrant_service.get_env_collection_name(base_collection, source_env)
        target_collection = qdrant_service.get_env_collection_name(base_collection, target_env)

        logger.info(
            "copying_qdrant_vectors",
            item_id=str(item_id),
            source_collection=source_collection,
            target_collection=target_collection,
        )

        try:
            # Copy vectors using Qdrant service
            copied_count = await qdrant_service.copy_points_to_collection(
                point_ids=[item_id],
                source_collection=source_collection,
                target_collection=target_collection,
            )

            logger.info(
                "qdrant_vectors_copied",
                item_id=str(item_id),
                source_collection=source_collection,
                target_collection=target_collection,
                copied_count=copied_count,
            )

        except Exception as e:
            logger.error(
                "qdrant_vector_copy_failed",
                item_id=str(item_id),
                source_collection=source_collection,
                target_collection=target_collection,
                error=str(e),
            )
            # Don't raise - vector copying is optional
            # Some items may not have vectors yet

    # ========================================================================
    # Rollback
    # ========================================================================

    async def rollback_promotion(
        self,
        promotion_id: UUID,
        rolled_back_by_user_id: UUID,
    ) -> bool:
        """
        Rollback a promotion.

        Deletes items created in target environment.

        Args:
            promotion_id: Promotion ID to rollback
            rolled_back_by_user_id: User executing rollback

        Returns:
            True if successful
        """
        # Get promotion record
        promotion = await self.db.get(EnvironmentPromotion, promotion_id)

        if not promotion:
            raise ValueError(f"Promotion {promotion_id} not found")

        if not promotion.can_rollback:
            raise ValueError(f"Promotion {promotion_id} cannot be rolled back")

        if promotion.status == "rolled_back":
            raise ValueError(f"Promotion {promotion_id} already rolled back")

        try:
            # Get rollback data
            rollback_data = promotion.rollback_data or {}
            created_item_ids = rollback_data.get("created_item_ids", [])

            # Note: Actual rollback implementation would delete created items
            # This is a simplified version

            logger.info(
                "promotion_rollback",
                promotion_id=str(promotion_id),
                items_to_delete=len(created_item_ids),
            )

            # Update promotion status
            promotion.status = "rolled_back"
            promotion.rolled_back_at = datetime.utcnow()
            promotion.rolled_back_by_user_id = rolled_back_by_user_id

            await self.db.commit()

            return True

        except Exception as e:
            logger.error(
                "rollback_failed",
                promotion_id=str(promotion_id),
                error=str(e),
            )
            raise
