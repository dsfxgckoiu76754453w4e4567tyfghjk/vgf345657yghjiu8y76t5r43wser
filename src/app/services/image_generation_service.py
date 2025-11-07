"""Image generation service using OpenRouter."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

import httpx
from app.core.config import settings
from app.core.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import GeneratedImage, MonthlyUsageQuota, PlanLimit

logger = get_logger(__name__)


class ImageGenerationService:
    """
    Service for generating images via OpenRouter.

    Features:
    - Multi-model support (Gemini, DALL-E, Flux, etc.)
    - Aspect ratio configuration
    - Base64 and URL storage
    - Cost tracking and quota checking
    - Plan-based access control
    """

    def __init__(self):
        """Initialize image generation service."""
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.app_url = settings.openrouter_app_url
        self.app_name = settings.openrouter_app_name

        logger.info("image_generation_service_initialized")

    async def generate_image(
        self,
        prompt: str,
        user_id: UUID,
        db: AsyncSession,
        conversation_id: UUID | None = None,
        model: str | None = None,
        aspect_ratio: str = "1:1",
        output_format: Literal["url", "base64"] = "url",
    ) -> dict[str, Any]:
        """
        Generate an image using OpenRouter.

        Args:
            prompt: Image generation prompt
            user_id: User ID
            db: Database session
            conversation_id: Optional conversation ID
            model: Model to use (default from settings)
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, etc.)
            output_format: Return URL or base64 encoded image

        Returns:
            Generated image data with URL/base64, cost, metadata

        Raises:
            ValueError: If user has exceeded quota or plan doesn't allow image generation
        """
        # Check if image generation is enabled
        if not settings.image_generation_enabled:
            raise ValueError("Image generation is not enabled")

        # Check user's plan and quota
        await self._check_user_quota(user_id, db)

        # Select model
        selected_model = model or settings.image_generation_models[0]

        # Build payload
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "user": str(user_id),
        }

        # Add aspect ratio if supported
        if aspect_ratio != "1:1":
            payload["aspect_ratio"] = aspect_ratio

        # Add output format preference
        if output_format == "base64":
            payload["response_format"] = "b64_json"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=120.0,
                )
                response.raise_for_status()
                data = response.json()

            # Parse response
            result = self._parse_response(data, output_format)

            # Calculate cost
            cost_usd = self._estimate_cost(selected_model)

            # Save to database
            generated_image = GeneratedImage(
                user_id=user_id,
                conversation_id=conversation_id,
                prompt=prompt,
                model_used=selected_model,
                image_data_url=result.get("b64_json") if output_format == "base64" else None,
                image_url=result.get("url") if output_format == "url" else None,
                aspect_ratio=aspect_ratio,
                generation_cost_usd=cost_usd,
            )
            db.add(generated_image)

            # Update quota
            await self._update_usage_quota(user_id, db, cost_usd)

            await db.commit()
            await db.refresh(generated_image)

            logger.info(
                "image_generated",
                user_id=str(user_id),
                model=selected_model,
                cost_usd=cost_usd,
            )

            return {
                "id": generated_image.id,
                "url": generated_image.image_url,
                "b64_json": generated_image.image_data_url,
                "model": selected_model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "cost_usd": cost_usd,
                "created_at": generated_image.created_at,
            }

        except httpx.HTTPStatusError as e:
            error_data = self._parse_error(e)
            logger.error(
                "image_generation_failed",
                status_code=e.response.status_code,
                error=error_data,
            )
            raise

        except Exception as e:
            logger.error("image_generation_error", error=str(e))
            raise

    async def _check_user_quota(self, user_id: UUID, db: AsyncSession) -> None:
        """Check if user has quota for image generation."""
        # Get user's plan
        from app.models.subscription import Subscription

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

        # Check if plan allows image generation
        if not plan_limit.image_generation_enabled:
            raise ValueError(
                f"Image generation not available on {subscription.plan_type} plan"
            )

        # Get current month usage
        month_year = datetime.utcnow().strftime("%Y-%m")
        result = await db.execute(
            select(MonthlyUsageQuota).where(
                MonthlyUsageQuota.user_id == user_id,
                MonthlyUsageQuota.month_year == month_year,
            )
        )
        quota = result.scalar_one_or_none()

        if quota:
            if quota.images_generated >= plan_limit.max_images_per_month:
                raise ValueError(
                    f"Monthly image generation limit reached ({plan_limit.max_images_per_month})"
                )

    async def _update_usage_quota(
        self, user_id: UUID, db: AsyncSession, cost_usd: float
    ) -> None:
        """Update user's monthly usage quota."""
        month_year = datetime.utcnow().strftime("%Y-%m")

        result = await db.execute(
            select(MonthlyUsageQuota).where(
                MonthlyUsageQuota.user_id == user_id,
                MonthlyUsageQuota.month_year == month_year,
            )
        )
        quota = result.scalar_one_or_none()

        if quota:
            quota.images_generated += 1
            quota.total_cost_usd += cost_usd
        else:
            quota = MonthlyUsageQuota(
                user_id=user_id,
                month_year=month_year,
                images_generated=1,
                total_cost_usd=cost_usd,
            )
            db.add(quota)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

    def _parse_response(self, data: dict[str, Any], output_format: str) -> dict[str, Any]:
        """Parse OpenRouter image generation response."""
        if "data" in data and len(data["data"]) > 0:
            image_data = data["data"][0]

            if output_format == "url":
                return {"url": image_data.get("url")}
            else:
                return {"b64_json": image_data.get("b64_json")}

        raise ValueError("No image data in response")

    def _parse_error(self, error: httpx.HTTPStatusError) -> dict[str, Any]:
        """Parse OpenRouter error."""
        try:
            error_data = error.response.json()
            error_info = error_data.get("error", {})

            return {
                "code": error_info.get("code", error.response.status_code),
                "message": error_info.get("message", str(error)),
                "status_code": error.response.status_code,
            }
        except Exception:
            return {
                "code": error.response.status_code,
                "message": str(error),
                "status_code": error.response.status_code,
            }

    def _estimate_cost(self, model: str) -> float:
        """
        Estimate image generation cost.

        Based on OpenRouter pricing:
        - Gemini Flash Image: ~$0.0004 per image
        - DALL-E 3: ~$0.04-0.08 per image
        - Flux: ~$0.005-0.01 per image
        """
        model_lower = model.lower()

        # Gemini models
        if "gemini" in model_lower and "flash" in model_lower:
            return 0.0004

        # DALL-E models
        if "dall-e" in model_lower:
            if "1024x1024" in model_lower or "standard" in model_lower:
                return 0.04
            return 0.08  # HD quality

        # Flux models
        if "flux" in model_lower:
            if "schnell" in model_lower:
                return 0.003
            return 0.01  # Pro

        # Default estimate
        return 0.01

    async def get_user_images(
        self,
        user_id: UUID,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GeneratedImage]:
        """Get user's generated images."""
        result = await db.execute(
            select(GeneratedImage)
            .where(GeneratedImage.user_id == user_id)
            .order_by(GeneratedImage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_image(
        self, image_id: UUID, user_id: UUID, db: AsyncSession
    ) -> GeneratedImage | None:
        """Get a specific generated image."""
        result = await db.execute(
            select(GeneratedImage).where(
                GeneratedImage.id == image_id, GeneratedImage.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_image(
        self, image_id: UUID, user_id: UUID, db: AsyncSession
    ) -> bool:
        """Delete a generated image."""
        result = await db.execute(
            select(GeneratedImage).where(
                GeneratedImage.id == image_id, GeneratedImage.user_id == user_id
            )
        )
        image = result.scalar_one_or_none()

        if image:
            await db.delete(image)
            await db.commit()
            logger.info("image_deleted", image_id=str(image_id), user_id=str(user_id))
            return True

        return False


# Global service instance
image_generation_service = ImageGenerationService()
