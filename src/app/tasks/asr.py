"""
Audio transcription tasks (HIGH PRIORITY).

Handles asynchronous audio-to-text transcription with:
- OpenAI Whisper / Google Speech-to-Text
- Multi-language support
- Progress tracking
- Storage to MinIO
- Cost tracking
"""

import asyncio
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.services.asr_service import ASRService

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


class ASRTask(Task):
    """Custom task class with progress tracking."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            "asr_transcription_success",
            task_id=task_id,
            user_id=kwargs.get('user_id'),
            language=kwargs.get('language'),
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            "asr_transcription_failure",
            task_id=task_id,
            exception=str(exc),
            user_id=kwargs.get('user_id'),
        )


@celery_app.task(
    base=ASRTask,
    bind=True,
    name='app.tasks.asr.transcribe_audio',
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
    time_limit=180,  # 3 minutes max
)
def transcribe_audio(
    self,
    user_id: str,
    audio_file_path: str,
    language: str = "auto",
    provider: str | None = None,
    conversation_id: str | None = None,
) -> dict:
    """
    Transcribe audio to text asynchronously.

    Args:
        self: Celery task instance
        user_id: User ID (string UUID)
        audio_file_path: Path to audio file in MinIO or local filesystem
        language: Language code (ar, fa, en, etc.) or "auto" for auto-detection
        provider: ASR provider ("whisper" or "google", default from settings)
        conversation_id: Optional conversation ID (string UUID)

    Returns:
        dict: Transcription result with text, language, confidence, etc.

    Raises:
        Exception: If transcription fails after retries
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={
                'progress': 0,
                'status': 'Initializing audio transcription...',
                'user_id': user_id,
                'language': language,
            }
        )

        # Convert string UUID to UUID object
        user_uuid = UUID(user_id)
        conversation_uuid = UUID(conversation_id) if conversation_id else None

        logger.info(
            "transcribing_audio",
            task_id=self.request.id,
            user_id=user_id,
            audio_file=audio_file_path,
            language=language,
            provider=provider or settings.asr_provider,
            environment=settings.environment,
        )

        # Run async transcription in sync context
        async def _transcribe_audio():
            """Inner async function to handle audio transcription."""
            async with async_session_maker() as db:
                # Update progress: Loading audio
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 10,
                        'status': 'Loading audio file...',
                    }
                )

                # Initialize ASR service
                asr_service = ASRService()

                # Update progress: Transcribing
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 30,
                        'status': f'Transcribing audio ({provider or settings.asr_provider})...',
                    }
                )

                # Read audio file (from MinIO or local)
                # Note: audio_file_path should be the raw audio bytes or a path
                # For now, assuming it's bytes or the service handles file loading

                # Transcribe audio
                result = await asr_service.transcribe_audio(
                    audio_data=audio_file_path,  # Service should handle file loading
                    language=language if language != "auto" else None,
                    provider=provider,
                )

                # Update progress: Processing complete
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 90,
                        'status': 'Finalizing transcription...',
                    }
                )

                # Add metadata
                result['user_id'] = str(user_uuid)
                if conversation_uuid:
                    result['conversation_id'] = str(conversation_uuid)

                return result

        # Execute async code
        result = asyncio.run(_transcribe_audio())

        logger.info(
            "audio_transcribed",
            task_id=self.request.id,
            user_id=user_id,
            transcript_length=len(result.get('transcript', '')),
            language_detected=result.get('language'),
            provider_used=result.get('provider'),
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
            "asr_transcription_error",
            task_id=self.request.id,
            user_id=user_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )

        # Retry on transient errors
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)

        # Don't retry on validation errors (invalid audio format, etc.)
        if 'invalid' in str(exc).lower() or 'format' in str(exc).lower():
            raise

        # Retry other errors once
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        raise
