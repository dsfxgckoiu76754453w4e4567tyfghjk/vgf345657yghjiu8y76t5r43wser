"""Seed initial plan limits data."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import async_session_maker
from app.models.subscription import PlanLimit

logger = get_logger(__name__)


async def seed_plan_limits():
    """Seed initial plan limits data."""

    # Define plan limits
    plans = [
        {
            "plan_type": "free",
            "max_messages_per_month": 100,
            "max_tokens_per_month": 100_000,
            "max_images_per_month": 5,
            "max_documents_per_month": 10,
            "max_audio_minutes_per_month": 5,
            "web_search_enabled": True,
            "image_generation_enabled": False,
            "pdf_processing_enabled": False,
            "audio_processing_enabled": False,
            "prompt_caching_enabled": False,
            "advanced_models_enabled": False,
            "presets_limit": 3,
            "max_context_length": 4096,
            "priority_support": False,
            "monthly_price_usd": 0.00,
            "yearly_price_usd": 0.00,
        },
        {
            "plan_type": "premium",
            "max_messages_per_month": 2_000,
            "max_tokens_per_month": 5_000_000,
            "max_images_per_month": 100,
            "max_documents_per_month": 500,
            "max_audio_minutes_per_month": 100,
            "web_search_enabled": True,
            "image_generation_enabled": True,
            "pdf_processing_enabled": True,
            "audio_processing_enabled": True,
            "prompt_caching_enabled": True,
            "advanced_models_enabled": True,
            "presets_limit": 20,
            "max_context_length": 200_000,
            "priority_support": False,
            "monthly_price_usd": 19.99,
            "yearly_price_usd": 199.99,
        },
        {
            "plan_type": "unlimited",
            "max_messages_per_month": 10_000,
            "max_tokens_per_month": 50_000_000,
            "max_images_per_month": 1_000,
            "max_documents_per_month": 5_000,
            "max_audio_minutes_per_month": 1_000,
            "web_search_enabled": True,
            "image_generation_enabled": True,
            "pdf_processing_enabled": True,
            "audio_processing_enabled": True,
            "prompt_caching_enabled": True,
            "advanced_models_enabled": True,
            "presets_limit": 100,
            "max_context_length": 1_000_000,
            "priority_support": True,
            "monthly_price_usd": 99.99,
            "yearly_price_usd": 999.99,
        },
        {
            "plan_type": "enterprise",
            "max_messages_per_month": 100_000,
            "max_tokens_per_month": 500_000_000,
            "max_images_per_month": 10_000,
            "max_documents_per_month": 50_000,
            "max_audio_minutes_per_month": 10_000,
            "web_search_enabled": True,
            "image_generation_enabled": True,
            "pdf_processing_enabled": True,
            "audio_processing_enabled": True,
            "prompt_caching_enabled": True,
            "advanced_models_enabled": True,
            "presets_limit": 500,
            "max_context_length": 1_000_000,
            "priority_support": True,
            "monthly_price_usd": 499.99,
            "yearly_price_usd": 4_999.99,
        },
    ]

    async with async_session_maker() as db:
        for plan_data in plans:
            # Check if plan already exists
            result = await db.execute(
                select(PlanLimit).where(PlanLimit.plan_type == plan_data["plan_type"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(
                    "plan_already_exists",
                    plan_type=plan_data["plan_type"],
                    action="skipping",
                )
                continue

            # Create new plan
            plan = PlanLimit(**plan_data)
            db.add(plan)

            logger.info(
                "plan_created",
                plan_type=plan_data["plan_type"],
                monthly_price=plan_data["monthly_price_usd"],
            )

        await db.commit()
        logger.info("plan_limits_seeded", total_plans=len(plans))


async def main():
    """Main function."""
    try:
        logger.info("starting_plan_limits_seed")
        await seed_plan_limits()
        logger.info("plan_limits_seed_completed")
    except Exception as e:
        logger.error("plan_limits_seed_failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
