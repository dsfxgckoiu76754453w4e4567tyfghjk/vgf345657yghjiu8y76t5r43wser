"""
Celery tasks for background processing.

This package contains all async tasks organized by priority:

High Priority (User-facing):
- chat: Chat message processing with LLM
- images: Image generation
- asr: Audio transcription
- web_search: Web search operations

Medium Priority (Background):
- embeddings: Batch embedding generation
- storage: File uploads and processing
- promotion: Environment promotion
- dataset: Dataset creation

Low Priority (Fire-and-forget):
- email: Email sending
- langfuse_tasks: Observability traces
- cleanup: File and data cleanup
- leaderboard: Ranking calculations
"""

# Import all tasks to ensure they're registered with Celery
from app.tasks import (  # noqa: F401
    asr,
    chat,
    cleanup,
    dataset,
    email,
    embeddings,
    images,
    langfuse_tasks,
    leaderboard,
    promotion,
    storage,
    web_search,
)

__all__ = [
    "chat",
    "images",
    "asr",
    "web_search",
    "embeddings",
    "storage",
    "promotion",
    "dataset",
    "email",
    "langfuse_tasks",
    "cleanup",
    "leaderboard",
]
