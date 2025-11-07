"""
Chat processing tasks (HIGH PRIORITY).

Handles asynchronous LLM chat message processing with:
- Intent detection
- Model routing
- Prompt caching
- Progress tracking
- Langfuse integration
"""

import asyncio
from typing import Any
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.services.enhanced_chat_service import EnhancedChatService

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


class ChatTask(Task):
    """Custom task class with progress tracking."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            "chat_task_success",
            task_id=task_id,
            user_id=kwargs.get('user_id'),
            conversation_id=kwargs.get('conversation_id'),
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            "chat_task_failure",
            task_id=task_id,
            exception=str(exc),
            user_id=kwargs.get('user_id'),
            conversation_id=kwargs.get('conversation_id'),
        )


@celery_app.task(
    base=ChatTask,
    bind=True,
    name='app.tasks.chat.process_chat_message',
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def process_chat_message(
    self,
    user_id: str,
    conversation_id: str,
    message_content: str,
    model: str | None = None,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    enable_caching: bool = True,
    response_schema: dict[str, Any] | None = None,
    auto_detect_images: bool = True,
    langfuse_trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Process chat message asynchronously.

    Args:
        self: Celery task instance
        user_id: User ID (string UUID)
        conversation_id: Conversation ID (string UUID)
        message_content: User's message text
        model: Optional model override
        system_prompt: Optional system prompt override
        temperature: Optional temperature override
        max_tokens: Optional max_tokens override
        enable_caching: Enable prompt caching (default: True)
        response_schema: Optional JSON schema for structured output
        auto_detect_images: Auto-detect image generation intents (default: True)
        langfuse_trace_id: Optional Langfuse trace ID for observability

    Returns:
        dict: Chat response with message, tokens, cost, etc.

    Raises:
        Exception: If chat processing fails after retries
    """
    try:
        # Update task state to STARTED with initial progress
        self.update_state(
            state='STARTED',
            meta={
                'progress': 0,
                'status': 'Initializing chat processing...',
                'user_id': user_id,
                'conversation_id': conversation_id,
            }
        )

        # Convert string UUIDs to UUID objects
        user_uuid = UUID(user_id)
        conversation_uuid = UUID(conversation_id)

        logger.info(
            "processing_chat_message",
            task_id=self.request.id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_length=len(message_content),
            model=model,
            environment=settings.environment,
        )

        # Run async chat service in sync context
        async def _process_chat():
            """Inner async function to handle chat processing."""
            async with async_session_maker() as db:
                # Update progress: Intent detection
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 20,
                        'status': 'Detecting intents...',
                    }
                )

                # Initialize chat service
                chat_service = EnhancedChatService()

                # Update progress: Preparing LLM request
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 40,
                        'status': 'Preparing LLM request...',
                    }
                )

                # Call chat service (no streaming for background tasks)
                result = await chat_service.chat(
                    user_id=user_uuid,
                    conversation_id=conversation_uuid,
                    message_content=message_content,
                    db=db,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    enable_caching=enable_caching,
                    enable_streaming=False,  # No streaming for background tasks
                    response_schema=response_schema,
                    auto_detect_images=auto_detect_images,
                    langfuse_trace_id=langfuse_trace_id,
                )

                # Update progress: Processing complete
                self.update_state(
                    state='STARTED',
                    meta={
                        'progress': 90,
                        'status': 'Finalizing response...',
                    }
                )

                return result

        # Execute async code
        result = asyncio.run(_process_chat())

        logger.info(
            "chat_message_processed",
            task_id=self.request.id,
            user_id=user_id,
            conversation_id=conversation_id,
            response_length=len(result.get('response', '')),
            total_tokens=result.get('usage', {}).get('total_tokens', 0),
            total_cost=result.get('usage', {}).get('total_cost_usd', 0),
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
            "chat_processing_error",
            task_id=self.request.id,
            user_id=user_id,
            conversation_id=conversation_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )

        # Retry on transient errors
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

        # Don't retry on validation errors or permanent failures
        raise
