"""Web search service with multi-provider support."""

from typing import Any, Literal, Optional

import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSearchService:
    """
    Service for web search with multi-provider support.

    Supports:
    - Tavily (Recommended for LLM applications)
    - Serper (Google Search API)
    """

    def __init__(
        self,
        provider: Optional[Literal["tavily", "serper"]] = None,
    ):
        """
        Initialize web search service.

        Args:
            provider: Search provider (tavily or serper)
        """
        self.provider = provider or settings.web_search_provider

        # Validate API keys
        if self.provider == "tavily" and not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required when WEB_SEARCH_PROVIDER=tavily")
        elif self.provider == "serper" and not settings.serper_api_key:
            raise ValueError("SERPER_API_KEY is required when WEB_SEARCH_PROVIDER=serper")

        logger.info(
            "web_search_service_initialized",
            provider=self.provider,
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: Literal["basic", "advanced"] = "basic",
    ) -> dict[str, Any]:
        """
        Search the web for relevant information.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            search_depth: Search depth (basic or advanced)

        Returns:
            Search results with URLs, titles, and content
        """
        if not settings.web_search_enabled:
            logger.warning("web_search_disabled", query=query[:50])
            return {"results": [], "message": "Web search is disabled"}

        try:
            if self.provider == "tavily":
                return await self._search_tavily(query, max_results, search_depth)
            elif self.provider == "serper":
                return await self._search_serper(query, max_results)
            else:
                raise ValueError(f"Unsupported search provider: {self.provider}")

        except Exception as e:
            logger.error(
                "web_search_failed",
                provider=self.provider,
                query=query[:50],
                error=str(e),
            )
            raise

    async def _search_tavily(
        self,
        query: str,
        max_results: int,
        search_depth: str,
    ) -> dict[str, Any]:
        """
        Search using Tavily API.

        Tavily is optimized for LLM applications with:
        - Clean, structured results
        - Relevant content extraction
        - Fast response times
        """
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True,  # Get AI-generated answer
            "include_raw_content": False,  # Don't include full HTML
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        logger.info(
            "web_search_completed",
            provider="tavily",
            query=query[:50],
            results_count=len(data.get("results", [])),
        )

        return {
            "provider": "tavily",
            "query": query,
            "answer": data.get("answer"),  # AI-generated summary
            "results": [
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "score": result.get("score", 0),
                }
                for result in data.get("results", [])
            ],
        }

    async def _search_serper(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        """
        Search using Serper API (Google Search).

        Serper provides:
        - Google search results
        - Knowledge graph data
        - Related searches
        """
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": settings.serper_api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "num": max_results,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        logger.info(
            "web_search_completed",
            provider="serper",
            query=query[:50],
            results_count=len(data.get("organic", [])),
        )

        return {
            "provider": "serper",
            "query": query,
            "answer": data.get("answerBox", {}).get("answer"),  # Featured snippet
            "results": [
                {
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "content": result.get("snippet"),
                    "score": 1.0,  # Serper doesn't provide relevance scores
                }
                for result in data.get("organic", [])
            ],
        }

    def estimate_cost(self, num_searches: int) -> float:
        """
        Estimate search cost in USD.

        Approximate costs (as of 2025):
        - Tavily: $0.001 per search (basic), $0.01 (advanced)
        - Serper: $0.001 per search

        Args:
            num_searches: Number of searches

        Returns:
            Estimated cost in USD
        """
        if self.provider == "tavily":
            # Basic search is cheaper
            cost_per_search = 0.001
            return num_searches * cost_per_search

        elif self.provider == "serper":
            cost_per_search = 0.001
            return num_searches * cost_per_search

        return 0.0


# Global web search service instance
web_search_service = WebSearchService()
