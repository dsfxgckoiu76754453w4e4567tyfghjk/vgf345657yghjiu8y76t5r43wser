"""Langfuse observability service for LLM monitoring."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LangfuseService:
    """Service for LLM observability using Langfuse."""

    def __init__(self):
        """Initialize Langfuse service."""
        # Langfuse configuration
        self.public_key = getattr(settings, "langfuse_public_key", None)
        self.secret_key = getattr(settings, "langfuse_secret_key", None)
        self.host = getattr(settings, "langfuse_host", "https://cloud.langfuse.com")

        # Initialize Langfuse client
        self.client = None
        if self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse

                self.client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
                logger.info("langfuse_initialized", host=self.host)
            except ImportError:
                logger.warn("langfuse_not_installed", message="Install with: pip install langfuse")
            except Exception as e:
                logger.error("langfuse_initialization_failed", error=str(e))
        else:
            logger.warn("langfuse_not_configured", message="Langfuse keys not provided")

    # ========================================================================
    # Trace Management
    # ========================================================================

    def create_trace(
        self,
        name: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Create a new trace for tracking LLM interactions.

        A trace represents a single user request/response cycle.

        Args:
            name: Trace name (e.g., "chat_query", "document_search")
            user_id: User ID
            session_id: Session ID
            metadata: Additional metadata

        Returns:
            Trace ID
        """
        if not self.client:
            return str(uuid4())  # Return dummy ID if Langfuse not configured

        try:
            trace = self.client.trace(
                name=name,
                user_id=str(user_id) if user_id else None,
                session_id=session_id,
                metadata=metadata or {},
            )

            logger.info("langfuse_trace_created", trace_id=trace.id, name=name)
            return trace.id

        except Exception as e:
            logger.error("langfuse_trace_creation_failed", error=str(e))
            return str(uuid4())

    # ========================================================================
    # Generation Tracking (LLM Calls)
    # ========================================================================

    def track_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_text: str,
        output_text: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Track an LLM generation (API call).

        Args:
            trace_id: Trace ID
            name: Generation name (e.g., "query_classification", "response_generation")
            model: Model name (e.g., "gpt-4", "claude-3-sonnet")
            input_text: Input prompt
            output_text: Generated output
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens used
            latency_ms: Latency in milliseconds
            metadata: Additional metadata
        """
        if not self.client:
            return

        try:
            self.client.generation(
                trace_id=trace_id,
                name=name,
                model=model,
                input=input_text,
                output=output_text,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                metadata={
                    **(metadata or {}),
                    "latency_ms": latency_ms,
                },
            )

            logger.info(
                "langfuse_generation_tracked",
                trace_id=trace_id,
                model=model,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error("langfuse_generation_tracking_failed", error=str(e))

    # ========================================================================
    # Span Tracking (Operations within a Trace)
    # ========================================================================

    def create_span(
        self,
        trace_id: str,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Create a span within a trace.

        Spans represent operations like RAG retrieval, tool calls, etc.

        Args:
            trace_id: Parent trace ID
            name: Span name (e.g., "vector_search", "ahkam_tool_call")
            start_time: Start timestamp
            end_time: End timestamp
            metadata: Additional metadata

        Returns:
            Span ID
        """
        if not self.client:
            return str(uuid4())

        try:
            span = self.client.span(
                trace_id=trace_id,
                name=name,
                start_time=start_time or datetime.utcnow(),
                end_time=end_time,
                metadata=metadata or {},
            )

            logger.info("langfuse_span_created", trace_id=trace_id, span_id=span.id, name=name)
            return span.id

        except Exception as e:
            logger.error("langfuse_span_creation_failed", error=str(e))
            return str(uuid4())

    # ========================================================================
    # Score Tracking (Quality Metrics)
    # ========================================================================

    def track_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ) -> None:
        """
        Track a score/metric for a trace.

        Useful for tracking:
        - User feedback (thumbs up/down)
        - Response quality scores
        - Relevance scores
        - Safety scores

        Args:
            trace_id: Trace ID
            name: Score name (e.g., "user_feedback", "response_quality")
            value: Score value (typically 0-1 or 1-5)
            comment: Optional comment
        """
        if not self.client:
            return

        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )

            logger.info("langfuse_score_tracked", trace_id=trace_id, name=name, value=value)

        except Exception as e:
            logger.error("langfuse_score_tracking_failed", error=str(e))

    # ========================================================================
    # Event Tracking
    # ========================================================================

    def track_event(
        self,
        trace_id: str,
        name: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Track an event within a trace.

        Events represent discrete occurrences like:
        - Tool calls
        - Cache hits/misses
        - Errors
        - Custom events

        Args:
            trace_id: Trace ID
            name: Event name
            metadata: Event metadata
        """
        if not self.client:
            return

        try:
            self.client.event(
                trace_id=trace_id,
                name=name,
                metadata=metadata or {},
            )

            logger.info("langfuse_event_tracked", trace_id=trace_id, name=name)

        except Exception as e:
            logger.error("langfuse_event_tracking_failed", error=str(e))

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def flush(self) -> None:
        """Flush all pending events to Langfuse."""
        if not self.client:
            return

        try:
            self.client.flush()
            logger.info("langfuse_flushed")
        except Exception as e:
            logger.error("langfuse_flush_failed", error=str(e))

    def shutdown(self) -> None:
        """Shutdown Langfuse client."""
        if not self.client:
            return

        try:
            self.client.shutdown()
            logger.info("langfuse_shutdown")
        except Exception as e:
            logger.error("langfuse_shutdown_failed", error=str(e))

    # ========================================================================
    # Convenience Methods for Common Operations
    # ========================================================================

    def track_chat_query(
        self,
        user_id: UUID,
        session_id: str,
        query: str,
        response: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        tools_used: Optional[list[str]] = None,
        rag_chunks_retrieved: Optional[int] = None,
    ) -> str:
        """
        Track a complete chat query with all metadata.

        Args:
            user_id: User ID
            session_id: Session ID
            query: User query
            response: Chatbot response
            model: LLM model used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            latency_ms: Total latency
            tools_used: List of tools used
            rag_chunks_retrieved: Number of RAG chunks retrieved

        Returns:
            Trace ID
        """
        # Create trace
        trace_id = self.create_trace(
            name="chat_query",
            user_id=user_id,
            session_id=session_id,
            metadata={
                "tools_used": tools_used or [],
                "rag_chunks_retrieved": rag_chunks_retrieved,
            },
        )

        # Track generation
        self.track_generation(
            trace_id=trace_id,
            name="response_generation",
            model=model,
            input_text=query,
            output_text=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
        )

        return trace_id

    def track_rag_retrieval(
        self,
        trace_id: str,
        query: str,
        chunks_retrieved: int,
        top_k: int,
        retrieval_latency_ms: int,
    ) -> None:
        """
        Track RAG retrieval operation.

        Args:
            trace_id: Parent trace ID
            query: Search query
            chunks_retrieved: Number of chunks retrieved
            top_k: Top-k parameter
            retrieval_latency_ms: Retrieval latency
        """
        self.create_span(
            trace_id=trace_id,
            name="rag_retrieval",
            metadata={
                "query": query[:100],  # Truncate for readability
                "chunks_retrieved": chunks_retrieved,
                "top_k": top_k,
                "latency_ms": retrieval_latency_ms,
            },
        )

    def track_tool_call(
        self,
        trace_id: str,
        tool_name: str,
        tool_input: Any,
        tool_output: Any,
        latency_ms: int,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Track a tool call (Ahkam, Hadith, DateTime, Math).

        Args:
            trace_id: Parent trace ID
            tool_name: Tool name
            tool_input: Tool input
            tool_output: Tool output
            latency_ms: Tool execution latency
            success: Whether tool call succeeded
            error: Error message if failed
        """
        self.create_span(
            trace_id=trace_id,
            name=f"tool_call_{tool_name}",
            metadata={
                "tool_name": tool_name,
                "input": str(tool_input)[:200],  # Truncate
                "output": str(tool_output)[:200] if success else None,
                "latency_ms": latency_ms,
                "success": success,
                "error": error,
            },
        )

    def track_user_feedback(
        self,
        trace_id: str,
        feedback_type: str,  # "thumbs_up", "thumbs_down", "rating"
        value: float,  # 1 for thumbs up, 0 for thumbs down, 1-5 for rating
        comment: Optional[str] = None,
    ) -> None:
        """
        Track user feedback on a response.

        Args:
            trace_id: Trace ID
            feedback_type: Type of feedback
            value: Feedback value
            comment: Optional user comment
        """
        self.track_score(
            trace_id=trace_id,
            name=feedback_type,
            value=value,
            comment=comment,
        )
