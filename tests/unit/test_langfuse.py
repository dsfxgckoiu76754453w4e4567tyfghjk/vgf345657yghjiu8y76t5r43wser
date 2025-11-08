"""Comprehensive unit tests for Langfuse observability service and client."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.langfuse_service import LangfuseService
from app.core.langfuse_client import (
    get_langfuse_client,
    flush_langfuse,
    trace_request,
    trace_span,
    log_event,
    score_trace,
    score_observation,
    NoOpLangfuse,
    NoOpSpan,
)


# ============================================================================
# LangfuseService Tests
# ============================================================================


class TestLangfuseServiceInitialization:
    """Test cases for Langfuse service initialization."""

    @patch('app.services.langfuse_service.get_settings')
    def test_initialization_without_credentials(self, mock_settings):
        """Test that service initializes without credentials (no-op mode)."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings_obj.langfuse_secret_key = None
        mock_settings.return_value = mock_settings_obj

        # Act
        service = LangfuseService()

        # Assert
        assert service.public_key is None
        assert service.secret_key is None
        assert service.client is None

    @patch('app.services.langfuse_service.get_settings')
    @patch('app.services.langfuse_service.Langfuse')
    def test_initialization_with_credentials(self, mock_langfuse, mock_settings):
        """Test that service initializes properly with credentials."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test_123"
        mock_settings_obj.langfuse_secret_key = "sk_test_456"
        mock_settings_obj.langfuse_host = "https://cloud.langfuse.com"
        mock_settings.return_value = mock_settings_obj

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        # Act
        service = LangfuseService()

        # Assert
        assert service.public_key == "pk_test_123"
        assert service.secret_key == "sk_test_456"
        assert service.host == "https://cloud.langfuse.com"
        assert service.client == mock_client
        mock_langfuse.assert_called_once_with(
            public_key="pk_test_123",
            secret_key="sk_test_456",
            host="https://cloud.langfuse.com",
        )

    @patch('app.services.langfuse_service.get_settings')
    def test_initialization_langfuse_not_installed(self, mock_settings):
        """Test graceful handling when Langfuse package is not installed."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test_123"
        mock_settings_obj.langfuse_secret_key = "sk_test_456"
        mock_settings.return_value = mock_settings_obj

        # Act - Import error will be caught
        with patch.dict('sys.modules', {'langfuse': None}):
            service = LangfuseService()

        # Assert - Should not crash, client should be None
        # (In real scenario, ImportError is caught and client remains None)


class TestLangfuseServiceTraceManagement:
    """Test cases for trace management."""

    @patch('app.services.langfuse_service.get_settings')
    def test_create_trace_without_client(self, mock_settings):
        """Test trace creation returns dummy ID when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        user_id = uuid4()

        # Act
        trace_id = service.create_trace(
            name="test_trace",
            user_id=user_id,
            session_id="session_123",
            metadata={"key": "value"},
        )

        # Assert
        assert trace_id is not None
        assert isinstance(trace_id, str)
        # Should be valid UUID format
        assert len(trace_id) == 36

    @patch('app.services.langfuse_service.get_settings')
    def test_create_trace_with_client(self, mock_settings):
        """Test trace creation with configured client."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings_obj.langfuse_secret_key = "sk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_trace = MagicMock()
        mock_trace.id = "trace_abc123"
        service.client = MagicMock()
        service.client.trace.return_value = mock_trace

        user_id = uuid4()

        # Act
        trace_id = service.create_trace(
            name="chat_query",
            user_id=user_id,
            session_id="session_456",
            metadata={"tool": "ahkam"},
        )

        # Assert
        assert trace_id == "trace_abc123"
        service.client.trace.assert_called_once_with(
            name="chat_query",
            user_id=str(user_id),
            session_id="session_456",
            metadata={"tool": "ahkam"},
        )

    @patch('app.services.langfuse_service.get_settings')
    def test_create_trace_handles_errors(self, mock_settings):
        """Test trace creation handles errors gracefully."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()
        service.client.trace.side_effect = Exception("API Error")

        # Act
        trace_id = service.create_trace(name="test_trace")

        # Assert - Should return dummy UUID instead of crashing
        assert trace_id is not None
        assert isinstance(trace_id, str)


class TestLangfuseServiceGenerationTracking:
    """Test cases for LLM generation tracking."""

    @patch('app.services.langfuse_service.get_settings')
    def test_track_generation_without_client(self, mock_settings):
        """Test generation tracking is no-op when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()

        # Act - Should not raise exception
        service.track_generation(
            trace_id="trace_123",
            name="response_generation",
            model="claude-3-sonnet",
            input_text="What is Islam?",
            output_text="Islam is a monotheistic religion...",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=2500,
        )

        # Assert - No exception raised

    @patch('app.services.langfuse_service.get_settings')
    def test_track_generation_with_client(self, mock_settings):
        """Test generation tracking with configured client."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.track_generation(
            trace_id="trace_123",
            name="intent_detection",
            model="gpt-4",
            input_text="Generate an image",
            output_text='{"intent": "image_generation"}',
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70,
            latency_ms=1200,
            metadata={"provider": "openai"},
        )

        # Assert
        service.client.generation.assert_called_once_with(
            trace_id="trace_123",
            name="intent_detection",
            model="gpt-4",
            input="Generate an image",
            output='{"intent": "image_generation"}',
            usage={
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70,
            },
            metadata={
                "provider": "openai",
                "latency_ms": 1200,
            },
        )

    @patch('app.services.langfuse_service.get_settings')
    def test_track_generation_handles_errors(self, mock_settings):
        """Test generation tracking handles errors gracefully."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()
        service.client.generation.side_effect = Exception("Network error")

        # Act - Should not raise exception
        service.track_generation(
            trace_id="trace_123",
            name="test",
            model="model",
            input_text="input",
            output_text="output",
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20,
            latency_ms=100,
        )

        # Assert - No exception raised


class TestLangfuseServiceSpanTracking:
    """Test cases for span tracking."""

    @patch('app.services.langfuse_service.get_settings')
    def test_create_span_without_client(self, mock_settings):
        """Test span creation returns dummy ID when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()

        # Act
        span_id = service.create_span(
            trace_id="trace_123",
            name="vector_search",
            metadata={"collection": "hadith"},
        )

        # Assert
        assert span_id is not None
        assert isinstance(span_id, str)

    @patch('app.services.langfuse_service.get_settings')
    def test_create_span_with_client(self, mock_settings):
        """Test span creation with configured client."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_span = MagicMock()
        mock_span.id = "span_xyz789"
        service.client = MagicMock()
        service.client.span.return_value = mock_span

        start_time = datetime.utcnow()

        # Act
        span_id = service.create_span(
            trace_id="trace_123",
            name="ahkam_tool_call",
            start_time=start_time,
            metadata={"tool": "ahkam", "query": "prayer times"},
        )

        # Assert
        assert span_id == "span_xyz789"
        service.client.span.assert_called_once()
        call_args = service.client.span.call_args[1]
        assert call_args['trace_id'] == "trace_123"
        assert call_args['name'] == "ahkam_tool_call"
        assert call_args['start_time'] == start_time
        assert call_args['metadata'] == {"tool": "ahkam", "query": "prayer times"}


class TestLangfuseServiceScoreTracking:
    """Test cases for score tracking."""

    @patch('app.services.langfuse_service.get_settings')
    def test_track_score_without_client(self, mock_settings):
        """Test score tracking is no-op when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()

        # Act - Should not raise exception
        service.track_score(
            trace_id="trace_123",
            name="user_feedback",
            value=1.0,
            comment="Helpful response",
        )

        # Assert - No exception raised

    @patch('app.services.langfuse_service.get_settings')
    def test_track_score_with_client(self, mock_settings):
        """Test score tracking with configured client."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.track_score(
            trace_id="trace_456",
            name="response_quality",
            value=0.95,
            comment="High quality response",
        )

        # Assert
        service.client.score.assert_called_once_with(
            trace_id="trace_456",
            name="response_quality",
            value=0.95,
            comment="High quality response",
        )


class TestLangfuseServiceEventTracking:
    """Test cases for event tracking."""

    @patch('app.services.langfuse_service.get_settings')
    def test_track_event_without_client(self, mock_settings):
        """Test event tracking is no-op when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()

        # Act - Should not raise exception
        service.track_event(
            trace_id="trace_123",
            name="cache_hit",
            metadata={"cache_key": "user_123_conversation"},
        )

        # Assert - No exception raised

    @patch('app.services.langfuse_service.get_settings')
    def test_track_event_with_client(self, mock_settings):
        """Test event tracking with configured client."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.track_event(
            trace_id="trace_789",
            name="tool_call",
            metadata={"tool": "hadith_search", "results": 5},
        )

        # Assert
        service.client.event.assert_called_once_with(
            trace_id="trace_789",
            name="tool_call",
            metadata={"tool": "hadith_search", "results": 5},
        )


class TestLangfuseServiceUtilityMethods:
    """Test cases for utility methods."""

    @patch('app.services.langfuse_service.get_settings')
    def test_flush_without_client(self, mock_settings):
        """Test flush is no-op when client not configured."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = None
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()

        # Act - Should not raise exception
        service.flush()

        # Assert - No exception raised

    @patch('app.services.langfuse_service.get_settings')
    def test_flush_with_client(self, mock_settings):
        """Test flush calls client flush method."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.flush()

        # Assert
        service.client.flush.assert_called_once()

    @patch('app.services.langfuse_service.get_settings')
    def test_shutdown_with_client(self, mock_settings):
        """Test shutdown calls client shutdown method."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.shutdown()

        # Assert
        service.client.shutdown.assert_called_once()


class TestLangfuseServiceConvenienceMethods:
    """Test cases for convenience methods."""

    @patch('app.services.langfuse_service.get_settings')
    def test_track_chat_query(self, mock_settings):
        """Test convenience method for tracking chat queries."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_trace = MagicMock()
        mock_trace.id = "trace_chat_123"
        service.client = MagicMock()
        service.client.trace.return_value = mock_trace

        user_id = uuid4()

        # Act
        trace_id = service.track_chat_query(
            user_id=user_id,
            session_id="conv_456",
            query="What are the pillars of Islam?",
            response="The five pillars of Islam are...",
            model="claude-3-sonnet",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=2000,
            tools_used=["ahkam_tool"],
            rag_chunks_retrieved=5,
        )

        # Assert
        assert trace_id == "trace_chat_123"
        service.client.trace.assert_called_once()
        service.client.generation.assert_called_once()

    @patch('app.services.langfuse_service.get_settings')
    def test_track_rag_retrieval(self, mock_settings):
        """Test convenience method for tracking RAG retrieval."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_span = MagicMock()
        mock_span.id = "span_rag_123"
        service.client = MagicMock()
        service.client.span.return_value = mock_span

        # Act
        service.track_rag_retrieval(
            trace_id="trace_123",
            query="Islamic history",
            chunks_retrieved=10,
            top_k=10,
            retrieval_latency_ms=150,
        )

        # Assert
        service.client.span.assert_called_once()
        call_args = service.client.span.call_args[1]
        assert call_args['trace_id'] == "trace_123"
        assert call_args['name'] == "rag_retrieval"
        assert call_args['metadata']['chunks_retrieved'] == 10
        assert call_args['metadata']['top_k'] == 10

    @patch('app.services.langfuse_service.get_settings')
    def test_track_tool_call_success(self, mock_settings):
        """Test tracking successful tool call."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_span = MagicMock()
        service.client = MagicMock()
        service.client.span.return_value = mock_span

        # Act
        service.track_tool_call(
            trace_id="trace_123",
            tool_name="ahkam",
            tool_input={"query": "prayer times"},
            tool_output={"result": "Prayer times for today..."},
            latency_ms=500,
            success=True,
        )

        # Assert
        service.client.span.assert_called_once()
        call_args = service.client.span.call_args[1]
        assert call_args['name'] == "tool_call_ahkam"
        assert call_args['metadata']['success'] is True
        assert call_args['metadata']['error'] is None

    @patch('app.services.langfuse_service.get_settings')
    def test_track_tool_call_failure(self, mock_settings):
        """Test tracking failed tool call."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        mock_span = MagicMock()
        service.client = MagicMock()
        service.client.span.return_value = mock_span

        # Act
        service.track_tool_call(
            trace_id="trace_123",
            tool_name="math",
            tool_input={"expression": "invalid"},
            tool_output=None,
            latency_ms=100,
            success=False,
            error="Invalid expression",
        )

        # Assert
        call_args = service.client.span.call_args[1]
        assert call_args['metadata']['success'] is False
        assert call_args['metadata']['error'] == "Invalid expression"

    @patch('app.services.langfuse_service.get_settings')
    def test_track_user_feedback(self, mock_settings):
        """Test tracking user feedback."""
        # Arrange
        mock_settings_obj = MagicMock()
        mock_settings_obj.langfuse_public_key = "pk_test"
        mock_settings.return_value = mock_settings_obj

        service = LangfuseService()
        service.client = MagicMock()

        # Act
        service.track_user_feedback(
            trace_id="trace_123",
            feedback_type="thumbs_up",
            value=1.0,
            comment="Very helpful answer",
        )

        # Assert
        service.client.score.assert_called_once_with(
            trace_id="trace_123",
            name="thumbs_up",
            value=1.0,
            comment="Very helpful answer",
        )


# ============================================================================
# Langfuse Client Tests
# ============================================================================


class TestLangfuseClientInitialization:
    """Test cases for Langfuse client initialization."""

    @patch('app.core.langfuse_client.settings')
    def test_get_langfuse_client_when_enabled(self, mock_settings):
        """Test getting client when Langfuse is enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True
        mock_settings.langfuse_public_key = "pk_test"
        mock_settings.langfuse_secret_key = "sk_test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"
        mock_settings.environment = "dev"

        # Act
        client = get_langfuse_client()

        # Assert
        assert client is not None

    @patch('app.core.langfuse_client.settings')
    def test_get_langfuse_client_when_disabled(self, mock_settings):
        """Test getting no-op client when Langfuse is disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False

        # Act
        client = get_langfuse_client()

        # Assert
        assert isinstance(client, NoOpLangfuse)


class TestNoOpLangfuseClient:
    """Test cases for no-op Langfuse client."""

    def test_noop_client_methods_do_nothing(self):
        """Test that no-op client methods execute without errors."""
        # Arrange
        client = NoOpLangfuse()

        # Act & Assert - Should not raise exceptions
        span = client.start_as_current_span("test")
        assert isinstance(span, NoOpSpan)

        client.update_current_trace(metadata={"key": "value"})
        client.flush()

        decorator = client.trace(name="test")
        assert callable(decorator)

    def test_noop_span_context_manager(self):
        """Test no-op span as context manager."""
        # Arrange
        span = NoOpSpan()

        # Act & Assert
        with span as s:
            assert s is span
            s.update_trace(metadata={"key": "value"})
            s.span(name="nested")
            s.generation(name="gen")
            s.event(name="event")


class TestTraceRequestContextManager:
    """Test cases for trace_request context manager."""

    @patch('app.core.langfuse_client.settings')
    def test_trace_request_when_disabled(self, mock_settings):
        """Test trace_request returns no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False

        # Act
        with trace_request("test_request") as trace:
            # Assert
            assert isinstance(trace, NoOpSpan)

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_trace_request_when_enabled(self, mock_client, mock_settings):
        """Test trace_request creates proper trace when enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True
        mock_settings.environment = "dev"
        mock_settings.is_production = False

        mock_trace = MagicMock()
        mock_client.trace.return_value = mock_trace

        # Act
        with trace_request(
            name="chat_request",
            user_id="user_123",
            session_id="session_456",
            metadata={"endpoint": "/api/v1/chat"},
            tags=["chat", "api"],
        ) as trace:
            # Assert
            assert trace is mock_trace
            mock_client.trace.assert_called_once()
            call_args = mock_client.trace.call_args[1]
            assert call_args['name'] == "chat_request"
            assert call_args['user_id'] == "user_123"
            assert call_args['session_id'] == "session_456"
            assert "environment" in call_args['metadata']
            assert "dev" in call_args['tags']

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_trace_request_handles_exceptions(self, mock_client, mock_settings):
        """Test trace_request logs errors to trace."""
        # Arrange
        mock_settings.langfuse_enabled = True
        mock_settings.environment = "dev"
        mock_settings.is_production = False

        mock_trace = MagicMock()
        mock_client.trace.return_value = mock_trace

        # Act & Assert
        with pytest.raises(ValueError):
            with trace_request("test_request") as trace:
                raise ValueError("Test error")

        # Assert - Should have called update with error
        mock_trace.update.assert_called()


class TestTraceSpanContextManager:
    """Test cases for trace_span context manager."""

    @patch('app.core.langfuse_client.settings')
    def test_trace_span_when_disabled(self, mock_settings):
        """Test trace_span returns no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False
        mock_trace = MagicMock()

        # Act
        with trace_span(mock_trace, "test_span") as span:
            # Assert
            assert isinstance(span, NoOpSpan)

    @patch('app.core.langfuse_client.settings')
    def test_trace_span_creates_regular_span(self, mock_settings):
        """Test trace_span creates regular span."""
        # Arrange
        mock_settings.langfuse_enabled = True

        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_trace.span.return_value = mock_span

        # Act
        with trace_span(
            mock_trace,
            "database_query",
            metadata={"table": "users"},
            input_data={"query": "SELECT *"},
        ) as span:
            # Assert
            assert span is mock_span
            mock_trace.span.assert_called_once()
            call_args = mock_trace.span.call_args[1]
            assert call_args['name'] == "database_query"
            assert call_args['metadata'] == {"table": "users"}

    @patch('app.core.langfuse_client.settings')
    def test_trace_span_creates_generation_span(self, mock_settings):
        """Test trace_span creates generation span."""
        # Arrange
        mock_settings.langfuse_enabled = True

        mock_trace = MagicMock()
        mock_generation = MagicMock()
        mock_trace.generation.return_value = mock_generation

        # Act
        with trace_span(
            mock_trace,
            "llm_call",
            span_type="generation",
            input_data="What is Islam?",
        ) as span:
            # Assert
            assert span is mock_generation
            mock_trace.generation.assert_called_once()

    @patch('app.core.langfuse_client.settings')
    def test_trace_span_creates_event(self, mock_settings):
        """Test trace_span creates event (no-op span returned)."""
        # Arrange
        mock_settings.langfuse_enabled = True

        mock_trace = MagicMock()

        # Act
        with trace_span(
            mock_trace,
            "cache_hit",
            span_type="event",
            metadata={"cache_key": "user_123"},
        ) as span:
            # Assert
            assert isinstance(span, NoOpSpan)
            mock_trace.event.assert_called_once()

    @patch('app.core.langfuse_client.settings')
    def test_trace_span_updates_with_output(self, mock_settings):
        """Test trace_span updates span with output data."""
        # Arrange
        mock_settings.langfuse_enabled = True

        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_trace.span.return_value = mock_span

        # Act
        with trace_span(mock_trace, "test_span", output_data={"result": "success"}):
            pass

        # Assert
        mock_span.update.assert_called_with(output={"result": "success"})
        mock_span.end.assert_called_once()


class TestLogEvent:
    """Test cases for log_event function."""

    @patch('app.core.langfuse_client.settings')
    def test_log_event_when_disabled(self, mock_settings):
        """Test log_event is no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False
        mock_trace = MagicMock()

        # Act
        log_event(mock_trace, "test_event")

        # Assert
        mock_trace.event.assert_not_called()

    @patch('app.core.langfuse_client.settings')
    def test_log_event_when_enabled(self, mock_settings):
        """Test log_event logs event when enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True
        mock_trace = MagicMock()

        # Act
        log_event(
            mock_trace,
            "tool_executed",
            metadata={"tool": "ahkam", "duration_ms": 500},
            input_data={"query": "prayer times"},
        )

        # Assert
        mock_trace.event.assert_called_once_with(
            name="tool_executed",
            metadata={"tool": "ahkam", "duration_ms": 500},
            input={"query": "prayer times"},
        )


class TestScoreTrace:
    """Test cases for score_trace function."""

    @patch('app.core.langfuse_client.settings')
    def test_score_trace_when_disabled(self, mock_settings):
        """Test score_trace is no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False

        # Act
        score_trace(
            trace_id="trace_123",
            name="user_feedback",
            value=1.0,
        )

        # Assert - Should not raise exception

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_score_trace_when_enabled(self, mock_client, mock_settings):
        """Test score_trace adds score when enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True

        # Act
        score_trace(
            trace_id="trace_456",
            name="accuracy",
            value=0.95,
            comment="High accuracy response",
            data_type="NUMERIC",
        )

        # Assert
        mock_client.score.assert_called_once_with(
            trace_id="trace_456",
            name="accuracy",
            value=0.95,
            comment="High accuracy response",
            data_type="NUMERIC",
        )

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_score_trace_handles_errors(self, mock_client, mock_settings):
        """Test score_trace handles errors gracefully."""
        # Arrange
        mock_settings.langfuse_enabled = True
        mock_client.score.side_effect = Exception("API Error")

        # Act - Should not raise exception
        score_trace(
            trace_id="trace_123",
            name="test_score",
            value=1.0,
        )

        # Assert - Error was logged, no exception raised


class TestScoreObservation:
    """Test cases for score_observation function."""

    @patch('app.core.langfuse_client.settings')
    def test_score_observation_when_disabled(self, mock_settings):
        """Test score_observation is no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False

        # Act
        score_observation(
            observation_id="obs_123",
            name="quality",
            value=0.9,
        )

        # Assert - Should not raise exception

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_score_observation_when_enabled(self, mock_client, mock_settings):
        """Test score_observation adds score when enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True

        # Act
        score_observation(
            observation_id="obs_789",
            name="relevance",
            value=0.85,
            comment="Relevant response",
        )

        # Assert
        mock_client.score.assert_called_once_with(
            observation_id="obs_789",
            name="relevance",
            value=0.85,
            comment="Relevant response",
            data_type="NUMERIC",
        )


class TestFlushLangfuse:
    """Test cases for flush_langfuse function."""

    @patch('app.core.langfuse_client.settings')
    def test_flush_langfuse_when_disabled(self, mock_settings):
        """Test flush is no-op when disabled."""
        # Arrange
        mock_settings.langfuse_enabled = False

        # Act
        flush_langfuse()

        # Assert - Should not raise exception

    @patch('app.core.langfuse_client.settings')
    @patch('app.core.langfuse_client.langfuse_client')
    def test_flush_langfuse_when_enabled(self, mock_client, mock_settings):
        """Test flush calls client flush when enabled."""
        # Arrange
        mock_settings.langfuse_enabled = True

        # Act
        flush_langfuse()

        # Assert
        mock_client.flush.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
