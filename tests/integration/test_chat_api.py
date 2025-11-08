"""Comprehensive integration tests for Chat API endpoints."""

import pytest
import json
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.main import app
from app.models.user import User


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.subscription_plan = "premium"
    return user


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


class TestChatMessageEndpoint:
    """Test cases for POST /api/v1/chat/ endpoint."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_success(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a chat message successfully."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        message_id = uuid4()
        conversation_id = uuid4()

        mock_chat_service.chat = AsyncMock(return_value={
            "message_id": message_id,
            "content": "This is a test response",
            "model": "anthropic/claude-3-sonnet",
            "usage": {
                "total_tokens": 150,
                "prompt_tokens": 100,
                "completion_tokens": 50,
            },
            "cached_tokens_read": 50,
            "cached_tokens_write": 100,
            "cache_discount_usd": 0.01,
            "total_cost_usd": 0.05,
        })

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "What is Islam?",
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == str(message_id)
        assert data["content"] == "This is a test response"
        assert data["model"] == "anthropic/claude-3-sonnet"
        assert data["usage"]["total_tokens"] == 150
        assert data["cached_tokens_read"] == 50
        assert data["total_cost_usd"] == 0.05

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_with_image_generation(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message that generates an image."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        message_id = uuid4()
        image_id = uuid4()
        conversation_id = uuid4()

        mock_chat_service.chat = AsyncMock(return_value={
            "message_id": message_id,
            "content": "I've generated an image for you",
            "model": "anthropic/claude-3-sonnet",
            "usage": {
                "total_tokens": 200,
                "prompt_tokens": 150,
                "completion_tokens": 50,
            },
            "intent_results": {
                "generated_image": {
                    "id": str(image_id),
                    "url": "https://storage.example.com/image.png",
                    "prompt": "beautiful mosque",
                }
            },
        })

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Generate an image of a beautiful mosque",
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "intent_results" in data
        assert "generated_image" in data["intent_results"]
        assert data["intent_results"]["generated_image"]["id"] == str(image_id)

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_with_custom_parameters(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message with custom parameters."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        message_id = uuid4()
        conversation_id = uuid4()

        mock_chat_service.chat = AsyncMock(return_value={
            "message_id": message_id,
            "content": "Response",
            "model": "anthropic/claude-3-opus",
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        })

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Test message",
                    "model": "anthropic/claude-3-opus",
                    "temperature": 0.9,
                    "max_tokens": 2000,
                    "enable_caching": True,
                    "auto_detect_images": False,
                },
            )

        # Assert
        assert response.status_code == 200
        # Verify chat service was called with custom parameters
        mock_chat_service.chat.assert_called_once()
        call_kwargs = mock_chat_service.chat.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-3-opus"
        assert call_kwargs["temperature"] == 0.9
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["enable_caching"] is True
        assert call_kwargs["auto_detect_images"] is False

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_quota_exceeded(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message when quota is exceeded."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        mock_chat_service.chat = AsyncMock(
            side_effect=ValueError("Quota exceeded")
        )

        conversation_id = uuid4()

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Test message",
                },
            )

        # Assert
        assert response.status_code == 400
        assert "Quota exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_server_error(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message when server error occurs."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        mock_chat_service.chat = AsyncMock(
            side_effect=Exception("Internal server error")
        )

        conversation_id = uuid4()

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Test message",
                },
            )

        # Assert
        assert response.status_code == 500
        assert "Failed to send message" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_with_fallback(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message that uses model fallback."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        message_id = uuid4()
        conversation_id = uuid4()

        mock_chat_service.chat = AsyncMock(return_value={
            "message_id": message_id,
            "content": "Response from fallback model",
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
            "fallback_used": True,
            "final_model_used": "anthropic/claude-3-haiku",
        })

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Test message",
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert data["final_model_used"] == "anthropic/claude-3-haiku"

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_validation_error_empty_message(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_current_user,
        mock_db,
    ):
        """Test sending an empty message fails validation."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "",
                },
            )

        # Assert
        assert response.status_code == 422  # Validation error


class TestStructuredMessageEndpoint:
    """Test cases for POST /api/v1/chat/structured endpoint."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_structured_message_success(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a structured message successfully."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        message_id = uuid4()
        conversation_id = uuid4()

        response_schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["answer", "confidence"]
        }

        mock_chat_service.chat = AsyncMock(return_value={
            "message_id": message_id,
            "content": '{"answer": "Islam is a monotheistic religion", "confidence": 0.95}',
            "model": "anthropic/claude-3-sonnet",
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        })

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/structured",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "What is Islam?",
                    "response_schema": response_schema,
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == str(message_id)
        # Verify response_schema was passed to chat service
        mock_chat_service.chat.assert_called_once()
        call_kwargs = mock_chat_service.chat.call_args[1]
        assert call_kwargs["response_schema"] == response_schema

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_structured_message_without_schema(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_current_user,
        mock_db,
    ):
        """Test sending a structured message without schema fails."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/structured",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "What is Islam?",
                },
            )

        # Assert
        assert response.status_code == 400
        assert "response_schema is required" in response.json()["detail"]


class TestCacheStatsEndpoint:
    """Test cases for GET /api/v1/chat/cache-stats/{conversation_id} endpoint."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_get_cache_stats_success(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_current_user,
        mock_db,
    ):
        """Test getting cache statistics successfully."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Mock database query result
        mock_stats = MagicMock()
        mock_stats.total = 10
        mock_stats.cached = 7
        mock_stats.total_cached_tokens = 500
        mock_stats.total_savings = 0.15

        mock_result = MagicMock()
        mock_result.first.return_value = mock_stats
        mock_db.execute.return_value = mock_result

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/chat/cache-stats/{conversation_id}",
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_messages"] == 10
        assert data["cached_messages"] == 7
        assert data["total_cached_tokens"] == 500
        assert data["total_cache_savings_usd"] == 0.15
        assert data["cache_hit_rate"] == 0.7  # 7/10

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_get_cache_stats_no_messages(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_current_user,
        mock_db,
    ):
        """Test getting cache statistics for conversation with no messages."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Mock empty result
        mock_stats = MagicMock()
        mock_stats.total = 0
        mock_stats.cached = 0
        mock_stats.total_cached_tokens = 0
        mock_stats.total_savings = 0.0

        mock_result = MagicMock()
        mock_result.first.return_value = mock_stats
        mock_db.execute.return_value = mock_result

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/chat/cache-stats/{conversation_id}",
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_messages"] == 0
        assert data["cache_hit_rate"] == 0.0

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_get_cache_stats_database_error(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_current_user,
        mock_db,
    ):
        """Test getting cache statistics when database error occurs."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Mock database error
        mock_db.execute.side_effect = Exception("Database error")

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/chat/cache-stats/{conversation_id}",
            )

        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve cache statistics" in response.json()["detail"]


class TestStreamingMode:
    """Test cases for streaming responses."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chat.enhanced_chat_service')
    @patch('app.api.v1.chat.get_current_user')
    @patch('app.api.v1.chat.get_db')
    async def test_send_message_with_streaming(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_chat_service,
        mock_current_user,
        mock_db,
    ):
        """Test sending a message with streaming enabled."""
        # Arrange
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db

        conversation_id = uuid4()

        # Mock streaming response
        async def mock_stream():
            yield json.dumps({"type": "content", "content": "Hello"}) + "\n"
            yield json.dumps({"type": "content", "content": " world"}) + "\n"
            yield json.dumps({"type": "metadata", "model": "claude-3-sonnet"}) + "\n"

        mock_chat_service.chat = AsyncMock(return_value=mock_stream())

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Test message",
                    "stream": True,
                },
            )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        # Streaming content would be tested with actual streaming client


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
