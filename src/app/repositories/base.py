"""Base repository classes with environment awareness.

Provides environment-scoped data access with automatic:
- Environment filtering (only query current environment's data)
- Test data exclusion (optional, enabled by default in prod)
- Promotion support helpers
"""

from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.base import Base
from app.models.mixins import EnvironmentPromotionMixin

settings = get_settings()
logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class EnvironmentAwareRepository(Generic[ModelType]):
    """
    Base repository with environment awareness.

    All queries are automatically scoped to current environment
    and optionally exclude test data.

    Usage:
        class UserRepository(EnvironmentAwareRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, User)
    """

    def __init__(
        self,
        db: AsyncSession,
        model: type[ModelType],
        auto_exclude_test_data: bool = True,
    ):
        """
        Initialize environment-aware repository.

        Args:
            db: Database session
            model: SQLAlchemy model class
            auto_exclude_test_data: Automatically exclude test data in prod
        """
        self.db = db
        self.model = model
        self.auto_exclude_test_data = auto_exclude_test_data

        # Check if model has environment support
        if not hasattr(model, "environment"):
            logger.warning(
                "repository_without_environment_support",
                model=model.__name__,
                message="Model doesn't have EnvironmentPromotionMixin. "
                "Repository will not filter by environment.",
            )
            self._has_environment = False
        else:
            self._has_environment = True

    # ========================================================================
    # Query Building
    # ========================================================================

    def _build_base_query(
        self,
        include_test_data: bool = False,
        environment: Optional[str] = None,
    ) -> Select:
        """
        Build base query with environment and test data filters.

        Args:
            include_test_data: Include test data in results
            environment: Override environment (default: current)

        Returns:
            SQLAlchemy select statement with filters applied
        """
        query = select(self.model)

        # Apply environment filter
        if self._has_environment:
            env = environment or settings.environment
            query = query.where(self.model.environment == env)

        # Apply test data filter
        if (
            self._has_environment
            and hasattr(self.model, "is_test_data")
            and not include_test_data
        ):
            # In production, always exclude test data unless explicitly requested
            if settings.is_production or self.auto_exclude_test_data:
                query = query.where(self.model.is_test_data == False)  # noqa: E712

        return query

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def get_by_id(
        self,
        id: UUID,
        include_test_data: bool = False,
    ) -> Optional[ModelType]:
        """
        Get record by ID (scoped to current environment).

        Args:
            id: Record ID
            include_test_data: Include test data

        Returns:
            Model instance or None
        """
        query = self._build_base_query(include_test_data=include_test_data).where(
            self.model.id == id
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_test_data: bool = False,
    ) -> list[ModelType]:
        """
        Get all records (scoped to current environment).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            include_test_data: Include test data

        Returns:
            List of model instances
        """
        query = (
            self._build_base_query(include_test_data=include_test_data)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        obj_in: dict[str, Any],
        mark_as_test: bool = False,
    ) -> ModelType:
        """
        Create new record in current environment.

        Args:
            obj_in: Dictionary with model fields
            mark_as_test: Mark this record as test data

        Returns:
            Created model instance
        """
        # Ensure environment is set
        if self._has_environment and "environment" not in obj_in:
            obj_in["environment"] = settings.environment

        # Mark as test data if requested
        if mark_as_test and hasattr(self.model, "is_test_data"):
            obj_in["is_test_data"] = True
            obj_in["test_data_reason"] = "Manually marked during creation"

        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def update(
        self,
        id: UUID,
        obj_in: dict[str, Any],
    ) -> Optional[ModelType]:
        """
        Update record (scoped to current environment).

        Args:
            id: Record ID
            obj_in: Dictionary with fields to update

        Returns:
            Updated model instance or None
        """
        db_obj = await self.get_by_id(id, include_test_data=True)

        if not db_obj:
            return None

        # Update fields
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def delete(self, id: UUID) -> bool:
        """
        Delete record (scoped to current environment).

        Uses soft delete if model supports it.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = await self.get_by_id(id, include_test_data=True)

        if not db_obj:
            return False

        # Use soft delete if available
        if hasattr(db_obj, "soft_delete"):
            db_obj.soft_delete()
            await self.db.commit()
        else:
            # Hard delete
            await self.db.delete(db_obj)
            await self.db.commit()

        return True

    # ========================================================================
    # Environment Operations
    # ========================================================================

    async def get_promotable_items(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get items that can be promoted to next environment.

        Returns only approved, non-test items.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of promotable model instances
        """
        if not self._has_environment:
            return []

        query = (
            select(self.model)
            .where(
                self.model.environment == settings.environment,
                self.model.is_promotable == True,  # noqa: E712
                self.model.promotion_status == "approved",
                self.model.is_test_data == False,  # noqa: E712
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def approve_for_promotion(self, id: UUID) -> Optional[ModelType]:
        """
        Approve an item for promotion to next environment.

        Args:
            id: Record ID

        Returns:
            Updated model instance or None
        """
        db_obj = await self.get_by_id(id, include_test_data=True)

        if not db_obj:
            return None

        # Use mixin method if available
        if hasattr(db_obj, "approve_for_promotion"):
            try:
                db_obj.approve_for_promotion()
                await self.db.commit()
                await self.db.refresh(db_obj)
                return db_obj
            except ValueError as e:
                logger.warning(
                    "promotion_approval_failed",
                    id=str(id),
                    error=str(e),
                )
                return None

        return None

    async def mark_as_test_data(
        self,
        id: UUID,
        reason: str = "Manually marked",
    ) -> Optional[ModelType]:
        """
        Mark item as test data.

        Args:
            id: Record ID
            reason: Reason for marking as test data

        Returns:
            Updated model instance or None
        """
        db_obj = await self.get_by_id(id, include_test_data=True)

        if not db_obj:
            return None

        # Use mixin method if available
        if hasattr(db_obj, "mark_as_test_data"):
            db_obj.mark_as_test_data(reason)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        return None

    async def get_test_data_items(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get all test data items in current environment.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of test data model instances
        """
        if not self._has_environment:
            return []

        query = (
            select(self.model)
            .where(
                self.model.environment == settings.environment,
                self.model.is_test_data == True,  # noqa: E712
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Cross-Environment Operations
    # ========================================================================

    async def get_by_id_any_environment(
        self,
        id: UUID,
        environment: str,
    ) -> Optional[ModelType]:
        """
        Get record by ID from specific environment.

        Warning: Use with caution. Only for admin/debugging.

        Args:
            id: Record ID
            environment: Target environment

        Returns:
            Model instance or None
        """
        if not self._has_environment:
            return None

        query = select(self.model).where(
            self.model.id == id,
            self.model.environment == environment,
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_by_environment(self, environment: str) -> int:
        """
        Count records in specific environment.

        Args:
            environment: Target environment

        Returns:
            Count of records
        """
        if not self._has_environment:
            return 0

        from sqlalchemy import func

        query = select(func.count(self.model.id)).where(
            self.model.environment == environment
        )

        result = await self.db.execute(query)
        return result.scalar_one() or 0
