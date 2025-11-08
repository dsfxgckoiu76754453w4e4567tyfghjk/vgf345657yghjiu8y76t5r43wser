"""Langfuse client initialization and utilities for tracing."""

from typing import Any, Optional
from contextlib import contextmanager
import os

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize Langfuse client when enabled
if settings.langfuse_enabled:
    from langfuse import Langfuse

    # Initialize Langfuse client with optional environment-specific project
    # If langfuse_project_name is set, it will use environment-specific projects
    # e.g., "wisqu-dev", "wisqu-stage", "wisqu-prod"
    langfuse_kwargs = {
        "public_key": settings.langfuse_public_key,
        "secret_key": settings.langfuse_secret_key,
        "host": settings.langfuse_host,
    }

    # Add environment-specific release tag
    if hasattr(settings, "langfuse_release"):
        langfuse_kwargs["release"] = f"{settings.langfuse_release}-{settings.environment}"

    langfuse_client = Langfuse(**langfuse_kwargs)

    logger.info(
        "langfuse_client_initialized",
        host=settings.langfuse_host,
        environment=settings.environment,
        enabled=True
    )
else:
    # Create a no-op client when disabled
    class NoOpLangfuse:
        """No-op Langfuse client when tracing is disabled."""

        def start_as_current_span(self, *args, **kwargs):
            """No-op context manager."""
            return NoOpSpan()

        def update_current_trace(self, *args, **kwargs):
            """No-op trace update."""
            pass

        def flush(self):
            """No-op flush."""
            pass

        def trace(self, *args, **kwargs):
            """No-op trace decorator."""
            def decorator(func):
                return func
            return decorator

    class NoOpSpan:
        """No-op span when tracing is disabled."""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def update_trace(self, *args, **kwargs):
            """No-op update."""
            pass

        def span(self, *args, **kwargs):
            """No-op span."""
            return NoOpSpan()

        def generation(self, *args, **kwargs):
            """No-op generation."""
            return NoOpSpan()

        def event(self, *args, **kwargs):
            """No-op event."""
            pass

    langfuse_client = NoOpLangfuse()
    logger.info("langfuse_disabled", enabled=False)


def get_langfuse_client() -> Any:
    """
    Get the Langfuse client instance.

    Returns:
        Langfuse client or NoOp client if disabled
    """
    return langfuse_client


def flush_langfuse():
    """
    Flush pending Langfuse events.

    Call this in short-lived applications or before shutdown
    to ensure all events are sent.
    """
    if settings.langfuse_enabled:
        langfuse_client.flush()
        logger.debug("langfuse_flushed")


@contextmanager
def trace_request(
    name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    tags: Optional[list[str]] = None,
):
    """
    Context manager for tracing a complete request flow.

    Usage:
        with trace_request(
            name="chat-request",
            user_id=str(user.id),
            session_id=str(conversation.id),
            metadata={"endpoint": "/api/v1/chat"},
            tags=["chat", "api"]
        ) as trace:
            # Your code here
            result = await process_request()

            # Update trace with results
            trace.update_trace(
                output=result,
                metadata={"response_size": len(result)}
            )

    Args:
        name: Name of the trace
        user_id: User ID for user-level analytics
        session_id: Session ID for grouping related requests
        metadata: Additional metadata
        tags: Tags for filtering and organization

    Yields:
        Trace/Span object for updating during execution
    """
    if not settings.langfuse_enabled:
        # Return no-op context manager
        yield NoOpSpan()
        return

    # Add environment to metadata and tags
    env_metadata = {
        "environment": settings.environment,
        "is_production": settings.is_production,
        **(metadata or {}),
    }

    env_tags = [
        settings.environment,  # Add environment as tag
        *(tags or []),
    ]

    trace = langfuse_client.trace(
        name=name,
        user_id=user_id,
        session_id=session_id,
        metadata=env_metadata,
        tags=env_tags,
    )

    try:
        yield trace
    except Exception as e:
        # Log error to trace
        trace.update(
            metadata={
                **(metadata or {}),
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )
        raise
    finally:
        # Ensure trace is finalized
        if settings.langfuse_enabled:
            trace.update()


@contextmanager
def trace_span(
    parent_trace: Any,
    name: str,
    span_type: str = "span",  # "span", "generation", "event"
    metadata: Optional[dict[str, Any]] = None,
    input_data: Optional[Any] = None,
    output_data: Optional[Any] = None,
):
    """
    Context manager for adding a span within a trace.

    Usage:
        with trace_request("my-request") as trace:
            with trace_span(trace, "database-query", metadata={"table": "users"}):
                result = await db.execute(query)

            with trace_span(trace, "api-call", span_type="generation"):
                response = await api.call()

    Args:
        parent_trace: Parent trace or span object
        name: Name of the span
        span_type: Type of span ("span", "generation", "event")
        metadata: Additional metadata
        input_data: Input data for the span
        output_data: Output data for the span

    Yields:
        Span object
    """
    if not settings.langfuse_enabled:
        yield NoOpSpan()
        return

    # Create span based on type
    if span_type == "generation":
        span = parent_trace.generation(
            name=name,
            metadata=metadata or {},
            input=input_data,
        )
    elif span_type == "event":
        parent_trace.event(
            name=name,
            metadata=metadata or {},
            input=input_data,
        )
        yield NoOpSpan()
        return
    else:
        span = parent_trace.span(
            name=name,
            metadata=metadata or {},
            input=input_data,
        )

    try:
        yield span
    except Exception as e:
        # Log error to span
        span.update(
            metadata={
                **(metadata or {}),
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )
        raise
    finally:
        # Update span with output if provided
        if output_data is not None:
            span.update(output=output_data)
        span.end()


def log_event(
    trace: Any,
    name: str,
    metadata: Optional[dict[str, Any]] = None,
    input_data: Optional[Any] = None,
):
    """
    Log a simple event within a trace.

    Use this for logging important milestones or events that don't
    need to track duration (unlike spans).

    Args:
        trace: Parent trace object
        name: Name of the event
        metadata: Event metadata
        input_data: Event input data
    """
    if not settings.langfuse_enabled:
        return

    trace.event(
        name=name,
        metadata=metadata or {},
        input=input_data,
    )


def score_trace(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
    data_type: str = "NUMERIC",
):
    """
    Add a score to a trace in Langfuse.

    Use this for user feedback, evaluation scores, or any metrics
    you want to track for a specific trace.

    Args:
        trace_id: Langfuse trace ID
        name: Name of the score (e.g., "user-feedback", "accuracy")
        value: Numeric value of the score
        comment: Optional comment explaining the score
        data_type: Type of score ("NUMERIC", "CATEGORICAL", "BOOLEAN")

    Example:
        # Add user feedback score
        score_trace(
            trace_id="abc-123",
            name="user-feedback",
            value=1.0,  # 1 for thumbs up, 0 for thumbs down
            comment="User found response helpful"
        )
    """
    if not settings.langfuse_enabled:
        logger.debug("langfuse_disabled_skipping_score")
        return

    try:
        langfuse_client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
            data_type=data_type,
        )
        logger.info(
            "langfuse_score_added",
            trace_id=trace_id,
            score_name=name,
            value=value,
        )
    except Exception as e:
        logger.error(
            "langfuse_score_error",
            trace_id=trace_id,
            error=str(e),
        )


def score_observation(
    observation_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
    data_type: str = "NUMERIC",
):
    """
    Add a score to a specific observation (span/generation) in Langfuse.

    Args:
        observation_id: Langfuse observation ID
        name: Name of the score
        value: Numeric value of the score
        comment: Optional comment
        data_type: Type of score
    """
    if not settings.langfuse_enabled:
        logger.debug("langfuse_disabled_skipping_score")
        return

    try:
        langfuse_client.score(
            observation_id=observation_id,
            name=name,
            value=value,
            comment=comment,
            data_type=data_type,
        )
        logger.info(
            "langfuse_observation_score_added",
            observation_id=observation_id,
            score_name=name,
            value=value,
        )
    except Exception as e:
        logger.error(
            "langfuse_observation_score_error",
            observation_id=observation_id,
            error=str(e),
        )
