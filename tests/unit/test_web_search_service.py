"""Unit tests for web search service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import Response, HTTPStatusError, Request

from app.services.web_search_service import (
    WebSearchService,
    OPENROUTER_SEARCH_MODELS,
)


class TestWebSearchServiceInitialization:
    """Test WebSearchService initialization."""

    @patch("app.services.web_search_service.settings")
    def test_init_with_tavily_provider(self, mock_settings):
        """Test initialization with Tavily provider."""
        mock_settings.web_search_provider = "tavily"
        mock_settings.tavily_api_key = "test-key"

        service = WebSearchService()

        assert service.provider == "tavily"

    @patch("app.services.web_search_service.settings")
    def test_init_with_serper_provider(self, mock_settings):
        """Test initialization with Serper provider."""
        mock_settings.web_search_provider = "serper"
        mock_settings.serper_api_key = "test-key"

        service = WebSearchService()

        assert service.provider == "serper"

    @patch("app.services.web_search_service.settings")
    def test_init_with_openrouter_provider(self, mock_settings):
        """Test initialization with OpenRouter provider."""
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.web_search_model = "perplexity/sonar-deep-research"

        service = WebSearchService()

        assert service.provider == "openrouter"

    @patch("app.services.web_search_service.settings")
    def test_init_without_tavily_key_raises_error(self, mock_settings):
        """Test initialization without Tavily API key raises error."""
        mock_settings.web_search_provider = "tavily"
        mock_settings.tavily_api_key = None

        with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
            WebSearchService()

    @patch("app.services.web_search_service.settings")
    def test_init_without_openrouter_key_raises_error(self, mock_settings):
        """Test initialization without OpenRouter API key raises error."""
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = None

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
            WebSearchService()


class TestWebSearchServiceSearch:
    """Test WebSearchService search method."""

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    async def test_search_when_disabled(self, mock_settings):
        """Test search returns message when disabled."""
        mock_settings.web_search_enabled = False
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"

        service = WebSearchService()
        result = await service.search("test query")

        assert result["results"] == []
        assert "disabled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    async def test_search_with_invalid_provider(self, mock_settings):
        """Test search with invalid provider raises error."""
        mock_settings.web_search_enabled = True
        mock_settings.web_search_provider = "invalid"
        mock_settings.openrouter_api_key = "test-key"

        service = WebSearchService(provider="invalid")

        with pytest.raises(ValueError, match="Unsupported search provider"):
            await service.search("test query")


class TestOpenRouterSearch:
    """Test OpenRouter search functionality."""

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    @patch("httpx.AsyncClient")
    async def test_openrouter_search_success(self, mock_client_class, mock_settings):
        """Test successful OpenRouter search with web plugin."""
        # Setup mock settings
        mock_settings.web_search_enabled = True
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_app_url = "https://test.com"
        mock_settings.openrouter_app_name = "Test App"
        mock_settings.web_search_model = "perplexity/sonar"
        mock_settings.web_search_temperature = 0.3
        mock_settings.web_search_max_tokens = 4096
        mock_settings.web_search_context_size = "medium"
        mock_settings.web_search_engine = None

        # Setup mock response with annotations
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test answer with information about the query.",
                        "annotations": []
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()

        # Setup mock client
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute search
        service = WebSearchService()
        result = await service.search("test query", max_results=5)

        # Verify result
        assert result["provider"] == "openrouter"
        assert result["model"] == "perplexity/sonar"
        assert result["query"] == "test query"
        assert "answer" in result
        assert "Test answer" in result["answer"]

        # Verify API call includes plugins parameter
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "openrouter.ai" in call_args[0][0]
        payload = call_args[1]["json"]
        assert payload["model"] == "perplexity/sonar"
        assert "plugins" in payload
        assert payload["plugins"][0]["id"] == "web"
        assert payload["plugins"][0]["max_results"] == 5

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    @patch("httpx.AsyncClient")
    async def test_openrouter_search_with_annotations(self, mock_client_class, mock_settings):
        """Test OpenRouter search with annotations (URL citations)."""
        # Setup mock settings
        mock_settings.web_search_enabled = True
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_app_url = "https://test.com"
        mock_settings.openrouter_app_name = "Test App"
        mock_settings.web_search_model = "perplexity/sonar"
        mock_settings.web_search_temperature = 0.3
        mock_settings.web_search_max_tokens = 4096
        mock_settings.web_search_context_size = "medium"
        mock_settings.web_search_engine = None

        # Setup mock response with annotations (OpenRouter format)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test answer with citations [1][2]",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url_citation": {
                                    "url": "https://example.com/1",
                                    "title": "Source 1",
                                    "content": "Content 1",
                                    "start_index": 28,
                                    "end_index": 31
                                }
                            },
                            {
                                "type": "url_citation",
                                "url_citation": {
                                    "url": "https://example.com/2",
                                    "title": "Source 2",
                                    "content": "Content 2",
                                    "start_index": 31,
                                    "end_index": 34
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()

        # Setup mock client
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute search
        service = WebSearchService()
        result = await service.search("test query", max_results=5)

        # Verify citations parsed from annotations
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Source 1"
        assert result["results"][0]["url"] == "https://example.com/1"
        assert result["results"][0]["content"] == "Content 1"
        assert result["results"][1]["title"] == "Source 2"
        assert result["results"][1]["url"] == "https://example.com/2"

        # Verify raw annotations are included
        assert "annotations" in result
        assert len(result["annotations"]) == 2

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    @patch("httpx.AsyncClient")
    async def test_openrouter_search_fallback_on_model_failure(
        self, mock_client_class, mock_settings
    ):
        """Test OpenRouter search falls back to alternative models on failure."""
        # Setup mock settings
        mock_settings.web_search_enabled = True
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_app_url = "https://test.com"
        mock_settings.openrouter_app_name = "Test App"
        mock_settings.web_search_model = "deprecated/model"
        mock_settings.web_search_temperature = 0.3
        mock_settings.web_search_max_tokens = 4096

        # Setup mock responses - first fails, second succeeds
        mock_error_response = Mock()
        mock_error_response.status_code = 404
        mock_error_response.json.return_value = {
            "error": {"message": "Model not found"}
        }
        mock_error_response.raise_for_status.side_effect = HTTPStatusError(
            "404",
            request=Mock(spec=Request),
            response=mock_error_response
        )

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Fallback model answer"
                    }
                }
            ]
        }
        mock_success_response.raise_for_status = Mock()

        # Setup mock client with two responses
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_error_response, mock_success_response]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute search
        service = WebSearchService()
        result = await service.search("test query", max_results=5)

        # Add required settings for fallback test
        mock_settings.web_search_context_size = "medium"
        mock_settings.web_search_engine = None

        # Update mock responses to include message format
        mock_success_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Fallback model answer",
                        "annotations": []
                    }
                }
            ]
        }

        # Verify fallback was used
        assert result["provider"] == "openrouter"
        assert result["model"] == OPENROUTER_SEARCH_MODELS[0]  # First fallback
        assert "Fallback model answer" in result["answer"]

        # Verify two API calls were made
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.web_search_service.settings")
    @patch("httpx.AsyncClient")
    async def test_openrouter_search_all_models_fail(
        self, mock_client_class, mock_settings
    ):
        """Test OpenRouter search raises error when all models fail."""
        # Setup mock settings
        mock_settings.web_search_enabled = True
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_app_url = "https://test.com"
        mock_settings.openrouter_app_name = "Test App"
        mock_settings.web_search_model = "deprecated/model"
        mock_settings.web_search_temperature = 0.3
        mock_settings.web_search_max_tokens = 4096

        # Setup mock error response
        mock_error_response = Mock()
        mock_error_response.status_code = 404
        mock_error_response.json.return_value = {
            "error": {"message": "Model not found"}
        }
        mock_error_response.raise_for_status.side_effect = HTTPStatusError(
            "404",
            request=Mock(spec=Request),
            response=mock_error_response
        )

        # Setup mock client to always fail
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_error_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute search and expect error
        service = WebSearchService()

        with pytest.raises(ValueError, match="All OpenRouter search models failed"):
            await service.search("test query", max_results=5)


class TestCostEstimation:
    """Test cost estimation methods."""

    @patch("app.services.web_search_service.settings")
    def test_estimate_cost_tavily(self, mock_settings):
        """Test cost estimation for Tavily."""
        mock_settings.web_search_provider = "tavily"
        mock_settings.tavily_api_key = "test-key"

        service = WebSearchService()
        cost = service.estimate_cost(10)

        assert cost == 0.01  # 10 * 0.001

    @patch("app.services.web_search_service.settings")
    def test_estimate_cost_serper(self, mock_settings):
        """Test cost estimation for Serper."""
        mock_settings.web_search_provider = "serper"
        mock_settings.serper_api_key = "test-key"

        service = WebSearchService()
        cost = service.estimate_cost(10)

        assert cost == 0.01  # 10 * 0.001

    @patch("app.services.web_search_service.settings")
    def test_estimate_cost_openrouter_sonar_native(self, mock_settings):
        """Test cost estimation for OpenRouter Sonar with native search."""
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.web_search_model = "perplexity/sonar"
        mock_settings.web_search_context_size = "medium"
        mock_settings.web_search_engine = None  # Auto (uses native)

        service = WebSearchService()
        cost = service.estimate_cost(1000, max_results=5)

        # Native search: $8 per 1000 requests for medium context
        assert cost == 8.0

    @patch("app.services.web_search_service.settings")
    def test_estimate_cost_openrouter_exa(self, mock_settings):
        """Test cost estimation for OpenRouter with Exa search."""
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.web_search_model = "anthropic/claude-3.5-sonnet"
        mock_settings.web_search_engine = "exa"  # Force Exa

        service = WebSearchService()
        cost = service.estimate_cost(10, max_results=5)

        # Exa search: $4 per 1000 results, 10 searches * 5 results = 50 results
        # 50/1000 * $4 = $0.20
        assert cost == 0.20

    @patch("app.services.web_search_service.settings")
    def test_estimate_cost_openrouter_gpt4o_native(self, mock_settings):
        """Test cost estimation for OpenRouter GPT-4o with native search."""
        mock_settings.web_search_provider = "openrouter"
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.web_search_model = "openai/gpt-4o"
        mock_settings.web_search_context_size = "high"
        mock_settings.web_search_engine = None

        service = WebSearchService()
        cost = service.estimate_cost(1000, max_results=5)

        # GPT-4o native search: $50 per 1000 requests for high context
        assert cost == 50.0


class TestFallbackModels:
    """Test fallback model configuration."""

    def test_fallback_models_list_exists(self):
        """Test that fallback models list is defined."""
        assert OPENROUTER_SEARCH_MODELS is not None
        assert len(OPENROUTER_SEARCH_MODELS) > 0

    def test_fallback_models_include_sonar(self):
        """Test that fallback models include Sonar models."""
        sonar_models = [m for m in OPENROUTER_SEARCH_MODELS if "sonar" in m.lower()]
        assert len(sonar_models) > 0

    def test_fallback_models_include_gpt4o(self):
        """Test that fallback models include GPT-4o models."""
        gpt4o_models = [m for m in OPENROUTER_SEARCH_MODELS if "gpt-4o" in m.lower()]
        assert len(gpt4o_models) > 0
