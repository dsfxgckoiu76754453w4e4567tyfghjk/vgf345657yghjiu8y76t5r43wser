"""Enhanced chat service with OpenRouter advanced features."""

import json
from datetime import datetime
from typing import Any, AsyncGenerator
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.models.chat import Conversation, Message
from app.services.openrouter_service import OpenRouterService
from app.services.subscription_service import subscription_service
from app.services.intent_detector import intent_detector
from app.services.image_generation_service import image_generation_service
from sqlalchemy.ext.asyncio import AsyncSession

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
    - Automatic image generation detection
    """

    def __init__(self):
        """Initialize enhanced chat service."""
        self.openrouter = OpenRouterService()

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

        # Detect image generation intent (if enabled)
        generated_image = None
        if auto_detect_images and settings.image_generation_enabled:
            should_generate, image_prompt = intent_detector.should_generate_image(
                message=message_content,
                explicit_request=False,
            )

            if should_generate and image_prompt:
                try:
                    logger.info(
                        "auto_image_generation_detected",
                        user_id=str(user_id),
                        conversation_id=str(conversation_id),
                        prompt=image_prompt,
                    )

                    # Generate image
                    generated_image = await image_generation_service.generate_image(
                        prompt=image_prompt,
                        user_id=user_id,
                        db=db,
                        conversation_id=conversation_id,
                    )

                    logger.info(
                        "auto_image_generation_success",
                        user_id=str(user_id),
                        image_id=str(generated_image["id"]),
                    )
                except Exception as e:
                    # Don't fail the entire chat if image generation fails
                    logger.warning(
                        "auto_image_generation_failed",
                        user_id=str(user_id),
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

            # Add generated image if available
            if generated_image:
                response["generated_image"] = generated_image

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
