"""Chat API endpoints with OpenRouter advanced features and Langfuse tracing."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.core.langfuse_client import trace_request, trace_span, log_event
from app.db.base import get_db
from app.models.user import User
from app.services.enhanced_chat_service import enhanced_chat_service

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class ChatRequest(BaseModel):
    """Chat message request."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str | None = Field(None, description="Optional model override")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens")
    enable_caching: bool | None = Field(None, description="Enable prompt caching")
    stream: bool = Field(False, description="Enable streaming response")
    response_schema: dict[str, Any] | None = Field(None, description="JSON schema for structured output")
    auto_detect_images: bool = Field(True, description="Auto-detect image generation requests")


class ChatResponse(BaseModel):
    """Chat message response."""

    message_id: UUID
    content: str
    model: str
    usage: dict[str, Any]
    cached_tokens_read: int | None = None
    cached_tokens_write: int | None = None
    cache_discount_usd: float | None = None
    total_cost_usd: float | None = None
    fallback_used: bool = False
    final_model_used: str | None = None
    generated_image: dict[str, Any] | None = None
    intent_results: dict[str, Any] | None = None


@router.post("/", response_model=ChatResponse)
async def send_message(
    request_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get a response.

    - **conversation_id**: Conversation ID
    - **message**: User message content
    - **model**: Optional model override (default from settings)
    - **system_prompt**: Optional system prompt
    - **temperature**: Optional temperature (0.0-2.0)
    - **max_tokens**: Optional max tokens
    - **enable_caching**: Enable prompt caching (default from config)
    - **stream**: Enable streaming response (returns SSE)
    - **response_schema**: Optional JSON schema for structured output
    - **auto_detect_images**: Auto-detect image generation requests (default True)

    Features:
    - Automatic prompt caching for system prompts and conversation history
    - Model routing with fallbacks
    - Usage tracking with detailed token breakdown
    - Structured outputs with JSON schema validation
    - Cache-aware cost optimization
    - **Comprehensive Intent Detection**: Automatically detects and executes user intents:
      * **Image Generation**: "generate an image of..."
      * **Web Search**: "search online for...", "google..."
      * **Deep Web Search**: "do a thorough search for..."
      * **Document Search**: "search my documents for..."
      * **Audio Transcription**: "transcribe this audio..."
      * **Code/Document Analysis**: "analyze this code..."

    Intent Detection (Automatic):
    - Detects multiple intents in a single message
    - Prioritizes and executes high-confidence intents
    - Returns results in `intent_results` field
    - Examples:
      * "Generate an image of a mosque" → automatic image generation
      * "Search online for Islamic history" → web search request
      * "Search my documents for Quran verses" → document RAG search

    Returns:
    - If stream=false: Complete response with usage metadata (may include generated_image)
    - If stream=true: Server-Sent Events (SSE) stream
    """
    # Create trace for entire request flow
    with trace_request(
        name="chat-api-request",
        user_id=str(current_user.id),
        session_id=str(request_data.conversation_id),
        metadata={
            "endpoint": "/api/v1/chat",
            "model": request_data.model,
            "stream": request_data.stream,
            "auto_detect_images": request_data.auto_detect_images,
            "has_system_prompt": request_data.system_prompt is not None,
            "has_response_schema": request_data.response_schema is not None,
        },
        tags=["api", "chat", "v1"],
    ) as trace:
        try:
            # Log request received
            log_event(
                trace,
                "request-received",
                metadata={
                    "message_length": len(request_data.message),
                    "conversation_id": str(request_data.conversation_id),
                }
            )

            # Handle streaming
            if request_data.stream:
                log_event(trace, "streaming-mode", metadata={"enabled": True})

                async def generate():
                    async for chunk in await enhanced_chat_service.chat(
                        user_id=current_user.id,
                        conversation_id=request_data.conversation_id,
                        message_content=request_data.message,
                        db=db,
                        model=request_data.model,
                        system_prompt=request_data.system_prompt,
                        temperature=request_data.temperature,
                        max_tokens=request_data.max_tokens,
                        enable_caching=request_data.enable_caching,
                        enable_streaming=True,
                        response_schema=request_data.response_schema,
                        auto_detect_images=request_data.auto_detect_images,
                    ):
                        yield f"data: {chunk}\n\n"

                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            # Non-streaming
            with trace_span(trace, "chat-service-call", metadata={"streaming": False}):
                result = await enhanced_chat_service.chat(
                    user_id=current_user.id,
                    conversation_id=request_data.conversation_id,
                    message_content=request_data.message,
                    db=db,
                    model=request_data.model,
                    system_prompt=request_data.system_prompt,
                    temperature=request_data.temperature,
                    max_tokens=request_data.max_tokens,
                    enable_caching=request_data.enable_caching,
                    enable_streaming=False,
                    response_schema=request_data.response_schema,
                    auto_detect_images=request_data.auto_detect_images,
                )

            logger.info(
                "chat_message_sent",
                user_id=str(current_user.id),
                conversation_id=str(request_data.conversation_id),
                model=result["model"],
            )

            # Update trace with response details
            trace.update(
                output={
                    "message_id": str(result["message_id"]),
                    "model": result["model"],
                    "tokens": result["usage"]["total_tokens"],
                    "cost_usd": result.get("total_cost_usd"),
                    "cached_tokens": result.get("cached_tokens_read", 0),
                    "has_image": result.get("generated_image") is not None,
                    "intent_results": list(result.get("intent_results", {}).keys()),
                },
                metadata={
                    "response_length": len(result["content"]),
                    "cache_hit_rate": (
                        result.get("cached_tokens_read", 0) / result["usage"]["prompt_tokens"]
                        if result["usage"]["prompt_tokens"] > 0 else 0
                    ),
                }
            )

            response = ChatResponse(
                message_id=result["message_id"],
                content=result["content"],
                model=result["model"],
                usage=result["usage"],
                cached_tokens_read=result.get("cached_tokens_read"),
                cached_tokens_write=result.get("cached_tokens_write"),
                cache_discount_usd=result.get("cache_discount_usd"),
                total_cost_usd=result.get("total_cost_usd"),
                fallback_used=result.get("fallback_used", False),
                final_model_used=result.get("final_model_used"),
                generated_image=result.get("generated_image"),
                intent_results=result.get("intent_results"),
            )

            log_event(trace, "response-sent", metadata={"success": True})
            return response

        except ValueError as e:
            # Quota exceeded or validation error
            log_event(trace, "request-failed", metadata={"error": "quota_exceeded"})
            logger.warning(
                "chat_message_failed",
                user_id=str(current_user.id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            log_event(trace, "request-error", metadata={"error": str(e)})
            logger.error(
                "chat_message_error",
                user_id=str(current_user.id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message",
            )


@router.post("/structured", response_model=ChatResponse)
async def send_structured_message(
    request_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message with structured output.

    Same as /chat endpoint but enforces JSON schema validation.

    - **response_schema**: Required JSON schema for structured output

    Example response_schema:
    ```json
    {
      "type": "object",
      "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
      },
      "required": ["answer", "confidence"]
    }
    ```

    The assistant's response will be validated against the schema.
    """
    if not request_data.response_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="response_schema is required for structured output",
        )

    return await send_message(request_data, current_user, db)


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""

    total_messages: int
    cached_messages: int
    total_cached_tokens: int
    total_cache_savings_usd: float
    cache_hit_rate: float


@router.get("/cache-stats/{conversation_id}", response_model=CacheStatsResponse)
async def get_cache_stats(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CacheStatsResponse:
    """
    Get prompt caching statistics for a conversation.

    - **conversation_id**: Conversation ID

    Returns cache hit rate and savings.
    """
    try:
        from sqlalchemy import select, func
        from app.models.chat import Message

        # Get cache statistics
        result = await db.execute(
            select(
                func.count(Message.id).label("total"),
                func.count(Message.cached_tokens_read).label("cached"),
                func.sum(Message.cached_tokens_read).label("total_cached_tokens"),
                func.sum(Message.cache_discount_usd).label("total_savings"),
            ).where(
                Message.conversation_id == conversation_id,
                Message.role == "assistant",
            )
        )

        stats = result.first()

        total_messages = stats.total or 0
        cached_messages = stats.cached or 0
        total_cached_tokens = stats.total_cached_tokens or 0
        total_savings = float(stats.total_savings or 0.0)
        cache_hit_rate = (cached_messages / total_messages) if total_messages > 0 else 0.0

        logger.info(
            "cache_stats_retrieved",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
            cache_hit_rate=cache_hit_rate,
        )

        return CacheStatsResponse(
            total_messages=total_messages,
            cached_messages=cached_messages,
            total_cached_tokens=int(total_cached_tokens),
            total_cache_savings_usd=total_savings,
            cache_hit_rate=cache_hit_rate,
        )

    except Exception as e:
        logger.error(
            "cache_stats_error",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics",
        )
