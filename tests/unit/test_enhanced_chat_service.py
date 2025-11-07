"""Comprehensive unit tests for Enhanced Chat Service."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.enhanced_chat_service import EnhancedChatService
from app.services.intent_detector import IntentResult, IntentType


class TestEnhancedChatServiceInitialization:
    """Test cases for Enhanced Chat Service initialization."""

    def test_initialization(self):
        """Test service initializes correctly."""
        # Act
        service = EnhancedChatService()

        # Assert
        assert service is not None
        assert hasattr(service, 'openrouter')
        assert service.openrouter is not None


class TestEnhancedChatServiceQuotaChecking:
    """Test cases for quota checking."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    async def test_chat_checks_quota_before_processing(self, mock_subscription_service):
        """Test that chat checks usage limits before processing."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        mock_subscription_service.check_usage_limits = AsyncMock()

        # Act & Assert - Will fail at later stage but quota check should be called
        try:
            await service.chat(
                user_id=user_id,
                conversation_id=conversation_id,
                message_content="Test message",
                db=mock_db,
            )
        except:
            pass  # Expected to fail due to other mocking issues

        # Assert quota check was called
        mock_subscription_service.check_usage_limits.assert_called_once_with(
            user_id=user_id,
            db=mock_db,
        )

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    async def test_chat_raises_error_when_quota_exceeded(self, mock_subscription_service):
        """Test that chat raises error when quota is exceeded."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        mock_subscription_service.check_usage_limits = AsyncMock(
            side_effect=ValueError("Quota exceeded")
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Quota exceeded"):
            await service.chat(
                user_id=user_id,
                conversation_id=conversation_id,
                message_content="Test message",
                db=mock_db,
            )


class TestEnhancedChatServiceIntentDetection:
    """Test cases for intent detection and execution."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.intent_detector')
    @patch('app.services.enhanced_chat_service.image_generation_service')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_detects_and_executes_image_generation_intent(
        self,
        mock_settings,
        mock_image_service,
        mock_intent_detector,
        mock_subscription_service,
    ):
        """Test that image generation intent is detected and executed."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.image_generation_enabled = True
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock intent detection
        image_intent = IntentResult(
            intent_type=IntentType.IMAGE_GENERATION,
            confidence=0.95,
            extracted_query="beautiful mosque at sunset",
            priority=10,
        )
        mock_intent_detector.detect_intents.return_value = [image_intent]

        # Mock image generation
        generated_image = {
            "id": str(uuid4()),
            "url": "https://storage.example.com/image.png",
            "prompt": "beautiful mosque at sunset",
        }
        mock_image_service.generate_image = AsyncMock(return_value=generated_image)

        # Mock message building and saving
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Generate a beautiful mosque at sunset"}
        ])
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter response
        openrouter_response = {
            "choices": [{"message": {"content": "I've generated the image for you"}}],
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
        }
        service.openrouter.chat_completion = AsyncMock(return_value=openrouter_response)

        # Act
        result = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Generate a beautiful mosque at sunset",
            db=mock_db,
        )

        # Assert
        assert "intent_results" in result
        assert "generated_image" in result["intent_results"]
        assert result["intent_results"]["generated_image"]["id"] == generated_image["id"]
        mock_image_service.generate_image.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.intent_detector')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_detects_web_search_intent(
        self,
        mock_settings,
        mock_intent_detector,
        mock_subscription_service,
    ):
        """Test that web search intent is detected."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock intent detection
        web_search_intent = IntentResult(
            intent_type=IntentType.WEB_SEARCH,
            confidence=0.85,
            extracted_query="Islamic history",
            priority=8,
        )
        mock_intent_detector.detect_intents.return_value = [web_search_intent]

        # Mock message operations
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Search the web for Islamic history"}
        ])
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter response
        openrouter_response = {
            "choices": [{"message": {"content": "Here's what I found about Islamic history"}}],
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 200, "prompt_tokens": 150, "completion_tokens": 50},
        }
        service.openrouter.chat_completion = AsyncMock(return_value=openrouter_response)

        # Act
        result = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Search the web for Islamic history",
            db=mock_db,
        )

        # Assert
        assert "intent_results" in result
        assert "web_search_requested" in result["intent_results"]
        assert result["intent_results"]["web_search_requested"]["query"] == "Islamic history"
        assert result["intent_results"]["web_search_requested"]["type"] == "standard"

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.intent_detector')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_skips_low_confidence_intents(
        self,
        mock_settings,
        mock_intent_detector,
        mock_subscription_service,
    ):
        """Test that low-confidence intents are not executed."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock intent detection with low confidence
        low_confidence_intent = IntentResult(
            intent_type=IntentType.IMAGE_GENERATION,
            confidence=0.50,  # Below 0.70 threshold
            extracted_query="maybe an image",
            priority=10,
        )
        mock_intent_detector.detect_intents.return_value = [low_confidence_intent]

        # Mock message operations
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Maybe show me an image"}
        ])
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter response
        openrouter_response = {
            "choices": [{"message": {"content": "Response"}}],
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        }
        service.openrouter.chat_completion = AsyncMock(return_value=openrouter_response)

        # Act
        result = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Maybe show me an image",
            db=mock_db,
        )

        # Assert - Low confidence intent should not be executed
        assert "intent_results" not in result or len(result.get("intent_results", {})) == 0


class TestEnhancedChatServiceMessageOperations:
    """Test cases for message building and saving."""

    @pytest.mark.asyncio
    async def test_build_messages_with_system_prompt(self):
        """Test building messages with system prompt."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Mock empty conversation history
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        messages = await service._build_messages(
            conversation_id=conversation_id,
            new_message="Hello",
            system_prompt="You are a helpful assistant",
            db=mock_db,
        )

        # Assert
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_build_messages_without_system_prompt(self):
        """Test building messages without system prompt."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Mock empty conversation history
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        messages = await service._build_messages(
            conversation_id=conversation_id,
            new_message="Hello",
            system_prompt=None,
            db=mock_db,
        )

        # Assert
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_build_messages_with_conversation_history(self):
        """Test building messages with conversation history."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Mock conversation history
        mock_msg1 = MagicMock()
        mock_msg1.role = "user"
        mock_msg1.content = "What is prayer?"

        mock_msg2 = MagicMock()
        mock_msg2.role = "assistant"
        mock_msg2.content = "Prayer is one of the pillars of Islam"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_msg1, mock_msg2]
        mock_db.execute.return_value = mock_result

        # Act
        messages = await service._build_messages(
            conversation_id=conversation_id,
            new_message="Tell me more",
            system_prompt=None,
            db=mock_db,
        )

        # Assert
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is prayer?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Prayer is one of the pillars of Islam"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "Tell me more"

    @pytest.mark.asyncio
    async def test_save_message_user_message(self):
        """Test saving a user message."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        conversation_id = uuid4()

        mock_message = MagicMock()
        mock_message.id = uuid4()
        mock_db.refresh = AsyncMock()

        # Act
        result = await service._save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            db=mock_db,
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_message_assistant_message_with_metadata(self):
        """Test saving assistant message with comprehensive metadata."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Act
        result = await service._save_message(
            conversation_id=conversation_id,
            role="assistant",
            content="Here's my response",
            model_used="anthropic/claude-3-sonnet",
            tokens_used=150,
            cached_tokens_read=50,
            cached_tokens_write=100,
            cache_discount_usd=0.05,
            cache_breakpoint_count=2,
            routing_strategy="fallback",
            fallback_used=True,
            db=mock_db,
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify message fields
        saved_message = mock_db.add.call_args[0][0]
        assert saved_message.role == "assistant"
        assert saved_message.content == "Here's my response"
        assert saved_message.model_used == "anthropic/claude-3-sonnet"
        assert saved_message.tokens_used == 150
        assert saved_message.cached_tokens_read == 50
        assert saved_message.cached_tokens_write == 100
        assert saved_message.fallback_used is True


class TestEnhancedChatServiceUsageTracking:
    """Test cases for usage tracking."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    async def test_track_usage_called_after_chat(self, mock_subscription_service):
        """Test that usage is tracked after successful chat."""
        # Arrange
        service = EnhancedChatService()
        mock_db = AsyncMock()
        user_id = uuid4()

        mock_subscription_service.track_usage = AsyncMock()

        # Act
        await service._track_usage(
            user_id=user_id,
            tokens=150,
            cost_usd=0.01,
            cache_savings_usd=0.005,
            db=mock_db,
        )

        # Assert
        mock_subscription_service.track_usage.assert_called_once_with(
            user_id=user_id,
            db=mock_db,
            messages=1,
            tokens=150,
            cost_usd=0.01,
            cache_savings_usd=0.005,
        )


class TestEnhancedChatServiceStreaming:
    """Test cases for streaming responses."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_stream_response_yields_content_chunks(
        self,
        mock_settings,
        mock_subscription_service,
    ):
        """Test that streaming yields content chunks."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock message saving
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter streaming response
        async def mock_stream():
            yield {"choices": [{"delta": {"content": "Hello"}}]}
            yield {"choices": [{"delta": {"content": " world"}}]}
            yield {"model": "anthropic/claude-3-sonnet", "usage": {"total_tokens": 50}}

        service.openrouter.chat_completion = mock_stream

        # Act
        chat_params = {
            "messages": [{"role": "user", "content": "Test"}],
            "model": "anthropic/claude-3-sonnet",
        }
        chunks = []
        async for chunk in service._stream_response(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Test",
            chat_params=chat_params,
            db=mock_db,
        ):
            chunks.append(chunk)

        # Assert
        assert len(chunks) >= 3  # At least 2 content chunks + 1 metadata
        # First chunks should be content
        content_chunk = json.loads(chunks[0])
        assert content_chunk["type"] == "content"
        assert content_chunk["content"] == "Hello"


class TestEnhancedChatServiceErrorHandling:
    """Test cases for error handling."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.intent_detector')
    @patch('app.services.enhanced_chat_service.image_generation_service')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_continues_when_intent_execution_fails(
        self,
        mock_settings,
        mock_image_service,
        mock_intent_detector,
        mock_subscription_service,
    ):
        """Test that chat continues even if intent execution fails."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.image_generation_enabled = True
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock intent detection
        image_intent = IntentResult(
            intent_type=IntentType.IMAGE_GENERATION,
            confidence=0.95,
            extracted_query="test image",
            priority=10,
        )
        mock_intent_detector.detect_intents.return_value = [image_intent]

        # Mock image generation to fail
        mock_image_service.generate_image = AsyncMock(
            side_effect=Exception("Image generation failed")
        )

        # Mock message operations
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Generate an image"}
        ])
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter response
        openrouter_response = {
            "choices": [{"message": {"content": "Response despite image error"}}],
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        }
        service.openrouter.chat_completion = AsyncMock(return_value=openrouter_response)

        # Act
        result = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Generate an image",
            db=mock_db,
        )

        # Assert - Chat should complete despite intent failure
        assert result is not None
        assert result["content"] == "Response despite image error"
        # Intent results should be empty since execution failed
        assert "generated_image" not in result.get("intent_results", {})

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_raises_error_when_openrouter_fails(
        self,
        mock_settings,
        mock_subscription_service,
    ):
        """Test that chat raises error when OpenRouter fails."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()

        # Mock message operations
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Test"}
        ])

        # Mock OpenRouter to fail
        service.openrouter.chat_completion = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            await service.chat(
                user_id=user_id,
                conversation_id=conversation_id,
                message_content="Test",
                db=mock_db,
                auto_detect_images=False,  # Disable intent detection
            )


class TestEnhancedChatServiceConfiguration:
    """Test cases for configuration options."""

    @pytest.mark.asyncio
    @patch('app.services.enhanced_chat_service.subscription_service')
    @patch('app.services.enhanced_chat_service.settings')
    async def test_chat_respects_custom_parameters(
        self,
        mock_settings,
        mock_subscription_service,
    ):
        """Test that chat respects custom model, temperature, and max_tokens."""
        # Arrange
        service = EnhancedChatService()
        service.openrouter = AsyncMock()

        mock_db = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()

        # Mock settings
        mock_settings.prompt_caching_enabled = False
        mock_settings.llm_model = "anthropic/claude-3-sonnet"  # Default
        mock_settings.llm_temperature = 0.7  # Default
        mock_settings.llm_max_tokens = 1000  # Default
        mock_settings.model_routing_enabled = False
        mock_settings.langfuse_enabled = False

        # Mock quota check
        mock_subscription_service.check_usage_limits = AsyncMock()
        mock_subscription_service.track_usage = AsyncMock()

        # Mock message operations
        service._build_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Test"}
        ])
        mock_message = MagicMock()
        mock_message.id = uuid4()
        service._save_message = AsyncMock(return_value=mock_message)

        # Mock OpenRouter response
        openrouter_response = {
            "choices": [{"message": {"content": "Response"}}],
            "model": "anthropic/claude-3-opus",  # Custom model used
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        }
        service.openrouter.chat_completion = AsyncMock(return_value=openrouter_response)

        # Act
        result = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content="Test",
            db=mock_db,
            model="anthropic/claude-3-opus",  # Custom model
            temperature=0.9,  # Custom temperature
            max_tokens=2000,  # Custom max_tokens
            auto_detect_images=False,
        )

        # Assert
        # Check that OpenRouter was called with custom parameters
        call_kwargs = service.openrouter.chat_completion.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-3-opus"
        assert call_kwargs["temperature"] == 0.9
        assert call_kwargs["max_tokens"] == 2000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
