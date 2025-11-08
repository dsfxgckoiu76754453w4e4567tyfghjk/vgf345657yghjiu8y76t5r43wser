"""
Web search tasks (HIGH PRIORITY).

Handles asynchronous web search operations with:
- Multi-provider support (Tavily, Serper, OpenRouter/Perplexity)
- Result ranking and filtering
- Cost tracking
"""

import asyncio
from typing import Any
from uuid import UUID

from celery import Task

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.services.web_search_service import WebSearchService

logger = get_logger(__name__)


class WebSearchTask(Task):
    """Custom task class with progress tracking."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info("web_search_success", task_id=task_id, query=kwargs.get('query', '')[:50])

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error("web_search_failure", task_id=task_id, exception=str(exc))


@celery_app.task(
    base=WebSearchTask,
    bind=True,
    name='app.tasks.web_search.search_web',
    max_retries=2,
    default_retry_delay=5,
    acks_late=True,
    time_limit=60,
)
def search_web(
    self,
    query: str,
    user_id: str | None = None,
    max_results: int = 5,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Perform web search asynchronously.

    Args:
        self: Celery task instance
        query: Search query
        user_id: Optional user ID for tracking
        max_results: Maximum number of results (default: 5)
        provider: Search provider (tavily, serper, openrouter)

    Returns:
        dict: Search results with URLs, snippets, and metadata
    """
    try:
        self.update_state(
            state='STARTED',
            meta={'progress': 0, 'status': 'Searching web...'}
        )

        logger.info(
            "searching_web",
            task_id=self.request.id,
            query=query[:100],
            provider=provider or settings.web_search_provider,
        )

        async def _search_web():
            """Inner async function to handle web search."""
            web_search_service = WebSearchService()

            self.update_state(
                state='STARTED',
                meta={'progress': 50, 'status': 'Processing results...'}
            )

            result = await web_search_service.search(
                query=query,
                max_results=max_results,
                provider=provider,
            )

            return result

        result = asyncio.run(_search_web())

        logger.info(
            "web_search_completed",
            task_id=self.request.id,
            results_count=len(result.get('results', [])),
        )

        return {
            'status': 'success',
            'task_id': self.request.id,
            'result': result,
        }

    except Exception as exc:
        logger.error("web_search_error", task_id=self.request.id, error=str(exc))
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc)
        raise
