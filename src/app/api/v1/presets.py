"""Model presets API endpoints."""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.services.presets_service import presets_service

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class PresetCreateRequest(BaseModel):
    """Preset creation request."""

    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    model: str = Field(..., min_length=1, max_length=100, description="Model identifier")
    description: str | None = Field(None, max_length=500, description="Optional description")
    system_prompt: str | None = Field(None, description="Optional system prompt template")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top P (0.0-1.0)")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens")
    extra_model_config: dict[str, Any] | None = Field(None, description="Additional model configuration")
    provider_preferences: dict[str, Any] | None = Field(None, description="Provider routing preferences")
    is_public: bool = Field(False, description="Make preset publicly shareable")


class PresetUpdateRequest(BaseModel):
    """Preset update request."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    model: str | None = Field(None, min_length=1, max_length=100)
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(None, gt=0)
    extra_model_config: dict[str, Any] | None = None
    provider_preferences: dict[str, Any] | None = None
    is_public: bool | None = None


class PresetResponse(BaseModel):
    """Preset response."""

    id: UUID
    user_id: UUID | None
    name: str
    slug: str
    description: str | None
    model: str
    system_prompt: str | None
    temperature: float | None
    top_p: float | None
    max_tokens: int | None
    extra_model_config: str | None
    provider_preferences: str | None
    is_public: bool
    version: int
    created_at: str
    updated_at: str


class PresetListResponse(BaseModel):
    """List of presets."""

    presets: List[PresetResponse]
    total: int


class PresetDuplicateRequest(BaseModel):
    """Preset duplication request."""

    new_name: str = Field(..., min_length=1, max_length=100, description="Name for duplicated preset")
    new_slug: str = Field(..., min_length=1, max_length=100, description="Slug for duplicated preset")


@router.post("/", response_model=PresetResponse, status_code=status.HTTP_201_CREATED)
async def create_preset(
    request_data: PresetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """
    Create a new model preset.

    - **name**: Preset name
    - **slug**: URL-friendly identifier (unique per user)
    - **model**: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
    - **description**: Optional description
    - **system_prompt**: Optional system prompt template
    - **temperature**: Optional temperature (0.0-2.0)
    - **top_p**: Optional top_p (0.0-1.0)
    - **max_tokens**: Optional max tokens
    - **model_config**: Additional model configuration
    - **provider_preferences**: Provider routing preferences
    - **is_public**: Make preset publicly shareable

    Requires active subscription with presets enabled.
    Returns created preset.
    """
    try:
        preset = await presets_service.create_preset(
            user_id=current_user.id,
            db=db,
            name=request_data.name,
            slug=request_data.slug,
            model=request_data.model,
            description=request_data.description,
            system_prompt=request_data.system_prompt,
            temperature=request_data.temperature,
            top_p=request_data.top_p,
            max_tokens=request_data.max_tokens,
            model_config=request_data.extra_model_config,
            provider_preferences=request_data.provider_preferences,
            is_public=request_data.is_public,
        )

        logger.info(
            "preset_created_via_api",
            user_id=str(current_user.id),
            preset_id=str(preset.id),
            slug=preset.slug,
        )

        return PresetResponse(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            slug=preset.slug,
            description=preset.description,
            model=preset.model,
            system_prompt=preset.system_prompt,
            temperature=float(preset.temperature) if preset.temperature else None,
            top_p=float(preset.top_p) if preset.top_p else None,
            max_tokens=preset.max_tokens,
            model_config=preset.extra_model_config,
            provider_preferences=preset.provider_preferences,
            is_public=preset.is_public or False,
            version=preset.version or 1,
            created_at=preset.created_at.isoformat(),
            updated_at=preset.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.warning("preset_creation_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("preset_creation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preset",
        )


@router.get("/", response_model=PresetListResponse)
async def list_presets(
    include_public: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetListResponse:
    """
    List user's presets.

    - **include_public**: Include public presets from other users

    Returns list of presets.
    """
    try:
        presets = await presets_service.list_user_presets(
            user_id=current_user.id,
            db=db,
            include_public=include_public,
        )

        return PresetListResponse(
            presets=[
                PresetResponse(
                    id=preset.id,
                    user_id=preset.user_id,
                    name=preset.name,
                    slug=preset.slug,
                    description=preset.description,
                    model=preset.model,
                    system_prompt=preset.system_prompt,
                    temperature=float(preset.temperature) if preset.temperature else None,
                    top_p=float(preset.top_p) if preset.top_p else None,
                    max_tokens=preset.max_tokens,
                    model_config=preset.extra_model_config,
                    provider_preferences=preset.provider_preferences,
                    is_public=preset.is_public or False,
                    version=preset.version or 1,
                    created_at=preset.created_at.isoformat(),
                    updated_at=preset.updated_at.isoformat(),
                )
                for preset in presets
            ],
            total=len(presets),
        )

    except Exception as e:
        logger.error("list_presets_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve presets",
        )


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """
    Get a specific preset by ID.

    - **preset_id**: UUID of the preset

    Returns preset details.
    """
    try:
        preset = await presets_service.get_preset(
            preset_id=preset_id,
            user_id=current_user.id,
            db=db,
        )

        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found",
            )

        return PresetResponse(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            slug=preset.slug,
            description=preset.description,
            model=preset.model,
            system_prompt=preset.system_prompt,
            temperature=float(preset.temperature) if preset.temperature else None,
            top_p=float(preset.top_p) if preset.top_p else None,
            max_tokens=preset.max_tokens,
            model_config=preset.extra_model_config,
            provider_preferences=preset.provider_preferences,
            is_public=preset.is_public or False,
            version=preset.version or 1,
            created_at=preset.created_at.isoformat(),
            updated_at=preset.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_preset_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preset",
        )


@router.get("/slug/{slug}", response_model=PresetResponse)
async def get_preset_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """
    Get a preset by slug.

    - **slug**: Slug of the preset

    Returns preset details.
    """
    try:
        preset = await presets_service.get_preset_by_slug(
            slug=slug,
            user_id=current_user.id,
            db=db,
        )

        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found",
            )

        return PresetResponse(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            slug=preset.slug,
            description=preset.description,
            model=preset.model,
            system_prompt=preset.system_prompt,
            temperature=float(preset.temperature) if preset.temperature else None,
            top_p=float(preset.top_p) if preset.top_p else None,
            max_tokens=preset.max_tokens,
            model_config=preset.extra_model_config,
            provider_preferences=preset.provider_preferences,
            is_public=preset.is_public or False,
            version=preset.version or 1,
            created_at=preset.created_at.isoformat(),
            updated_at=preset.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_preset_by_slug_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preset",
        )


@router.patch("/{preset_id}", response_model=PresetResponse)
async def update_preset(
    preset_id: UUID,
    request_data: PresetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """
    Update a preset (only owner can update).

    - **preset_id**: UUID of the preset to update
    - Fields to update (all optional)

    Returns updated preset with incremented version.
    """
    try:
        # Build updates dict from request
        updates = {k: v for k, v in request_data.model_dump().items() if v is not None}

        preset = await presets_service.update_preset(
            preset_id=preset_id,
            user_id=current_user.id,
            db=db,
            **updates,
        )

        logger.info(
            "preset_updated_via_api",
            user_id=str(current_user.id),
            preset_id=str(preset_id),
            version=preset.version,
        )

        return PresetResponse(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            slug=preset.slug,
            description=preset.description,
            model=preset.model,
            system_prompt=preset.system_prompt,
            temperature=float(preset.temperature) if preset.temperature else None,
            top_p=float(preset.top_p) if preset.top_p else None,
            max_tokens=preset.max_tokens,
            model_config=preset.extra_model_config,
            provider_preferences=preset.provider_preferences,
            is_public=preset.is_public or False,
            version=preset.version or 1,
            created_at=preset.created_at.isoformat(),
            updated_at=preset.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.warning("preset_update_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("preset_update_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preset",
        )


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a preset (only owner can delete).

    - **preset_id**: UUID of the preset to delete
    """
    try:
        deleted = await presets_service.delete_preset(
            preset_id=preset_id,
            user_id=current_user.id,
            db=db,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found",
            )

        logger.info("preset_deleted_via_api", user_id=str(current_user.id), preset_id=str(preset_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_preset_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete preset",
        )


@router.post("/{preset_id}/duplicate", response_model=PresetResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_preset(
    preset_id: UUID,
    request_data: PresetDuplicateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """
    Duplicate a preset (user's own or public).

    - **preset_id**: UUID of the preset to duplicate
    - **new_name**: Name for the duplicated preset
    - **new_slug**: Slug for the duplicated preset

    Returns the new duplicated preset.
    """
    try:
        preset = await presets_service.duplicate_preset(
            preset_id=preset_id,
            user_id=current_user.id,
            db=db,
            new_name=request_data.new_name,
            new_slug=request_data.new_slug,
        )

        logger.info(
            "preset_duplicated_via_api",
            user_id=str(current_user.id),
            original_id=str(preset_id),
            new_id=str(preset.id),
        )

        return PresetResponse(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            slug=preset.slug,
            description=preset.description,
            model=preset.model,
            system_prompt=preset.system_prompt,
            temperature=float(preset.temperature) if preset.temperature else None,
            top_p=float(preset.top_p) if preset.top_p else None,
            max_tokens=preset.max_tokens,
            model_config=preset.extra_model_config,
            provider_preferences=preset.provider_preferences,
            is_public=preset.is_public or False,
            version=preset.version or 1,
            created_at=preset.created_at.isoformat(),
            updated_at=preset.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.warning("preset_duplication_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("preset_duplication_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate preset",
        )
