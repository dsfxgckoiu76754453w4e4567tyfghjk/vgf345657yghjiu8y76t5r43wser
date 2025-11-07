"""OpenRouter client service with advanced features."""

from typing import Any, Literal, Optional
from uuid import UUID

import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenRouterService:
    """
    Comprehensive OpenRouter client service.

    Features:
    - Prompt caching (Anthropic, OpenAI, Gemini, DeepSeek, Groq, Grok, Moonshot)
    - Usage accounting with detailed token tracking
    - User tracking for cache stickiness
    - Model routing and automatic fallbacks
    - Structured outputs with JSON schema
    - Multimodal support (images, PDFs, audio)
    - Enhanced error handling
    """

    def __init__(self):
        """Initialize OpenRouter service."""
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.app_url = settings.openrouter_app_url
        self.app_name = settings.openrouter_app_name

        logger.info("openrouter_service_initialized")

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        user_id: UUID | str | None = None,
        fallback_models: list[str] | None = None,
        enable_caching: bool | None = None,
        cache_breakpoints: list[int] | None = None,
        response_schema: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a chat completion with all advanced features.

        Args:
            messages: Chat messages
            model: Model to use (or None for default)
            user_id: User ID for tracking and cache stickiness
            fallback_models: Models to try if primary fails
            enable_caching: Enable prompt caching (uses config default if None)
            cache_breakpoints: Message indices to add cache breakpoints
            response_schema: JSON schema for structured outputs
            temperature: Temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            stream: Stream responses
            **kwargs: Additional parameters

        Returns:
            OpenRouter API response with usage data
        """
        # Prepare payload
        payload = self._build_payload(
            messages=messages,
            model=model,
            fallback_models=fallback_models,
            user_id=user_id,
            enable_caching=enable_caching,
            cache_breakpoints=cache_breakpoints,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs,
        )

        # Make request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=120.0,
                )
                response.raise_for_status()
                data = response.json()

            # Parse response
            result = self._parse_response(data)

            logger.info(
                "chat_completion_success",
                model=result.get("model"),
                tokens=result.get("usage", {}).get("total_tokens"),
                cached_tokens=result.get("usage", {}).get("prompt_tokens_details", {}).get(
                    "cached_tokens", 0
                ),
            )

            return result

        except httpx.HTTPStatusError as e:
            error_data = self._parse_error(e)
            logger.error(
                "chat_completion_failed",
                status_code=e.response.status_code,
                error=error_data,
            )
            raise

        except Exception as e:
            logger.error("chat_completion_error", error=str(e))
            raise

    def _build_payload(
        self,
        messages: list[dict[str, Any]],
        model: str | None,
        fallback_models: list[str] | None,
        user_id: UUID | str | None,
        enable_caching: bool | None,
        cache_breakpoints: list[int] | None,
        response_schema: dict[str, Any] | None,
        temperature: float | None,
        max_tokens: int | None,
        stream: bool,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build request payload with all features."""
        payload: dict[str, Any] = {}

        # Model routing
        if settings.enable_auto_router and not model:
            payload["model"] = "openrouter/auto"
        elif model:
            payload["model"] = model
        else:
            payload["model"] = settings.openrouter_model

        # Fallback models
        if settings.model_routing_enabled:
            models_list = [payload["model"]]
            if fallback_models:
                models_list.extend(fallback_models)
            elif settings.default_fallback_models:
                models_list.extend(settings.default_fallback_models)

            if len(models_list) > 1:
                payload["models"] = models_list

        # Messages with caching
        should_cache = (
            enable_caching if enable_caching is not None else settings.prompt_caching_enabled
        )
        payload["messages"] = self._prepare_messages_with_caching(
            messages, should_cache, cache_breakpoints
        )

        # User tracking
        if settings.track_user_ids and user_id:
            payload["user"] = str(user_id)

        # Usage accounting
        if settings.usage_tracking_enabled:
            payload["usage"] = {"include": True}

        # Structured outputs
        if response_schema and settings.structured_outputs_enabled:
            payload["response_format"] = {"type": "json_schema", "json_schema": response_schema}

        # Parameters
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        payload["stream"] = stream

        # Additional parameters
        payload.update(kwargs)

        return payload

    def _prepare_messages_with_caching(
        self,
        messages: list[dict[str, Any]],
        enable_caching: bool,
        cache_breakpoints: list[int] | None,
    ) -> list[dict[str, Any]]:
        """
        Prepare messages with cache_control breakpoints.

        For Anthropic and Gemini:
        - Adds cache_control to text content at specified breakpoints
        - Automatically places breakpoints at the end of large content

        For OpenAI, DeepSeek, etc:
        - Caching is automatic (no manual breakpoints needed)
        """
        if not enable_caching or settings.cache_control_strategy == "manual":
            return messages

        prepared_messages = []

        for idx, message in enumerate(messages):
            msg_copy = message.copy()

            # Check if this message should have a cache breakpoint
            should_add_breakpoint = False
            if cache_breakpoints and idx in cache_breakpoints:
                should_add_breakpoint = True
            elif settings.cache_control_strategy == "auto":
                # Auto-add breakpoints to large content (system prompts, RAG context)
                content = message.get("content", "")
                if isinstance(content, str) and len(content) > settings.cache_min_tokens * 3:
                    should_add_breakpoint = True

            # Add cache_control if needed
            if should_add_breakpoint:
                msg_copy = self._add_cache_control(msg_copy)

            prepared_messages.append(msg_copy)

        return prepared_messages

    def _add_cache_control(self, message: dict[str, Any]) -> dict[str, Any]:
        """Add cache_control to a message (Anthropic/Gemini format)."""
        content = message.get("content")

        # Handle string content
        if isinstance(content, str):
            message["content"] = [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
            ]
        # Handle array content
        elif isinstance(content, list) and len(content) > 0:
            # Add cache_control to the last text item
            for i in range(len(content) - 1, -1, -1):
                if content[i].get("type") == "text":
                    content[i]["cache_control"] = {"type": "ephemeral"}
                    break

        return message

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse OpenRouter response with enhanced usage data."""
        result = data.copy()

        # Extract usage data if present
        if "usage" in data:
            usage = data["usage"]

            # Parse cache discount
            if "cost_details" in usage:
                cache_discount = usage["cost_details"].get("cache_discount", 0)
                result["cache_discount_usd"] = cache_discount

            # Parse upstream cost (for BYOK)
            if "cost_details" in usage:
                upstream_cost = usage["cost_details"].get("upstream_inference_cost")
                if upstream_cost:
                    result["upstream_inference_cost_usd"] = upstream_cost / 1000000  # Convert to USD

        return result

    def _parse_error(self, error: httpx.HTTPStatusError) -> dict[str, Any]:
        """Parse OpenRouter error with metadata."""
        try:
            error_data = error.response.json()
            error_info = error_data.get("error", {})

            return {
                "code": error_info.get("code", error.response.status_code),
                "message": error_info.get("message", str(error)),
                "metadata": error_info.get("metadata", {}),
                "status_code": error.response.status_code,
            }
        except Exception:
            return {
                "code": error.response.status_code,
                "message": str(error),
                "metadata": {},
                "status_code": error.response.status_code,
            }

    async def get_models(self) -> list[dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

    async def get_credits(self) -> dict[str, Any]:
        """Get OpenRouter credit balance."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_generation(self, generation_id: str) -> dict[str, Any]:
        """Get generation details including usage data."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()


# Global service instance
openrouter_service = OpenRouterService()
