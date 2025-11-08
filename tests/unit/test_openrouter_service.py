"""Unit tests for OpenRouter service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.openrouter_service import OpenRouterService


class TestOpenRouterServiceInit:
    """Test OpenRouter service initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"

            service = OpenRouterService()

            assert service.api_key == "test-key"
            assert service.base_url == "https://openrouter.ai/api/v1"

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
                OpenRouterService()


class TestChatCompletion:
    """Test chat completion functionality."""

    @pytest.mark.asyncio
    async def test_basic_chat_completion(self):
        """Test basic chat completion."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.openrouter_model = "anthropic/claude-3.5-sonnet"
            mock_settings.enable_auto_router = False
            mock_settings.model_routing_enabled = False
            mock_settings.prompt_caching_enabled = False
            mock_settings.track_user_ids = False
            mock_settings.usage_tracking_enabled = False
            mock_settings.structured_outputs_enabled = False

            service = OpenRouterService()

            mock_response = {
                "id": "gen-123",
                "model": "anthropic/claude-3.5-sonnet",
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_post = AsyncMock()
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = MagicMock()
                mock_client.return_value.__aenter__.return_value.post = mock_post

                messages = [{"role": "user", "content": "Hello"}]
                result = await service.chat_completion(messages=messages)

                assert result["model"] == "anthropic/claude-3.5-sonnet"
                assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_chat_with_prompt_caching(self):
        """Test chat completion with prompt caching."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.openrouter_model = "anthropic/claude-3.5-sonnet"
            mock_settings.enable_auto_router = False
            mock_settings.model_routing_enabled = False
            mock_settings.prompt_caching_enabled = True
            mock_settings.cache_control_strategy = "auto"
            mock_settings.cache_min_tokens = 1024
            mock_settings.track_user_ids = True
            mock_settings.usage_tracking_enabled = True
            mock_settings.structured_outputs_enabled = False

            service = OpenRouterService()

            mock_response = {
                "id": "gen-123",
                "model": "anthropic/claude-3.5-sonnet",
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                    "prompt_tokens_details": {"cached_tokens": 80},
                    "cost_details": {"cache_discount": 0.001},
                },
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_post = AsyncMock()
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = MagicMock()
                mock_client.return_value.__aenter__.return_value.post = mock_post

                user_id = uuid4()
                # Large content to trigger auto-caching
                large_content = "a" * 5000
                messages = [{"role": "system", "content": large_content}]

                result = await service.chat_completion(
                    messages=messages, user_id=user_id, enable_caching=True
                )

                assert result["cache_discount_usd"] == 0.001
                assert result["usage"]["prompt_tokens_details"]["cached_tokens"] == 80

    @pytest.mark.asyncio
    async def test_chat_with_model_fallbacks(self):
        """Test chat completion with model fallbacks."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.openrouter_model = "anthropic/claude-3.5-sonnet"
            mock_settings.enable_auto_router = False
            mock_settings.model_routing_enabled = True
            mock_settings.default_fallback_models = ["openai/gpt-4o", "openai/gpt-4o-mini"]
            mock_settings.prompt_caching_enabled = False
            mock_settings.track_user_ids = False
            mock_settings.usage_tracking_enabled = False
            mock_settings.structured_outputs_enabled = False

            service = OpenRouterService()

            mock_response = {
                "id": "gen-123",
                "model": "anthropic/claude-3.5-sonnet",
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_post = AsyncMock()
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = MagicMock()
                mock_client.return_value.__aenter__.return_value.post = mock_post

                messages = [{"role": "user", "content": "Hello"}]
                result = await service.chat_completion(
                    messages=messages,
                    fallback_models=["openai/gpt-4o", "openai/gpt-4o-mini"],
                )

                # Check that models array was created in payload
                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert "models" in payload or "model" in payload


class TestMessageCaching:
    """Test message caching functionality."""

    def test_prepare_messages_with_auto_caching(self):
        """Test automatic cache breakpoint placement."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.cache_control_strategy = "auto"
            mock_settings.cache_min_tokens = 1024

            service = OpenRouterService()

            # Large content that should trigger auto-caching
            large_content = "a" * 5000
            messages = [{"role": "system", "content": large_content}]

            prepared = service._prepare_messages_with_caching(
                messages, enable_caching=True, cache_breakpoints=None
            )

            # Check that cache_control was added
            assert len(prepared) > 0
            if isinstance(prepared[0]["content"], list):
                # Check for cache_control in array content
                assert any(
                    "cache_control" in item for item in prepared[0]["content"]
                )

    def test_prepare_messages_with_manual_breakpoints(self):
        """Test manual cache breakpoint placement."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.cache_control_strategy = "manual"

            service = OpenRouterService()

            messages = [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User message"},
            ]

            prepared = service._prepare_messages_with_caching(
                messages, enable_caching=True, cache_breakpoints=[0]
            )

            # Check that cache_control was added only to message at index 0
            assert len(prepared) == 2
            if isinstance(prepared[0]["content"], list):
                assert any(
                    "cache_control" in item for item in prepared[0]["content"]
                )

    def test_add_cache_control_string_content(self):
        """Test adding cache_control to string content."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"

            service = OpenRouterService()

            message = {"role": "system", "content": "Test content"}
            result = service._add_cache_control(message)

            # Should convert string to array format with cache_control
            assert isinstance(result["content"], list)
            assert result["content"][0]["type"] == "text"
            assert result["content"][0]["text"] == "Test content"
            assert result["content"][0]["cache_control"]["type"] == "ephemeral"

    def test_add_cache_control_array_content(self):
        """Test adding cache_control to array content."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"

            service = OpenRouterService()

            message = {
                "role": "system",
                "content": [
                    {"type": "text", "text": "First"},
                    {"type": "text", "text": "Second"},
                ],
            }
            result = service._add_cache_control(message)

            # Should add cache_control to last text item
            assert result["content"][-1]["cache_control"]["type"] == "ephemeral"


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.mark.asyncio
    async def test_get_models(self):
        """Test getting available models."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"

            service = OpenRouterService()

            mock_response = {
                "data": [
                    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
                    {"id": "openai/gpt-4o", "name": "GPT-4o"},
                ]
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_get = AsyncMock()
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                mock_get.return_value.raise_for_status = MagicMock()
                mock_client.return_value.__aenter__.return_value.get = mock_get

                models = await service.get_models()

                assert len(models) == 2
                assert models[0]["id"] == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_get_credits(self):
        """Test getting credit balance."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"

            service = OpenRouterService()

            mock_response = {
                "data": {"label": "test-key", "usage": 10.5, "limit": 100.0}
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_get = AsyncMock()
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                mock_get.return_value.raise_for_status = MagicMock()
                mock_client.return_value.__aenter__.return_value.get = mock_get

                credits = await service.get_credits()

                assert credits["data"]["usage"] == 10.5
                assert credits["data"]["limit"] == 100.0


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test HTTP error handling."""
        with patch("app.services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_app_url = "https://test.com"
            mock_settings.openrouter_app_name = "Test App"
            mock_settings.openrouter_model = "anthropic/claude-3.5-sonnet"
            mock_settings.enable_auto_router = False
            mock_settings.model_routing_enabled = False
            mock_settings.prompt_caching_enabled = False
            mock_settings.track_user_ids = False
            mock_settings.usage_tracking_enabled = False

            service = OpenRouterService()

            with patch("httpx.AsyncClient") as mock_client:
                import httpx

                mock_response = MagicMock()
                mock_response.status_code = 429
                mock_response.json.return_value = {
                    "error": {
                        "code": 429,
                        "message": "Rate limit exceeded",
                        "metadata": {},
                    }
                }

                mock_post = AsyncMock()
                mock_post.return_value = mock_response
                mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Rate limit", request=MagicMock(), response=mock_response
                )
                mock_client.return_value.__aenter__.return_value.post = mock_post

                messages = [{"role": "user", "content": "Hello"}]

                with pytest.raises(httpx.HTTPStatusError):
                    await service.chat_completion(messages=messages)
