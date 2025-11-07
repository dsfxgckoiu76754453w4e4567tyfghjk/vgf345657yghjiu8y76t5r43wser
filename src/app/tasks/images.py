"""
Image generation tasks (HIGH PRIORITY).

Handles asynchronous AI image generation with:
- OpenRouter integration (DALL-E, Flux, Gemini)
- Progress tracking
- Storage to MinIO
- Cost tracking
- Quota validation
"""

import asyncio
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.services.image_generation_service import ImageGenerationService

logger = get_logger(__name__)

# Create async engine for database operations
async_engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class ImageGenerationTask(Task):
    """Custom task class with progress tracking."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            "image_generation_success",
            task_id=task_id,
            user_id=kwargs.get('user_id'),
            prompt_length=len(kwargs.get('prompt', '')),
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            "image_generation_failure",
            task_id=task_id,
            exception=str(exc),
            user_id=kwargs.get('user_id'),
        )


@celery_app.task(
    base=ImageGenerationTask,
    bind=True,
    name='app.tasks.images.generate_image',
    max_retries=2,  # Only 2 retries for expensive operations
    default_retry_delay=10,
    acks_late=True,
    time_limit=300,  # 5 minutes max (some image models are slow)
)
def generate_image(
    self,
    user_id: str,
    prompt: str,
    conversation_id: str | None = None,
    model: str | None = None,
    aspect_ratio: str = "1:1",
    output_format: str = "url",
) -> dict:
    """
    Generate AI image asynchronously.

    Args:
        self: Celery task instance
        user_id: User ID (string UUID)
        prompt: Image generation prompt
        conversation_id: Optional conversation ID (string UUID)
        model: Optional model override (default: Gemini Flash)
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, etc.)
        output_format: Output format (url or base64)

    Returns:
        dict: Generated image with URL, metadata, and cost

    Raises:
        Exception: If image generation fails after retries
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={
                'progress': 0,
                'status': 'Initializing image generation...',
                'user_id': user_id,
                'prompt': prompt[:100],
            }
        )

        # Convert string UUID to UUID object
        user_uuid = UUID(user_id)
        conversation_uuid = UUID(conversation_id) if conversation_id else None

        logger.info(
            "generating_image",
            task_id=self.request.id,
            user_id=user_id,
            prompt_length=len(prompt),
            model=model,
            aspect_ratio=aspect_ratio,
            environment=settings.environment,
        )

        # Run async image generation in sync context
        async def _generate_image():
            """Inner async function to handle image generation."""
            async with async_session_maker() as db:
                # Update progress: Checking quota
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 10,
                        'status': 'Checking quota and limits...',
                    }
                )

                # Initialize image generation service
                image_service = ImageGenerationService()

                # Update progress: Submitting to AI model
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 30,
                        'status': f'Generating image with {model or "default model"}...',
                    }
                )

                # Generate image
                result = await image_service.generate_image(
                    user_id=user_uuid,
                    prompt=prompt,
                    db=db,
                    conversation_id=conversation_uuid,
                    model=model,
                    aspect_ratio=aspect_ratio,
                    output_format=output_format,
                )

                # Update progress: Image generated
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 90,
                        'status': 'Saving image...',
                    }
                )

                return result

        # Execute async code
        result = asyncio.run(_generate_image())

        logger.info(
            "image_generated",
            task_id=self.request.id,
            user_id=user_id,
            image_id=result.get('image_id'),
            cost_usd=result.get('cost_usd', 0),
            model_used=result.get('model'),
        )

        # Return final result
        return {
            'status': 'success',
            'task_id': self.request.id,
            'result': result,
            'environment': settings.environment,
        }

    except Exception as exc:
        logger.error(
            "image_generation_error",
            task_id=self.request.id,
            user_id=user_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )

        # Retry on transient errors
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)

        # Don't retry on quota exceeded or validation errors
        if 'quota' in str(exc).lower() or 'limit' in str(exc).lower():
            raise

        # Retry other errors once
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        raise
