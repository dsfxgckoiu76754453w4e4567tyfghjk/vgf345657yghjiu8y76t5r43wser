"""Unit tests for embeddings service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embeddings_service import EmbeddingsService


# ============================================================================
# Test: Embeddings Service Initialization
# ============================================================================


class TestEmbeddingsServiceInitialization:
    """Test cases for EmbeddingsService initialization."""

    @patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings")
    @patch("app.services.embeddings_service.settings")
    def test_initialization_with_gemini(
        self,
        mock_settings,
        mock_gemini_class,
    ):
        """Test initialization with Gemini provider."""
        # Setup mock settings
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-api-key"

        # Mock Gemini embeddings
        mock_embeddings = MagicMock()
        mock_gemini_class.return_value = mock_embeddings

        # Initialize service
        service = EmbeddingsService()

        # Verify Gemini was initialized
        assert service.provider == "gemini"
        assert service.model == "text-embedding-004"
        assert service.dimension == 768
        mock_gemini_class.assert_called_once_with(
            model="text-embedding-004",
            google_api_key="test-api-key",
        )

    @patch("app.services.embeddings_service.CohereEmbeddings")
    @patch("app.services.embeddings_service.settings")
    def test_initialization_with_cohere(
        self,
        mock_settings,
        mock_cohere_class,
    ):
        """Test initialization with Cohere provider."""
        # Setup mock settings
        mock_settings.embedding_provider = "cohere"
        mock_settings.embedding_model = "embed-multilingual-v3.0"
        mock_settings.embedding_dimension = 1024
        mock_settings.cohere_api_key = "test-cohere-key"

        # Mock Cohere embeddings
        mock_embeddings = MagicMock()
        mock_cohere_class.return_value = mock_embeddings

        # Initialize service
        service = EmbeddingsService(provider="cohere")

        # Verify Cohere was initialized
        assert service.provider == "cohere"
        assert service.model == "embed-multilingual-v3.0"
        mock_cohere_class.assert_called_once_with(
            model="embed-multilingual-v3.0",
            cohere_api_key="test-cohere-key",
        )

    @patch("app.services.embeddings_service.OpenAIEmbeddings")
    @patch("app.services.embeddings_service.settings")
    def test_initialization_with_openrouter(
        self,
        mock_settings,
        mock_openai_class,
    ):
        """Test initialization with OpenRouter provider."""
        # Setup mock settings
        mock_settings.embedding_provider = "openrouter"
        mock_settings.embedding_model = "text-embedding-3-large"
        mock_settings.embedding_dimension = 3072
        mock_settings.openrouter_api_key = "test-openrouter-key"
        mock_settings.openrouter_app_url = "https://app.example.com"
        mock_settings.openrouter_app_name = "Test App"

        # Mock OpenAI embeddings
        mock_embeddings = MagicMock()
        mock_openai_class.return_value = mock_embeddings

        # Initialize service
        service = EmbeddingsService(provider="openrouter")

        # Verify OpenRouter was initialized
        assert service.provider == "openrouter"
        assert service.model == "text-embedding-3-large"
        mock_openai_class.assert_called_once()
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs["model"] == "text-embedding-3-large"
        assert call_kwargs["openai_api_key"] == "test-openrouter-key"
        assert call_kwargs["openai_api_base"] == "https://openrouter.ai/api/v1"

    @patch("app.services.embeddings_service.settings")
    def test_initialization_with_custom_model(self, mock_settings):
        """Test initialization with custom model override."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "default-model"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            service = EmbeddingsService(model="custom-model")

            # Verify custom model was used
            assert service.model == "custom-model"
            mock_gemini.assert_called_once_with(
                model="custom-model",
                google_api_key="test-key",
            )

    @patch("app.services.embeddings_service.settings")
    def test_initialization_with_unsupported_provider(self, mock_settings):
        """Test initialization with unsupported provider raises error."""
        mock_settings.embedding_provider = "unsupported_provider"
        mock_settings.embedding_model = "model"
        mock_settings.embedding_dimension = 768

        # Should raise ValueError
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            EmbeddingsService()


# ============================================================================
# Test: Embed Text (Single)
# ============================================================================


class TestEmbeddingsServiceEmbedText:
    """Test cases for single text embedding."""

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_text_success(self, mock_settings):
        """Test embedding single text successfully."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        # Create service with mocked embeddings
        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_query = AsyncMock(
                return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embed text
            text = "What is Islam?"
            embedding = await service.embed_text(text)

            # Verify embedding
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_embeddings.aembed_query.assert_called_once_with(text)

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_text_with_long_text(self, mock_settings):
        """Test embedding long text."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_query = AsyncMock(
                return_value=[0.1] * 768
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embed long text
            long_text = "Lorem ipsum " * 500  # ~6000 characters
            embedding = await service.embed_text(long_text)

            # Verify embedding dimension
            assert len(embedding) == 768

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_text_handles_error(self, mock_settings):
        """Test handling error during text embedding."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_query = AsyncMock(
                side_effect=Exception("API error")
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embedding should raise exception
            with pytest.raises(Exception, match="API error"):
                await service.embed_text("Test text")


# ============================================================================
# Test: Embed Documents (Batch)
# ============================================================================


class TestEmbeddingsServiceEmbedDocuments:
    """Test cases for batch document embedding."""

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_documents_success(self, mock_settings):
        """Test embedding multiple documents successfully."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_documents = AsyncMock(
                return_value=[
                    [0.1, 0.2, 0.3],
                    [0.4, 0.5, 0.6],
                    [0.7, 0.8, 0.9],
                ]
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embed documents
            texts = [
                "Document 1 text",
                "Document 2 text",
                "Document 3 text",
            ]
            embeddings = await service.embed_documents(texts)

            # Verify embeddings
            assert len(embeddings) == 3
            assert embeddings[0] == [0.1, 0.2, 0.3]
            assert embeddings[1] == [0.4, 0.5, 0.6]
            assert embeddings[2] == [0.7, 0.8, 0.9]
            mock_embeddings.aembed_documents.assert_called_once_with(texts)

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_documents_with_single_document(self, mock_settings):
        """Test embedding a single document in batch."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_documents = AsyncMock(
                return_value=[[0.1, 0.2, 0.3]]
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embed single document
            embeddings = await service.embed_documents(["Single document"])

            # Verify single embedding
            assert len(embeddings) == 1
            assert embeddings[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_documents_with_many_documents(self, mock_settings):
        """Test embedding many documents (large batch)."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            # Create 50 embeddings
            mock_embeddings_list = [[0.1, 0.2] for _ in range(50)]
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_documents = AsyncMock(
                return_value=mock_embeddings_list
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embed 50 documents
            texts = [f"Document {i}" for i in range(50)]
            embeddings = await service.embed_documents(texts)

            # Verify all embeddings
            assert len(embeddings) == 50

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_embed_documents_handles_error(self, mock_settings):
        """Test handling error during batch embedding."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_documents = AsyncMock(
                side_effect=Exception("Batch embedding failed")
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            # Embedding should raise exception
            with pytest.raises(Exception, match="Batch embedding failed"):
                await service.embed_documents(["Doc 1", "Doc 2"])


# ============================================================================
# Test: Estimate Cost
# ============================================================================


class TestEmbeddingsServiceEstimateCost:
    """Test cases for cost estimation."""

    @patch("app.services.embeddings_service.settings")
    def test_estimate_cost_for_gemini(self, mock_settings):
        """Test cost estimation for Gemini provider."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings"):
            service = EmbeddingsService()

            # Test 1000 characters
            cost = service.estimate_cost(1000)
            assert cost == pytest.approx(0.00001, rel=1e-5)

            # Test 10,000 characters
            cost = service.estimate_cost(10000)
            assert cost == pytest.approx(0.0001, rel=1e-5)

            # Test 100,000 characters
            cost = service.estimate_cost(100000)
            assert cost == pytest.approx(0.001, rel=1e-5)

    @patch("app.services.embeddings_service.settings")
    def test_estimate_cost_for_cohere(self, mock_settings):
        """Test cost estimation for Cohere provider."""
        mock_settings.embedding_provider = "cohere"
        mock_settings.embedding_model = "embed-multilingual-v3.0"
        mock_settings.embedding_dimension = 1024
        mock_settings.cohere_api_key = "test-key"

        with patch("app.services.embeddings_service.CohereEmbeddings"):
            service = EmbeddingsService()

            # Test 1000 characters (~250 tokens)
            cost = service.estimate_cost(1000)
            expected_cost = (1000 / 4 / 1000) * 0.0001
            assert cost == pytest.approx(expected_cost, rel=1e-5)

            # Test 10,000 characters (~2500 tokens)
            cost = service.estimate_cost(10000)
            expected_cost = (10000 / 4 / 1000) * 0.0001
            assert cost == pytest.approx(expected_cost, rel=1e-5)

    @patch("app.services.embeddings_service.settings")
    def test_estimate_cost_for_openrouter_returns_zero(self, mock_settings):
        """Test cost estimation for OpenRouter (not implemented)."""
        mock_settings.embedding_provider = "openrouter"
        mock_settings.embedding_model = "text-embedding-3-large"
        mock_settings.embedding_dimension = 3072
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_app_url = "https://app.example.com"
        mock_settings.openrouter_app_name = "Test App"

        with patch("app.services.embeddings_service.OpenAIEmbeddings"):
            service = EmbeddingsService()

            # OpenRouter cost estimation not implemented, should return 0
            cost = service.estimate_cost(1000)
            assert cost == 0.0

    @patch("app.services.embeddings_service.settings")
    def test_estimate_cost_with_zero_length(self, mock_settings):
        """Test cost estimation with zero text length."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings"):
            service = EmbeddingsService()

            cost = service.estimate_cost(0)
            assert cost == 0.0

    @patch("app.services.embeddings_service.settings")
    def test_estimate_cost_with_very_large_text(self, mock_settings):
        """Test cost estimation with very large text."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings"):
            service = EmbeddingsService()

            # Test 1 million characters
            cost = service.estimate_cost(1000000)
            expected_cost = (1000000 / 1000) * 0.00001
            assert cost == pytest.approx(expected_cost, rel=1e-5)


# ============================================================================
# Test: Multi-Provider Support
# ============================================================================


class TestEmbeddingsServiceMultiProvider:
    """Test cases for multi-provider support."""

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_switching_providers_gemini_to_cohere(self, mock_settings):
        """Test that different instances can use different providers."""
        # Setup for Gemini
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"
        mock_settings.cohere_api_key = "cohere-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings"):
            gemini_service = EmbeddingsService(provider="gemini")
            assert gemini_service.provider == "gemini"

        with patch("app.services.embeddings_service.CohereEmbeddings"):
            cohere_service = EmbeddingsService(provider="cohere")
            assert cohere_service.provider == "cohere"

    @pytest.mark.asyncio
    @patch("app.services.embeddings_service.settings")
    async def test_provider_specific_error_handling(self, mock_settings):
        """Test that errors are properly attributed to providers."""
        mock_settings.embedding_provider = "gemini"
        mock_settings.embedding_model = "text-embedding-004"
        mock_settings.embedding_dimension = 768
        mock_settings.google_api_key = "test-key"

        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock_gemini:
            mock_embeddings = MagicMock()
            mock_embeddings.aembed_query = AsyncMock(
                side_effect=Exception("Gemini API rate limit exceeded")
            )
            mock_gemini.return_value = mock_embeddings

            service = EmbeddingsService()

            with pytest.raises(Exception, match="Gemini API rate limit exceeded"):
                await service.embed_text("Test")
