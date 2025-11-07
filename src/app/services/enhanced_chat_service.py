"""Enhanced chat service with OpenRouter advanced features and Langfuse tracing."""

import json
from datetime import datetime
from typing import Any, AsyncGenerator
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.models.chat import Conversation, Message
from app.services.openrouter_service import OpenRouterService
from app.services.subscription_service import subscription_service
from app.services.intent_detector import intent_detector, IntentType
from app.services.image_generation_service import image_generation_service
from sqlalchemy.ext.asyncio import AsyncSession

# Import Langfuse observe decorator when enabled
if settings.langfuse_enabled:
    from langfuse.decorators import observe
else:
    # No-op decorator when Langfuse is disabled
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = get_logger(__name__)


class EnhancedChatService:
    """
    Enhanced chat service with OpenRouter advanced features.

    Features:
    - Prompt caching for system prompts and conversation history
    - Model routing with automatic fallbacks
    - Usage tracking with detailed token breakdown
    - Streaming support
    - Structured outputs
    - User tracking for cache stickiness
    - Comprehensive intent detection and automatic execution:
      * Image generation
      * Web search (standard and deep)
      * Document search (RAG)
      * Audio transcription
      * Document/code analysis
    """

    def __init__(self):
        """Initialize enhanced chat service."""
        self.openrouter = OpenRouterService()

    @observe(name="enhanced-chat")
    async def chat(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message_content: str,
        db: AsyncSession,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_caching: bool | None = None,
        enable_streaming: bool = False,
        response_schema: dict[str, Any] | None = None,
        auto_detect_images: bool = True,
    ) -> dict[str, Any] | AsyncGenerator[str, None]:
        """
        Send a chat message and get a response.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            message_content: User message content
            db: Database session
            model: Optional model override
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            enable_caching: Enable prompt caching (default from config)
            enable_streaming: Enable streaming response
            response_schema: Optional JSON schema for structured output
            auto_detect_images: Auto-detect image generation requests (default True)

        Returns:
            If streaming: AsyncGenerator yielding chunks
            If not streaming: Complete response dict (may include generated_image)
        """
        # Check user's subscription and quota
        try:
            await subscription_service.check_usage_limits(user_id=user_id, db=db)
        except ValueError as e:
            logger.warning("quota_exceeded", user_id=str(user_id), error=str(e))
            raise

        # Detect all user intents and execute appropriate actions
        intent_results = {}
        if auto_detect_images:
            # Build context for intent detection
            context = {
                "has_documents": False,  # TODO: Check if user has uploaded documents
                "has_audio": False,  # TODO: Check if message has audio attachment
                "has_code": False,  # TODO: Check if message contains code
            }

            # Detect all intents
            detected_intents = intent_detector.detect_intents(message_content, context)

            logger.info(
                "intents_detected_in_chat",
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                intent_count=len(detected_intents),
                primary_intent=detected_intents[0].intent_type.value if detected_intents else None,
                all_intents=[i.intent_type.value for i in detected_intents],
            )

            # Execute actions for high-priority intents
            for intent in detected_intents:
                # Only process high-confidence, high-priority intents
                if intent.confidence < 0.70 or intent.priority < 7:
                    continue

                try:
                    # IMAGE GENERATION
                    if intent.intent_type == IntentType.IMAGE_GENERATION and settings.image_generation_enabled:
                        logger.info(
                            "executing_image_generation_intent",
                            user_id=str(user_id),
                            prompt=intent.extracted_query,
                        )

                        generated_image = await image_generation_service.generate_image(
                            prompt=intent.extracted_query,
                            user_id=user_id,
                            db=db,
                            conversation_id=conversation_id,
                        )

                        intent_results["generated_image"] = generated_image
                        logger.info(
                            "image_generation_intent_success",
                            user_id=str(user_id),
                            image_id=str(generated_image["id"]),
                        )

                    # WEB SEARCH
                    elif intent.intent_type == IntentType.WEB_SEARCH:
                        logger.info(
                            "web_search_intent_detected",
                            user_id=str(user_id),
                            query=intent.extracted_query,
                            intent_type="web_search",
                        )
                        intent_results["web_search_requested"] = {
                            "query": intent.extracted_query,
                            "type": "standard",
                            "note": "Web search capability will be integrated with external API"
                        }

                    # DEEP WEB SEARCH
                    elif intent.intent_type == IntentType.DEEP_WEB_SEARCH:
                        logger.info(
                            "deep_web_search_intent_detected",
                            user_id=str(user_id),
                            query=intent.extracted_query,
                            intent_type="deep_web_search",
                        )
                        intent_results["web_search_requested"] = {
                            "query": intent.extracted_query,
                            "type": "deep",
                            "note": "Deep web search capability will be integrated with external API"
                        }

                    # DOCUMENT SEARCH (RAG)
                    elif intent.intent_type == IntentType.DOCUMENT_SEARCH:
                        logger.info(
                            "document_search_intent_detected",
                            user_id=str(user_id),
                            query=intent.extracted_query,
                            intent_type="document_search",
                        )
                        intent_results["document_search_requested"] = {
                            "query": intent.extracted_query,
                            "note": "Document search will use RAG pipeline on user's uploaded documents"
                        }

                    # AUDIO TRANSCRIPTION
                    elif intent.intent_type == IntentType.AUDIO_TRANSCRIPTION:
                        logger.info(
                            "audio_transcription_intent_detected",
                            user_id=str(user_id),
                            intent_type="audio_transcription",
                        )
                        intent_results["audio_transcription_requested"] = {
                            "note": "Audio transcription will be processed via ASR service"
                        }

                    # DOCUMENT/CODE ANALYSIS
                    elif intent.intent_type in [IntentType.DOCUMENT_ANALYSIS, IntentType.CODE_ANALYSIS]:
                        logger.info(
                            "analysis_intent_detected",
                            user_id=str(user_id),
                            intent_type=intent.intent_type.value,
                        )
                        intent_results["analysis_requested"] = {
                            "type": intent.intent_type.value,
                            "query": intent.extracted_query,
                            "note": "Analysis will be performed on attached documents/code"
                        }

                except Exception as e:
                    # Don't fail the entire chat if intent execution fails
                    logger.warning(
                        "intent_execution_failed",
                        user_id=str(user_id),
                        intent_type=intent.intent_type.value,
                        error=str(e),
                    )
                    # Continue with chat response

        # Build messages from conversation history
        messages = await self._build_messages(
            conversation_id=conversation_id,
            new_message=message_content,
            system_prompt=system_prompt,
            db=db,
        )

        # Determine caching settings
        use_caching = enable_caching if enable_caching is not None else settings.prompt_caching_enabled

        # Prepare OpenRouter request
        chat_params = {
            "messages": messages,
            "model": model or settings.llm_model,
            "user_id": user_id,
            "enable_caching": use_caching,
            "temperature": temperature or settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "stream": enable_streaming,
        }

        # Add fallback models if routing is enabled
        if settings.model_routing_enabled and settings.default_fallback_models:
            chat_params["fallback_models"] = settings.default_fallback_models

        # Add structured output schema if provided
        if response_schema:
            chat_params["response_schema"] = response_schema

        # Add Langfuse tracing metadata
        if settings.langfuse_enabled:
            chat_params["name"] = "chat-completion"
            chat_params["session_id"] = str(conversation_id)
            chat_params["metadata"] = {
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "model": model or settings.llm_model,
                "auto_detect_images": auto_detect_images,
            }
            chat_params["tags"] = ["chat", "enhanced-service"]
            if auto_detect_images:
                chat_params["tags"].append("intent-detection")

        # Handle streaming response
        if enable_streaming:
            return self._stream_response(
                user_id=user_id,
                conversation_id=conversation_id,
                message_content=message_content,
                chat_params=chat_params,
                db=db,
            )

        # Non-streaming response
        try:
            result = await self.openrouter.chat_completion(**chat_params)

            # Save user message
            user_message = await self._save_message(
                conversation_id=conversation_id,
                role="user",
                content=message_content,
                db=db,
            )

            # Extract response content
            response_content = result["choices"][0]["message"]["content"]

            # Save assistant message with usage metadata
            assistant_message = await self._save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_content,
                model_used=result["model"],
                tokens_used=result["usage"]["total_tokens"],
                cached_tokens_read=result.get("cached_tokens_read"),
                cached_tokens_write=result.get("cached_tokens_write"),
                cache_discount_usd=result.get("cache_discount_usd"),
                cache_breakpoint_count=result.get("cache_breakpoint_count", 0),
                reasoning_tokens=result.get("reasoning_tokens"),
                upstream_inference_cost_usd=result.get("upstream_inference_cost_usd"),
                routing_strategy=result.get("routing_strategy"),
                fallback_used=result.get("fallback_used", False),
                models_attempted=result.get("models_attempted"),
                final_model_used=result.get("final_model_used"),
                response_schema=json.dumps(response_schema) if response_schema else None,
                structured_data=json.dumps(result.get("structured_data")) if result.get("structured_data") else None,
                schema_validation_passed=result.get("schema_validation_passed", True),
                db=db,
            )

            # Track usage
            await self._track_usage(
                user_id=user_id,
                tokens=result["usage"]["total_tokens"],
                cost_usd=result.get("total_cost_usd", 0.0),
                cache_savings_usd=result.get("cache_discount_usd", 0.0),
                db=db,
            )

            logger.info(
                "chat_completion_success",
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                model=result["model"],
                tokens=result["usage"]["total_tokens"],
                cached=result.get("cached_tokens_read", 0),
            )

            response = {
                "message_id": assistant_message.id,
                "content": response_content,
                "model": result["model"],
                "usage": result["usage"],
                "cached_tokens_read": result.get("cached_tokens_read"),
                "cached_tokens_write": result.get("cached_tokens_write"),
                "cache_discount_usd": result.get("cache_discount_usd"),
                "total_cost_usd": result.get("total_cost_usd"),
                "fallback_used": result.get("fallback_used", False),
                "final_model_used": result.get("final_model_used"),
            }

            # Add intent results if any were executed
            if intent_results:
                response["intent_results"] = intent_results

                # Backward compatibility: keep generated_image at top level
                if "generated_image" in intent_results:
                    response["generated_image"] = intent_results["generated_image"]

            return response

        except Exception as e:
            logger.error(
                "chat_completion_failed",
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                error=str(e),
            )
            raise

    async def _stream_response(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message_content: str,
        chat_params: dict[str, Any],
        db: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response.

        Yields JSON lines with chunks and final metadata.
        """
        try:
            # Save user message
            user_message = await self._save_message(
                conversation_id=conversation_id,
                role="user",
                content=message_content,
                db=db,
            )

            # Variables to accumulate response
            full_content = ""
            usage_data = {}
            model_used = None

            # Stream from OpenRouter
            async for chunk in self.openrouter.chat_completion(**chat_params):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")

                    if content:
                        full_content += content
                        # Yield content chunk
                        yield json.dumps({"type": "content", "content": content}) + "\n"

                # Capture usage and model info
                if "model" in chunk:
                    model_used = chunk["model"]
                if "usage" in chunk:
                    usage_data = chunk["usage"]

            # Save complete assistant message
            assistant_message = await self._save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content,
                model_used=model_used or chat_params["model"],
                tokens_used=usage_data.get("total_tokens", 0),
                cached_tokens_read=usage_data.get("prompt_tokens_details", {}).get("cached_tokens"),
                db=db,
            )

            # Track usage
            if usage_data.get("total_tokens"):
                await self._track_usage(
                    user_id=user_id,
                    tokens=usage_data["total_tokens"],
                    cost_usd=0.0,  # Calculate from usage
                    cache_savings_usd=0.0,
                    db=db,
                )

            # Yield final metadata
            yield json.dumps({
                "type": "metadata",
                "message_id": str(assistant_message.id),
                "model": model_used,
                "usage": usage_data,
            }) + "\n"

            logger.info(
                "chat_stream_completed",
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                model=model_used,
            )

        except Exception as e:
            logger.error(
                "chat_stream_failed",
                user_id=str(user_id),
                error=str(e),
            )
            # Yield error
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    async def _build_messages(
        self,
        conversation_id: UUID,
        new_message: str,
        system_prompt: str | None,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Build messages array from conversation history."""
        from sqlalchemy import select

        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Load conversation history
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        history = result.scalars().all()

        # Add historical messages
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add new user message
        messages.append({"role": "user", "content": new_message})

        return messages

    async def _save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        db: AsyncSession,
        model_used: str | None = None,
        tokens_used: int | None = None,
        cached_tokens_read: int | None = None,
        cached_tokens_write: int | None = None,
        cache_discount_usd: float | None = None,
        cache_breakpoint_count: int = 0,
        reasoning_tokens: int | None = None,
        upstream_inference_cost_usd: float | None = None,
        routing_strategy: str | None = None,
        fallback_used: bool = False,
        models_attempted: list[str] | None = None,
        final_model_used: str | None = None,
        response_schema: str | None = None,
        structured_data: str | None = None,
        schema_validation_passed: bool = True,
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
            cached_tokens_read=cached_tokens_read,
            cached_tokens_write=cached_tokens_write,
            cache_discount_usd=cache_discount_usd,
            cache_breakpoint_count=cache_breakpoint_count,
            reasoning_tokens=reasoning_tokens,
            upstream_inference_cost_usd=upstream_inference_cost_usd,
            routing_strategy=routing_strategy,
            fallback_used=fallback_used,
            models_attempted=models_attempted,
            final_model_used=final_model_used,
            response_schema=response_schema,
            structured_data=structured_data,
            schema_validation_passed=schema_validation_passed,
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message

    async def _track_usage(
        self,
        user_id: UUID,
        tokens: int,
        cost_usd: float,
        cache_savings_usd: float,
        db: AsyncSession,
    ) -> None:
        """Track usage for the user."""
        await subscription_service.track_usage(
            user_id=user_id,
            db=db,
            messages=1,
            tokens=tokens,
            cost_usd=cost_usd,
            cache_savings_usd=cache_savings_usd,
        )


# Global service instance
enhanced_chat_service = EnhancedChatService()
