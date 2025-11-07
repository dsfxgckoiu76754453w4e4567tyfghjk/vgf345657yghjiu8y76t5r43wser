"""Image generation API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.services.image_generation_service import image_generation_service

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class ImageGenerationRequest(BaseModel):
    """Image generation request."""

    prompt: str = Field(..., min_length=1, max_length=2000, description="Image generation prompt")
    conversation_id: UUID | None = Field(None, description="Optional conversation ID")
    model: str | None = Field(None, description="Model to use (default from settings)")
    aspect_ratio: str = Field("1:1", description="Image aspect ratio (1:1, 16:9, 9:16, etc.)")
    output_format: str = Field("url", description="Output format (url or base64)")


class ImageResponse(BaseModel):
    """Image generation response."""

    id: UUID
    url: str | None = None
    b64_json: str | None = None
    model: str
    prompt: str
    aspect_ratio: str
    cost_usd: float
    created_at: str


class ImageListResponse(BaseModel):
    """List of generated images."""

    images: List[ImageResponse]
    total: int


@router.post("/generate", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def generate_image(
    request_data: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageResponse:
    """
    Generate an image using OpenRouter.

    - **prompt**: Description of the image to generate
    - **conversation_id**: Optional conversation ID to associate with
    - **model**: Optional model override (default uses config setting)
    - **aspect_ratio**: Image aspect ratio (1:1, 16:9, 9:16, etc.)
    - **output_format**: Return URL or base64 encoded image

    Requires active subscription with image generation enabled.
    Returns generated image URL/data and metadata.
    """
    try:
        result = await image_generation_service.generate_image(
            prompt=request_data.prompt,
            user_id=current_user.id,
            db=db,
            conversation_id=request_data.conversation_id,
            model=request_data.model,
            aspect_ratio=request_data.aspect_ratio,
            output_format=request_data.output_format,  # type: ignore
        )

        logger.info(
            "image_generated_via_api",
            user_id=str(current_user.id),
            image_id=str(result["id"]),
            model=result["model"],
        )

        return ImageResponse(
            id=result["id"],
            url=result.get("url"),
            b64_json=result.get("b64_json"),
            model=result["model"],
            prompt=result["prompt"],
            aspect_ratio=result["aspect_ratio"],
            cost_usd=result["cost_usd"],
            created_at=result["created_at"].isoformat(),
        )

    except ValueError as e:
        logger.warning("image_generation_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("image_generation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate image",
        )


@router.get("/history", response_model=ImageListResponse)
async def get_image_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageListResponse:
    """
    Get user's image generation history.

    - **limit**: Maximum number of images to return (default: 50)
    - **offset**: Number of images to skip (default: 0)

    Returns list of generated images with metadata.
    """
    try:
        images = await image_generation_service.get_user_images(
            user_id=current_user.id,
            db=db,
            limit=limit,
            offset=offset,
        )

        return ImageListResponse(
            images=[
                ImageResponse(
                    id=img.id,
                    url=img.image_url,
                    b64_json=img.image_data_url,
                    model=img.model_used,
                    prompt=img.prompt,
                    aspect_ratio=img.aspect_ratio or "1:1",
                    cost_usd=float(img.generation_cost_usd),
                    created_at=img.created_at.isoformat(),
                )
                for img in images
            ],
            total=len(images),
        )

    except Exception as e:
        logger.error("image_history_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image history",
        )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageResponse:
    """
    Get a specific generated image by ID.

    - **image_id**: UUID of the generated image

    Returns image metadata and URL/data.
    """
    try:
        image = await image_generation_service.get_image(
            image_id=image_id,
            user_id=current_user.id,
            db=db,
        )

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )

        return ImageResponse(
            id=image.id,
            url=image.image_url,
            b64_json=image.image_data_url,
            model=image.model_used,
            prompt=image.prompt,
            aspect_ratio=image.aspect_ratio or "1:1",
            cost_usd=float(image.generation_cost_usd),
            created_at=image.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_image_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image",
        )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a generated image.

    - **image_id**: UUID of the image to delete

    Only the owner can delete an image.
    """
    try:
        deleted = await image_generation_service.delete_image(
            image_id=image_id,
            user_id=current_user.id,
            db=db,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )

        logger.info("image_deleted", user_id=str(current_user.id), image_id=str(image_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_image_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image",
        )
