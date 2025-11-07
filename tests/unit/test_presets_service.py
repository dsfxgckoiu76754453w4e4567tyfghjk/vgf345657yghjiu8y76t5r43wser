"""Unit tests for presets service."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.presets_service import PresetsService
from app.models.subscription import ModelPreset, PlanLimit, Subscription


class TestCreatePreset:
    """Test preset creation."""

    @pytest.mark.asyncio
    async def test_create_basic_preset(self):
        """Test creating a basic preset."""
        service = PresetsService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock subscription check
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type="premium",
            status="active",
            billing_cycle="monthly",
            amount_usd=9.99,
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        # Mock plan limits
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium",
            presets_limit=10,
            max_messages_per_month=1000,
            max_tokens_per_month=1000000,
            max_images_per_month=100,
            max_documents_per_month=100,
            max_audio_minutes_per_month=100,
            monthly_price_usd=9.99,
            yearly_price_usd=99.99,
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        # Mock existing presets count (user has 2 presets)
        mock_presets_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(), MagicMock()]
        mock_presets_result.scalars.return_value = mock_scalars

        # Mock slug uniqueness check (slug doesn't exist)
        mock_slug_result = MagicMock()
        mock_slug_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [
            mock_sub_result,
            mock_plan_result,
            mock_presets_result,
            mock_slug_result,
        ]

        preset = await service.create_preset(
            user_id=user_id,
            db=mock_db,
            name="My Preset",
            slug="my-preset",
            model="anthropic/claude-3.5-sonnet",
            temperature=0.7,
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_preset_with_full_config(self):
        """Test creating preset with all configuration options."""
        service = PresetsService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock all required database calls
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(), user_id=user_id, plan_type="premium", status="active", billing_cycle="monthly", amount_usd=9.99
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium", presets_limit=10, max_messages_per_month=1000, max_tokens_per_month=1000000,
            max_images_per_month=100, max_documents_per_month=100, max_audio_minutes_per_month=100,
            monthly_price_usd=9.99, yearly_price_usd=99.99
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        mock_presets_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_presets_result.scalars.return_value = mock_scalars

        mock_slug_result = MagicMock()
        mock_slug_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [
            mock_sub_result,
            mock_plan_result,
            mock_presets_result,
            mock_slug_result,
        ]

        model_config = {"max_retries": 3, "timeout": 30}
        provider_preferences = {"prefer_anthropic": True}

        preset = await service.create_preset(
            user_id=user_id,
            db=mock_db,
            name="Advanced Preset",
            slug="advanced-preset",
            model="anthropic/claude-3.5-sonnet",
            description="Advanced configuration",
            system_prompt="You are a helpful assistant",
            temperature=0.7,
            top_p=0.9,
            max_tokens=2000,
            model_config=model_config,
            provider_preferences=provider_preferences,
            is_public=True,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_preset_exceeds_limit(self):
        """Test creating preset when user has reached limit."""
        service = PresetsService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock subscription
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(), user_id=user_id, plan_type="free", status="active", billing_cycle="monthly", amount_usd=0.0
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        # Mock plan with limit of 3
        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="free", presets_limit=3, max_messages_per_month=100, max_tokens_per_month=100000,
            max_images_per_month=10, max_documents_per_month=10, max_audio_minutes_per_month=10,
            monthly_price_usd=0.0, yearly_price_usd=0.0
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        # Mock user already has 3 presets
        mock_presets_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_presets_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [
            mock_sub_result,
            mock_plan_result,
            mock_presets_result,
        ]

        with pytest.raises(ValueError, match="Preset limit reached"):
            await service.create_preset(
                user_id=user_id,
                db=mock_db,
                name="Exceeds Limit",
                slug="exceeds-limit",
                model="anthropic/claude-3.5-sonnet",
            )

    @pytest.mark.asyncio
    async def test_create_preset_duplicate_slug(self):
        """Test creating preset with duplicate slug."""
        service = PresetsService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock successful limit check
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(), user_id=user_id, plan_type="premium", status="active", billing_cycle="monthly", amount_usd=9.99
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium", presets_limit=10, max_messages_per_month=1000, max_tokens_per_month=1000000,
            max_images_per_month=100, max_documents_per_month=100, max_audio_minutes_per_month=100,
            monthly_price_usd=9.99, yearly_price_usd=99.99
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        mock_presets_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_presets_result.scalars.return_value = mock_scalars

        # Mock slug already exists
        mock_slug_result = MagicMock()
        existing_preset = MagicMock()
        mock_slug_result.scalar_one_or_none.return_value = existing_preset

        mock_db.execute.side_effect = [
            mock_sub_result,
            mock_plan_result,
            mock_presets_result,
            mock_slug_result,
        ]

        with pytest.raises(ValueError, match="Preset with slug 'duplicate' already exists"):
            await service.create_preset(
                user_id=user_id,
                db=mock_db,
                name="Duplicate",
                slug="duplicate",
                model="anthropic/claude-3.5-sonnet",
            )


class TestPresetRetrieval:
    """Test preset retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_preset_by_id(self):
        """Test getting preset by ID."""
        service = PresetsService()
        user_id = uuid4()
        preset_id = uuid4()

        mock_db = AsyncMock()

        # Mock preset lookup
        mock_result = MagicMock()
        mock_preset = MagicMock()
        mock_preset.id = preset_id
        mock_preset.user_id = user_id
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        preset = await service.get_preset(preset_id=preset_id, user_id=user_id, db=mock_db)

        assert preset.id == preset_id

    @pytest.mark.asyncio
    async def test_list_user_presets(self):
        """Test listing user's presets."""
        service = PresetsService()
        user_id = uuid4()

        mock_db = AsyncMock()

        # Mock presets list
        mock_result = MagicMock()
        mock_presets = [MagicMock(), MagicMock(), MagicMock()]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_presets
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        presets = await service.list_user_presets(user_id=user_id, db=mock_db)

        assert len(presets) == 3


class TestPresetUpdate:
    """Test preset update operations."""

    @pytest.mark.asyncio
    async def test_update_preset(self):
        """Test updating a preset."""
        service = PresetsService()
        user_id = uuid4()
        preset_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing preset
        mock_result = MagicMock()
        mock_preset = MagicMock()
        mock_preset.id = preset_id
        mock_preset.user_id = user_id
        mock_preset.version = 1
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        preset = await service.update_preset(
            preset_id=preset_id,
            user_id=user_id,
            db=mock_db,
            name="Updated Name",
            temperature=0.8,
        )

        # Verify version was incremented
        assert mock_preset.version == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preset_not_found(self):
        """Test updating non-existent preset."""
        service = PresetsService()
        user_id = uuid4()
        preset_id = uuid4()

        mock_db = AsyncMock()

        # Mock preset not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Preset not found or access denied"):
            await service.update_preset(
                preset_id=preset_id, user_id=user_id, db=mock_db, name="Updated"
            )


class TestPresetDeletion:
    """Test preset deletion."""

    @pytest.mark.asyncio
    async def test_delete_preset(self):
        """Test deleting a preset."""
        service = PresetsService()
        user_id = uuid4()
        preset_id = uuid4()

        mock_db = AsyncMock()

        # Mock existing preset
        mock_result = MagicMock()
        mock_preset = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        result = await service.delete_preset(preset_id=preset_id, user_id=user_id, db=mock_db)

        assert result == True
        mock_db.delete.assert_called_once_with(mock_preset)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_preset_not_found(self):
        """Test deleting non-existent preset."""
        service = PresetsService()
        user_id = uuid4()
        preset_id = uuid4()

        mock_db = AsyncMock()

        # Mock preset not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.delete_preset(preset_id=preset_id, user_id=user_id, db=mock_db)

        assert result == False
        mock_db.delete.assert_not_called()


class TestPresetDuplication:
    """Test preset duplication."""

    @pytest.mark.asyncio
    async def test_duplicate_preset(self):
        """Test duplicating a preset."""
        service = PresetsService()
        user_id = uuid4()
        original_id = uuid4()

        mock_db = AsyncMock()

        # Mock original preset lookup
        mock_original_result = MagicMock()
        mock_original = MagicMock()
        mock_original.id = original_id
        mock_original.name = "Original"
        mock_original.model = "anthropic/claude-3.5-sonnet"
        mock_original.temperature = 0.7
        mock_original_result.scalar_one_or_none.return_value = mock_original

        # Mock subscription and plan for limit check
        mock_sub_result = MagicMock()
        mock_subscription = Subscription(
            id=uuid4(), user_id=user_id, plan_type="premium", status="active", billing_cycle="monthly", amount_usd=9.99
        )
        mock_sub_result.scalar_one_or_none.return_value = mock_subscription

        mock_plan_result = MagicMock()
        mock_plan = PlanLimit(
            plan_type="premium", presets_limit=10, max_messages_per_month=1000, max_tokens_per_month=1000000,
            max_images_per_month=100, max_documents_per_month=100, max_audio_minutes_per_month=100,
            monthly_price_usd=9.99, yearly_price_usd=99.99
        )
        mock_plan_result.scalar_one_or_none.return_value = mock_plan

        # Mock presets count
        mock_presets_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_presets_result.scalars.return_value = mock_scalars

        # Mock slug uniqueness check
        mock_slug_result = MagicMock()
        mock_slug_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [
            mock_original_result,
            mock_sub_result,
            mock_plan_result,
            mock_presets_result,
            mock_slug_result,
        ]

        duplicate = await service.duplicate_preset(
            preset_id=original_id,
            user_id=user_id,
            db=mock_db,
            new_name="Duplicate",
            new_slug="duplicate",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestValidation:
    """Test validation methods."""

    def test_validate_temperature_valid(self):
        """Test temperature validation with valid value."""
        service = PresetsService()
        # Should not raise
        service._validate_preset_config(temperature=0.7)

    def test_validate_temperature_invalid(self):
        """Test temperature validation with invalid value."""
        service = PresetsService()
        with pytest.raises(ValueError, match="Temperature must be between"):
            service._validate_preset_config(temperature=2.5)

    def test_validate_top_p_valid(self):
        """Test top_p validation with valid value."""
        service = PresetsService()
        # Should not raise
        service._validate_preset_config(top_p=0.9)

    def test_validate_top_p_invalid(self):
        """Test top_p validation with invalid value."""
        service = PresetsService()
        with pytest.raises(ValueError, match="Top_p must be between"):
            service._validate_preset_config(top_p=1.5)

    def test_validate_max_tokens_valid(self):
        """Test max_tokens validation with valid value."""
        service = PresetsService()
        # Should not raise
        service._validate_preset_config(max_tokens=2000)

    def test_validate_max_tokens_invalid(self):
        """Test max_tokens validation with invalid value."""
        service = PresetsService()
        with pytest.raises(ValueError, match="Max_tokens must be positive"):
            service._validate_preset_config(max_tokens=-100)


class TestConfigParsing:
    """Test configuration parsing."""

    def test_parse_preset_config(self):
        """Test parsing preset configuration."""
        service = PresetsService()

        mock_preset = MagicMock()
        mock_preset.model = "anthropic/claude-3.5-sonnet"
        mock_preset.temperature = 0.7
        mock_preset.top_p = 0.9
        mock_preset.max_tokens = 2000
        mock_preset.model_config = json.dumps({"max_retries": 3})
        mock_preset.provider_preferences = json.dumps({"prefer_anthropic": True})

        config = service.parse_preset_config(mock_preset)

        assert config["model"] == "anthropic/claude-3.5-sonnet"
        assert config["temperature"] == 0.7
        assert config["model_config"]["max_retries"] == 3
        assert config["provider_preferences"]["prefer_anthropic"] == True

    def test_parse_preset_config_invalid_json(self):
        """Test parsing preset with invalid JSON."""
        service = PresetsService()

        mock_preset = MagicMock()
        mock_preset.id = uuid4()
        mock_preset.model = "anthropic/claude-3.5-sonnet"
        mock_preset.temperature = None
        mock_preset.top_p = None
        mock_preset.max_tokens = None
        mock_preset.model_config = "invalid json"
        mock_preset.provider_preferences = None

        config = service.parse_preset_config(mock_preset)

        # Should return empty dict for invalid JSON
        assert config["model_config"] == {}
        assert "provider_preferences" not in config
