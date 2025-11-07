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
    - OpenRouter (Search-enabled models like Perplexity Sonar)
    """

    def __init__(
        self,
        provider: Optional[Literal["tavily", "serper", "openrouter"]] = None,
    ):
        """
        Initialize web search service.

        Args:
            provider: Search provider (tavily, serper, or openrouter)
        """
        self.provider = provider or settings.web_search_provider

        # Validate API keys
        if self.provider == "tavily" and not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required when WEB_SEARCH_PROVIDER=tavily")
        elif self.provider == "serper" and not settings.serper_api_key:
            raise ValueError("SERPER_API_KEY is required when WEB_SEARCH_PROVIDER=serper")
        elif self.provider == "openrouter" and not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when WEB_SEARCH_PROVIDER=openrouter")

        logger.info(
            "web_search_service_initialized",
            provider=self.provider,
            model=settings.web_search_model if self.provider == "openrouter" else None,
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
            elif self.provider == "openrouter":
                return await self._search_openrouter(query, max_results)
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

    async def _search_openrouter(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        """
        Search using OpenRouter's search-enabled models.

        OpenRouter provides access to search-enabled models like:
        - perplexity/sonar-deep-research (deep research with citations)
        - openai/gpt-4o-search-preview (GPT-4 with search)
        - openai/gpt-4o-mini-search-preview (faster, cheaper)

        These models have built-in web search capabilities and provide
        responses with citations and sources.
        """
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_app_url,
            "X-Title": settings.openrouter_app_name,
        }

        # Construct prompt for search
        search_prompt = f"""Please search the web and provide comprehensive information about: {query}

Include:
1. A clear, concise answer to the query
2. Key facts and details
3. Multiple sources and references

Provide up to {max_results} relevant sources with their URLs."""

        payload = {
            "model": settings.web_search_model,
            "messages": [
                {
                    "role": "user",
                    "content": search_prompt,
                }
            ],
            "temperature": settings.web_search_temperature,
            "max_tokens": settings.web_search_max_tokens,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()

        # Extract the response
        answer = data["choices"][0]["message"]["content"]

        # Parse citations if available (some models provide structured citations)
        citations = []
        if "citations" in data:
            citations = data["citations"]
        elif "sources" in data.get("choices", [{}])[0].get("message", {}):
            citations = data["choices"][0]["message"]["sources"]

        logger.info(
            "web_search_completed",
            provider="openrouter",
            model=settings.web_search_model,
            query=query[:50],
            citations_count=len(citations),
        )

        # Format results - extract URLs from citations or answer
        results = []
        if citations:
            for i, citation in enumerate(citations[:max_results]):
                results.append({
                    "title": citation.get("title", f"Source {i+1}"),
                    "url": citation.get("url", citation.get("link", "")),
                    "content": citation.get("snippet", citation.get("excerpt", "")),
                    "score": 1.0 - (i * 0.1),  # Simple relevance scoring
                })

        return {
            "provider": "openrouter",
            "model": settings.web_search_model,
            "query": query,
            "answer": answer,
            "results": results,
            "full_response": answer,  # Include full response for models without structured citations
        }

    def estimate_cost(self, num_searches: int) -> float:
        """
        Estimate search cost in USD.

        Approximate costs (as of 2025):
        - Tavily: $0.001 per search (basic), $0.01 (advanced)
        - Serper: $0.001 per search
        - OpenRouter: Varies by model
          - perplexity/sonar-deep-research: ~$0.015 per search
          - openai/gpt-4o-search-preview: ~$0.02 per search
          - openai/gpt-4o-mini-search-preview: ~$0.002 per search

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

        elif self.provider == "openrouter":
            # Estimate based on model
            model = settings.web_search_model.lower()
            if "mini" in model:
                cost_per_search = 0.002
            elif "gpt-4o" in model:
                cost_per_search = 0.02
            elif "sonar" in model:
                cost_per_search = 0.015
            else:
                cost_per_search = 0.01  # Default estimate
            return num_searches * cost_per_search

        return 0.0


# Global web search service instance
web_search_service = WebSearchService()
