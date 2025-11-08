"""OpenRouter client service with Langfuse integration for cost tracking."""

import os
from typing import Any, Literal, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger

# Import Langfuse OpenAI wrapper when enabled, otherwise use regular OpenAI
if settings.langfuse_enabled:
    from langfuse.openai import AsyncOpenAI
    logger = get_logger(__name__)
    logger.info("langfuse_openai_wrapper_enabled")
else:
    from openai import AsyncOpenAI
    logger = get_logger(__name__)


class OpenRouterService:
    """
    Comprehensive OpenRouter client service with Langfuse observability.

    Features:
    - Prompt caching (Anthropic, OpenAI, Gemini, DeepSeek, Groq, Grok, Moonshot)
    - Usage accounting with detailed token tracking
    - User tracking for cache stickiness
    - Model routing and automatic fallbacks
    - Structured outputs with JSON schema
    - Multimodal support (images, PDFs, audio)
    - Enhanced error handling
    - **Langfuse integration**: Automatic tracing, cost tracking, and observability
    """

    def __init__(self):
        """Initialize OpenRouter service with Langfuse integration."""
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.app_url = settings.openrouter_app_url
        self.app_name = settings.openrouter_app_name

        # Set OpenAI API key for OpenRouter (required by OpenAI SDK)
        os.environ["OPENAI_API_KEY"] = self.api_key

        # Create OpenAI client with OpenRouter base URL
        # This is automatically traced by Langfuse when enabled
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": self.app_url,
                "X-Title": self.app_name,
            },
        )

        logger.info(
            "openrouter_service_initialized",
            langfuse_enabled=settings.langfuse_enabled,
            base_url=self.base_url
        )

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
        name: str | None = None,  # Langfuse trace name
        metadata: dict[str, Any] | None = None,  # Langfuse metadata
        tags: list[str] | None = None,  # Langfuse tags
        session_id: str | None = None,  # Langfuse session ID
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a chat completion with all advanced features and Langfuse tracing.

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
            name: Name for this generation in Langfuse (optional)
            metadata: Additional metadata for Langfuse tracing (optional)
            tags: Tags for Langfuse tracing (optional)
            session_id: Session ID for Langfuse tracing (optional)
            **kwargs: Additional parameters

        Returns:
            OpenRouter API response with usage data
        """
        # Determine model
        if settings.enable_auto_router and not model:
            selected_model = "openrouter/auto"
        elif model:
            selected_model = model
        else:
            selected_model = settings.openrouter_model

        # Prepare messages with caching
        should_cache = (
            enable_caching if enable_caching is not None else settings.prompt_caching_enabled
        )
        prepared_messages = self._prepare_messages_with_caching(
            messages, should_cache, cache_breakpoints
        )

        # Build extra_body for OpenRouter-specific features
        extra_body = {}

        # Usage accounting (CRITICAL for accurate cost tracking)
        if settings.usage_tracking_enabled:
            extra_body["usage"] = {"include": True}

        # Model routing / fallbacks
        if settings.model_routing_enabled:
            models_list = [selected_model]
            if fallback_models:
                models_list.extend(fallback_models)
            elif settings.default_fallback_models:
                models_list.extend(settings.default_fallback_models)

            if len(models_list) > 1:
                extra_body["models"] = models_list

        # Add any additional kwargs to extra_body
        extra_body.update(kwargs)

        # Prepare parameters for OpenAI SDK
        completion_params = {
            "model": selected_model,
            "messages": prepared_messages,
            "stream": stream,
        }

        # Add optional parameters
        if temperature is not None:
            completion_params["temperature"] = temperature
        if max_tokens is not None:
            completion_params["max_tokens"] = max_tokens
        if user_id and settings.track_user_ids:
            completion_params["user"] = str(user_id)
        if response_schema and settings.structured_outputs_enabled:
            completion_params["response_format"] = {
                "type": "json_schema",
                "json_schema": response_schema
            }

        # Add extra_body if not empty
        if extra_body:
            completion_params["extra_body"] = extra_body

        # Add comprehensive Langfuse parameters if enabled
        if settings.langfuse_enabled:
            # Build comprehensive metadata
            langfuse_metadata = {
                "provider": "openrouter",
                "model_requested": selected_model,
                "caching_enabled": should_cache,
                "structured_output": response_schema is not None,
                "num_messages": len(prepared_messages),
                "stream": stream,
                **(metadata or {}),
            }

            # Build comprehensive tags
            langfuse_tags = ["openrouter", "chat-completion"]
            if stream:
                langfuse_tags.append("streaming")
            if response_schema:
                langfuse_tags.append("structured-output")
            if should_cache:
                langfuse_tags.append("caching-enabled")
            if tags:
                langfuse_tags.extend(tags)

            # Add langfuse params to extra_headers (Langfuse uses these)
            completion_params["extra_headers"] = {
                "langfuse-trace-name": name or "openrouter-completion",
                "langfuse-session-id": session_id or "",
            }

        # Make API call with Langfuse tracing
        try:
            response = await self.client.chat.completions.create(**completion_params)

            # Convert response to dict (OpenAI SDK returns object)
            result = self._parse_openai_response(response)

            logger.info(
                "chat_completion_success",
                model=result.get("model"),
                tokens=result.get("usage", {}).get("total_tokens"),
                cached_tokens=result.get("cached_tokens_read", 0),
                cost_usd=result.get("total_cost_usd"),
                langfuse_enabled=settings.langfuse_enabled,
            )

            return result

        except Exception as e:
            logger.error(
                "chat_completion_error",
                error=str(e),
                model=selected_model,
                langfuse_enabled=settings.langfuse_enabled,
            )
            raise

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

    def _parse_openai_response(self, response) -> dict[str, Any]:
        """
        Parse OpenAI SDK response to dict with OpenRouter cost data.

        OpenRouter returns cost data in the response which Langfuse
        automatically captures when usage accounting is enabled.
        """
        # Convert to dict
        result = {
            "id": response.id,
            "model": response.model,
            "choices": [
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                    },
                    "finish_reason": choice.finish_reason,
                }
                for choice in response.choices
            ],
            "created": response.created,
        }

        # Parse usage data
        if response.usage:
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            # OpenRouter cost data (if available)
            if hasattr(response.usage, "prompt_tokens_details"):
                details = response.usage.prompt_tokens_details
                if details:
                    usage_dict["prompt_tokens_details"] = {
                        "cached_tokens": getattr(details, "cached_tokens", 0),
                    }
                    # Add cached_tokens_read to top level for easier access
                    result["cached_tokens_read"] = getattr(details, "cached_tokens", 0)

            # OpenRouter may include cost in usage (via extra fields)
            # These are automatically captured by Langfuse
            if hasattr(response.usage, "cost"):
                result["total_cost_usd"] = response.usage.cost

            result["usage"] = usage_dict

        return result

    async def get_models(self) -> list[dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        # Use httpx for this endpoint as it's not a completion
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.app_url,
                    "X-Title": self.app_name,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

    async def get_credits(self) -> dict[str, Any]:
        """Get OpenRouter credit balance."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.app_url,
                    "X-Title": self.app_name,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_generation(self, generation_id: str) -> dict[str, Any]:
        """Get generation details including usage data."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.app_url,
                    "X-Title": self.app_name,
                },
            )
            response.raise_for_status()
            return response.json()


# Global service instance
openrouter_service = OpenRouterService()
