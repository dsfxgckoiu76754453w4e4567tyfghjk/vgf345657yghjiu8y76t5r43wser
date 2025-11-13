"""Web search service with multi-provider support."""

from typing import Any, Literal, Optional

import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# OpenRouter search model fallbacks (in priority order)
# These models have native search support
OPENROUTER_SEARCH_MODELS = [
    "perplexity/sonar",
    "perplexity/sonar-pro",
    "perplexity/sonar-reasoning",
    "perplexity/sonar-reasoning-pro",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
]


class WebSearchService:
    """
    Service for web search with multi-provider support.

    Supports:
    - OpenRouter (Primary - Search-enabled models like Perplexity Sonar)
    - Serper (Google Search API)
    """

    def __init__(
        self,
        provider: Optional[Literal["serper", "openrouter"]] = None,
    ):
        """
        Initialize web search service.

        Args:
            provider: Search provider (serper or openrouter)
        """
        self.provider = provider or settings.web_search_provider

        # Validate API keys
        if self.provider == "serper" and not settings.serper_api_key:
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
            if self.provider == "serper":
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

        Includes automatic fallback to alternative models if the primary model
        is unavailable or deprecated.
        """
        # Prepare list of models to try (primary + fallbacks)
        primary_model = settings.web_search_model
        models_to_try = [primary_model]

        # Add fallback models if primary is not in the list
        for fallback_model in OPENROUTER_SEARCH_MODELS:
            if fallback_model != primary_model and fallback_model not in models_to_try:
                models_to_try.append(fallback_model)

        last_error = None
        for attempt, model in enumerate(models_to_try):
            try:
                result = await self._try_openrouter_model(query, max_results, model)

                # Log if we used a fallback model
                if attempt > 0:
                    logger.warning(
                        "openrouter_model_fallback_used",
                        primary_model=primary_model,
                        fallback_model=model,
                        attempt=attempt + 1,
                        message=f"Primary model '{primary_model}' failed, using fallback '{model}'",
                    )

                return result

            except httpx.HTTPStatusError as e:
                last_error = e
                error_detail = ""
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("error", {}).get("message", str(e))
                except Exception:
                    error_detail = str(e)

                logger.warning(
                    "openrouter_model_failed",
                    model=model,
                    status_code=e.response.status_code,
                    error=error_detail,
                    attempt=attempt + 1,
                    remaining_fallbacks=len(models_to_try) - attempt - 1,
                )

                # If this is the last model, raise the error
                if attempt == len(models_to_try) - 1:
                    raise ValueError(
                        f"All OpenRouter search models failed. Last error: {error_detail}. "
                        f"Tried models: {', '.join(models_to_try)}. "
                        f"Please check if your model '{primary_model}' is still available at https://openrouter.ai/models"
                    ) from e

            except Exception as e:
                last_error = e
                logger.warning(
                    "openrouter_model_error",
                    model=model,
                    error=str(e),
                    attempt=attempt + 1,
                )

                # If this is the last model, raise the error
                if attempt == len(models_to_try) - 1:
                    raise

        # Should not reach here, but just in case
        raise last_error or Exception("Failed to search with OpenRouter")

    async def _try_openrouter_model(
        self,
        query: str,
        max_results: int,
        model: str,
    ) -> dict[str, Any]:
        """
        Try searching with a specific OpenRouter model using the web plugin.

        Uses OpenRouter's native web search plugin which works with any model.
        For models with native search support (OpenAI, Anthropic, Perplexity),
        it uses provider's built-in search. For others, uses Exa search.

        Args:
            query: Search query
            max_results: Maximum number of results
            model: Model to use

        Returns:
            Search results with citations from annotations

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_app_url,
            "X-Title": settings.openrouter_app_name,
        }

        # Build web plugin configuration
        web_plugin = {
            "id": "web",
            "max_results": max_results,
        }

        # Add engine specification if configured
        if settings.web_search_engine:
            web_plugin["engine"] = settings.web_search_engine

        # Build payload with web plugin
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ],
            "plugins": [web_plugin],
            "temperature": settings.web_search_temperature,
            "max_tokens": settings.web_search_max_tokens,
        }

        # Add web_search_options for native search models
        # (Perplexity, OpenAI with search, etc.)
        if self._is_native_search_model(model):
            payload["web_search_options"] = {
                "search_context_size": settings.web_search_context_size
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()

        # Extract the response
        message = data["choices"][0]["message"]
        answer = message["content"]

        # Parse citations from annotations (standardized by OpenRouter)
        annotations = message.get("annotations", [])
        citations = []

        for annotation in annotations:
            if annotation.get("type") == "url_citation":
                citation_data = annotation.get("url_citation", {})
                citations.append({
                    "title": citation_data.get("title", ""),
                    "url": citation_data.get("url", ""),
                    "content": citation_data.get("content", ""),
                    "start_index": citation_data.get("start_index"),
                    "end_index": citation_data.get("end_index"),
                })

        logger.info(
            "web_search_completed",
            provider="openrouter",
            model=model,
            query=query[:50],
            citations_count=len(citations),
            engine=settings.web_search_engine or "auto",
        )

        # Format results for compatibility
        results = []
        for i, citation in enumerate(citations):
            results.append({
                "title": citation["title"] or f"Source {i+1}",
                "url": citation["url"],
                "content": citation["content"],
                "score": 1.0 - (i * 0.1),  # Simple relevance scoring
            })

        return {
            "provider": "openrouter",
            "model": model,
            "query": query,
            "answer": answer,
            "results": results,
            "full_response": answer,
            "annotations": annotations,  # Include raw annotations
        }

    def _is_native_search_model(self, model: str) -> bool:
        """
        Check if a model has native search support.

        Native search is supported by:
        - Perplexity models (all sonar variants)
        - OpenAI models
        - Anthropic models

        Args:
            model: Model ID

        Returns:
            True if model has native search support
        """
        model_lower = model.lower()
        native_providers = ["perplexity/", "openai/", "anthropic/"]
        return any(model_lower.startswith(provider) for provider in native_providers)

    def estimate_cost(self, num_searches: int, max_results: int = 5) -> float:
        """
        Estimate search cost in USD based on OpenRouter documentation.

        Costs (as of 2025):
        - Serper: $0.001 per search
        - OpenRouter with Exa: $4 per 1000 results ($0.02 for 5 results)
        - OpenRouter Native Search (per 1000 requests):
          - Perplexity Sonar: $5 (low), $8 (medium), $12 (high)
          - Perplexity Sonar Pro: $6 (low), $10 (medium), $14 (high)
          - OpenAI GPT-4o/GPT-4.1: $30 (low), $35 (medium), $50 (high)
          - OpenAI GPT-4o-mini: $25 (low), $27.50 (medium), $30 (high)

        Args:
            num_searches: Number of searches
            max_results: Maximum results per search (for Exa pricing)

        Returns:
            Estimated cost in USD
        """
        if self.provider == "serper":
            cost_per_search = 0.001
            return num_searches * cost_per_search

        elif self.provider == "openrouter":
            model = settings.web_search_model.lower()

            # Check if using native search or Exa
            if self._is_native_search_model(settings.web_search_model) and settings.web_search_engine != "exa":
                # Native search pricing (per 1000 requests)
                context_size = settings.web_search_context_size

                # Perplexity pricing
                if "sonar-reasoning-pro" in model or "sonar-pro" in model:
                    cost_per_1k = {"low": 6.0, "medium": 10.0, "high": 14.0}[context_size]
                elif "sonar" in model:
                    cost_per_1k = {"low": 5.0, "medium": 8.0, "high": 12.0}[context_size]
                # OpenAI pricing
                elif "gpt-4o-mini" in model or "gpt-4.1-mini" in model:
                    cost_per_1k = {"low": 25.0, "medium": 27.5, "high": 30.0}[context_size]
                elif "gpt-4o" in model or "gpt-4.1" in model:
                    cost_per_1k = {"low": 30.0, "medium": 35.0, "high": 50.0}[context_size]
                else:
                    # Default for other native search models
                    cost_per_1k = {"low": 5.0, "medium": 8.0, "high": 12.0}[context_size]

                return (num_searches / 1000) * cost_per_1k
            else:
                # Exa search pricing: $4 per 1000 results
                total_results = num_searches * max_results
                return (total_results / 1000) * 4.0

        return 0.0


# Global web search service instance
web_search_service = WebSearchService()
