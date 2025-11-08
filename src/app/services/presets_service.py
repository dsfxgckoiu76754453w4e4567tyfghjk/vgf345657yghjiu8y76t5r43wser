"""Model presets management service."""

import json
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import ModelPreset, PlanLimit, Subscription

logger = get_logger(__name__)


class PresetsService:
    """
    Service for managing model presets.

    Features:
    - User-defined model configurations
    - System prompt templates
    - Provider preferences
    - Public/private presets
    - Versioning support
    - Plan-based limits
    """

    async def create_preset(
        self,
        user_id: UUID,
        db: AsyncSession,
        name: str,
        slug: str,
        model: str,
        description: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        model_config: dict[str, Any] | None = None,
        provider_preferences: dict[str, Any] | None = None,
        is_public: bool = False,
    ) -> ModelPreset:
        """
        Create a new model preset.

        Args:
            user_id: User ID
            db: Database session
            name: Preset name
            slug: URL-friendly identifier
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            description: Optional description
            system_prompt: Optional system prompt template
            temperature: Optional temperature (0.0-1.0)
            top_p: Optional top_p (0.0-1.0)
            max_tokens: Optional max tokens
            model_config: Additional model configuration (JSONB)
            provider_preferences: Provider routing preferences (JSONB)
            is_public: Whether preset is publicly shareable

        Returns:
            Created ModelPreset

        Raises:
            ValueError: If user has exceeded preset limit or slug exists
        """
        # Check user's plan and preset limit
        await self._check_preset_limit(user_id, db)

        # Check if slug already exists for this user
        existing = await db.execute(
            select(ModelPreset).where(
                ModelPreset.user_id == user_id, ModelPreset.slug == slug
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Preset with slug '{slug}' already exists")

        # Validate model configuration
        self._validate_preset_config(
            temperature=temperature, top_p=top_p, max_tokens=max_tokens
        )

        # Create preset
        preset = ModelPreset(
            user_id=user_id,
            name=name,
            slug=slug,
            model=model,
            description=description,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            model_config=json.dumps(model_config) if model_config else None,
            provider_preferences=json.dumps(provider_preferences)
            if provider_preferences
            else None,
            is_public=is_public,
            version=1,
        )

        db.add(preset)
        await db.commit()
        await db.refresh(preset)

        logger.info("preset_created", user_id=str(user_id), slug=slug, model=model)

        return preset

    async def get_preset(
        self, preset_id: UUID, user_id: UUID, db: AsyncSession
    ) -> ModelPreset | None:
        """Get a preset by ID (must belong to user or be public)."""
        result = await db.execute(
            select(ModelPreset).where(
                ModelPreset.id == preset_id,
                (ModelPreset.user_id == user_id) | (ModelPreset.is_public == True),
            )
        )
        return result.scalar_one_or_none()

    async def get_preset_by_slug(
        self, slug: str, user_id: UUID, db: AsyncSession
    ) -> ModelPreset | None:
        """Get a preset by slug (must belong to user or be public)."""
        result = await db.execute(
            select(ModelPreset).where(
                ModelPreset.slug == slug,
                (ModelPreset.user_id == user_id) | (ModelPreset.is_public == True),
            )
        )
        return result.scalar_one_or_none()

    async def list_user_presets(
        self, user_id: UUID, db: AsyncSession, include_public: bool = False
    ) -> list[ModelPreset]:
        """List user's presets, optionally including public presets."""
        if include_public:
            result = await db.execute(
                select(ModelPreset)
                .where(
                    (ModelPreset.user_id == user_id) | (ModelPreset.is_public == True)
                )
                .order_by(ModelPreset.created_at.desc())
            )
        else:
            result = await db.execute(
                select(ModelPreset)
                .where(ModelPreset.user_id == user_id)
                .order_by(ModelPreset.created_at.desc())
            )

        return list(result.scalars().all())

    async def update_preset(
        self,
        preset_id: UUID,
        user_id: UUID,
        db: AsyncSession,
        **updates: Any,
    ) -> ModelPreset:
        """
        Update a preset (only owner can update).

        Args:
            preset_id: Preset ID
            user_id: User ID (must be owner)
            db: Database session
            **updates: Fields to update

        Returns:
            Updated ModelPreset

        Raises:
            ValueError: If preset not found or user is not owner
        """
        result = await db.execute(
            select(ModelPreset).where(
                ModelPreset.id == preset_id, ModelPreset.user_id == user_id
            )
        )
        preset = result.scalar_one_or_none()

        if not preset:
            raise ValueError("Preset not found or access denied")

        # Validate updates
        if "temperature" in updates or "top_p" in updates or "max_tokens" in updates:
            self._validate_preset_config(
                temperature=updates.get("temperature"),
                top_p=updates.get("top_p"),
                max_tokens=updates.get("max_tokens"),
            )

        # Update fields
        for key, value in updates.items():
            if key in [
                "name",
                "description",
                "model",
                "system_prompt",
                "temperature",
                "top_p",
                "max_tokens",
                "is_public",
            ]:
                setattr(preset, key, value)
            elif key == "model_config" and value is not None:
                preset.model_config = json.dumps(value)
            elif key == "provider_preferences" and value is not None:
                preset.provider_preferences = json.dumps(value)

        # Increment version
        preset.version += 1

        await db.commit()
        await db.refresh(preset)

        logger.info(
            "preset_updated",
            user_id=str(user_id),
            preset_id=str(preset_id),
            version=preset.version,
        )

        return preset

    async def delete_preset(
        self, preset_id: UUID, user_id: UUID, db: AsyncSession
    ) -> bool:
        """Delete a preset (only owner can delete)."""
        result = await db.execute(
            select(ModelPreset).where(
                ModelPreset.id == preset_id, ModelPreset.user_id == user_id
            )
        )
        preset = result.scalar_one_or_none()

        if preset:
            await db.delete(preset)
            await db.commit()
            logger.info("preset_deleted", user_id=str(user_id), preset_id=str(preset_id))
            return True

        return False

    async def duplicate_preset(
        self,
        preset_id: UUID,
        user_id: UUID,
        db: AsyncSession,
        new_name: str,
        new_slug: str,
    ) -> ModelPreset:
        """Duplicate an existing preset (user's own or public)."""
        # Get original preset
        result = await db.execute(
            select(ModelPreset).where(
                ModelPreset.id == preset_id,
                (ModelPreset.user_id == user_id) | (ModelPreset.is_public == True),
            )
        )
        original = result.scalar_one_or_none()

        if not original:
            raise ValueError("Preset not found or access denied")

        # Check preset limit
        await self._check_preset_limit(user_id, db)

        # Check slug availability
        existing = await db.execute(
            select(ModelPreset).where(
                ModelPreset.user_id == user_id, ModelPreset.slug == new_slug
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Preset with slug '{new_slug}' already exists")

        # Create duplicate
        duplicate = ModelPreset(
            user_id=user_id,
            name=new_name,
            slug=new_slug,
            description=original.description,
            model=original.model,
            system_prompt=original.system_prompt,
            temperature=original.temperature,
            top_p=original.top_p,
            max_tokens=original.max_tokens,
            model_config=original.model_config,
            provider_preferences=original.provider_preferences,
            is_public=False,  # Duplicates are private by default
            version=1,
        )

        db.add(duplicate)
        await db.commit()
        await db.refresh(duplicate)

        logger.info(
            "preset_duplicated",
            user_id=str(user_id),
            original_id=str(preset_id),
            new_id=str(duplicate.id),
        )

        return duplicate

    async def _check_preset_limit(self, user_id: UUID, db: AsyncSession) -> None:
        """Check if user has reached preset limit."""
        # Get user's subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("No active subscription found")

        # Get plan limits
        result = await db.execute(
            select(PlanLimit).where(PlanLimit.plan_type == subscription.plan_type)
        )
        plan_limit = result.scalar_one_or_none()

        if not plan_limit:
            raise ValueError(f"Plan limits not found for {subscription.plan_type}")

        # Count user's presets
        result = await db.execute(
            select(ModelPreset).where(ModelPreset.user_id == user_id)
        )
        preset_count = len(list(result.scalars().all()))

        if preset_count >= plan_limit.presets_limit:
            raise ValueError(
                f"Preset limit reached ({plan_limit.presets_limit}) for {subscription.plan_type} plan"
            )

    def _validate_preset_config(
        self,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        """Validate preset configuration parameters."""
        if temperature is not None and not 0.0 <= temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        if top_p is not None and not 0.0 <= top_p <= 1.0:
            raise ValueError("Top_p must be between 0.0 and 1.0")

        if max_tokens is not None and max_tokens < 1:
            raise ValueError("Max_tokens must be positive")

    def parse_preset_config(self, preset: ModelPreset) -> dict[str, Any]:
        """Parse preset configuration into a usable format."""
        config = {
            "model": preset.model,
            "temperature": preset.temperature,
            "top_p": preset.top_p,
            "max_tokens": preset.max_tokens,
        }

        # Parse JSON fields
        if preset.model_config:
            try:
                config["model_config"] = json.loads(preset.model_config)
            except json.JSONDecodeError:
                logger.warning(
                    "invalid_model_config", preset_id=str(preset.id)
                )
                config["model_config"] = {}

        if preset.provider_preferences:
            try:
                config["provider_preferences"] = json.loads(preset.provider_preferences)
            except json.JSONDecodeError:
                logger.warning(
                    "invalid_provider_preferences", preset_id=str(preset.id)
                )
                config["provider_preferences"] = {}

        # Remove None values
        return {k: v for k, v in config.items() if v is not None}


# Global service instance
presets_service = PresetsService()
