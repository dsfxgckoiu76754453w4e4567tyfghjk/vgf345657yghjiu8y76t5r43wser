"""Embeddings generation service with multi-provider support."""

from typing import Literal, Optional

from langchain_cohere import CohereEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingsService:
    """
    Service for generating embeddings with multi-provider support.

    Supports:
    - Gemini (Google Generative AI)
    - Cohere
    """

    def __init__(
        self,
        provider: Optional[Literal["gemini", "cohere"]] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize embeddings service.

        Args:
            provider: Embedding provider (gemini or cohere)
            model: Model name
        """
        self.provider = provider or settings.embedding_provider
        self.model = model or settings.embedding_model
        self.dimension = settings.embedding_dimension

        # Initialize the appropriate embeddings client
        if self.provider == "gemini":
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.model,
                google_api_key=settings.google_api_key,
            )
            logger.info(
                "embeddings_service_initialized",
                provider="gemini",
                model=self.model,
            )

        elif self.provider == "cohere":
            self.embeddings = CohereEmbeddings(
                model=self.model,
                cohere_api_key=settings.cohere_api_key,
            )
            logger.info(
                "embeddings_service_initialized",
                provider="cohere",
                model=self.model,
            )

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            embedding = await self.embeddings.aembed_query(text)

            logger.debug(
                "text_embedded",
                provider=self.provider,
                text_length=len(text),
                vector_dimension=len(embedding),
            )

            return embedding

        except Exception as e:
            logger.error(
                "text_embedding_failed",
                provider=self.provider,
                error=str(e),
            )
            raise

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)

            logger.info(
                "documents_embedded",
                provider=self.provider,
                count=len(texts),
                vector_dimension=len(embeddings[0]) if embeddings else 0,
            )

            return embeddings

        except Exception as e:
            logger.error(
                "documents_embedding_failed",
                provider=self.provider,
                count=len(texts),
                error=str(e),
            )
            raise

    def estimate_cost(self, text_length: int) -> float:
        """
        Estimate embedding cost in USD.

        Approximate costs (as of 2025):
        - Gemini: $0.00001 per 1K characters
        - Cohere: $0.0001 per 1K tokens

        Args:
            text_length: Length of text in characters

        Returns:
            Estimated cost in USD
        """
        if self.provider == "gemini":
            # Gemini charges per character
            cost_per_1k_chars = 0.00001
            return (text_length / 1000) * cost_per_1k_chars

        elif self.provider == "cohere":
            # Cohere charges per token (estimate 4 chars = 1 token)
            estimated_tokens = text_length / 4
            cost_per_1k_tokens = 0.0001
            return (estimated_tokens / 1000) * cost_per_1k_tokens

        return 0.0


# Global embeddings service instance
embeddings_service = EmbeddingsService()
