"""Embeddings generation service with multi-provider support."""

import asyncio
from typing import Literal, Optional

from langchain_cohere import CohereEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingsService:
    """
    Service for generating embeddings with multi-provider support.

    Supports:
    - Gemini (Google Generative AI) with task_type optimization
    - Cohere
    - OpenRouter (unified API for multiple providers)
    """

    def __init__(
        self,
        provider: Optional[Literal["gemini", "cohere", "openrouter"]] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize embeddings service.

        Args:
            provider: Embedding provider (gemini, cohere, or openrouter)
            model: Model name
        """
        self.provider = provider or settings.embedding_provider
        self.model = model or settings.embedding_model
        self.dimension = settings.embedding_dimension

        # Initialize the appropriate embeddings client
        if self.provider == "gemini":
            # Google Gemini with task_type optimization (LangChain best practice)
            self.embeddings_document = GoogleGenerativeAIEmbeddings(
                model=self.model,
                google_api_key=settings.google_api_key,
                task_type="RETRIEVAL_DOCUMENT",  # Optimized for document indexing
            )
            self.embeddings_query = GoogleGenerativeAIEmbeddings(
                model=self.model,
                google_api_key=settings.google_api_key,
                task_type="RETRIEVAL_QUERY",  # Optimized for query search
            )
            logger.info(
                "embeddings_service_initialized",
                provider="gemini",
                model=self.model,
                task_types=["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"],
            )

        elif self.provider == "cohere":
            self.embeddings_document = CohereEmbeddings(
                model=self.model,
                cohere_api_key=settings.cohere_api_key,
            )
            self.embeddings_query = self.embeddings_document  # Cohere uses same client
            logger.info(
                "embeddings_service_initialized",
                provider="cohere",
                model=self.model,
            )

        elif self.provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API
            self.embeddings_document = OpenAIEmbeddings(
                model=self.model,
                openai_api_key=settings.openrouter_api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": settings.openrouter_app_url,
                    "X-Title": settings.openrouter_app_name,
                },
            )
            self.embeddings_query = self.embeddings_document  # OpenRouter uses same client
            logger.info(
                "embeddings_service_initialized",
                provider="openrouter",
                model=self.model,
            )

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def embed_text(self, text: str, is_query: bool = True) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            is_query: True for query (search), False for document (indexing)

        Returns:
            Embedding vector
        """
        try:
            # Use appropriate embedding client based on task type
            embeddings_client = self.embeddings_query if is_query else self.embeddings_document
            embedding = await embeddings_client.aembed_query(text)

            logger.debug(
                "text_embedded",
                provider=self.provider,
                text_length=len(text),
                vector_dimension=len(embedding),
                is_query=is_query,
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
        Generate embeddings for multiple texts (batch) - optimized for document indexing.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Use document-optimized embeddings
            embeddings = await self.embeddings_document.aembed_documents(texts)

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

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batches (3-5x faster).

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (100 for Gemini, 96 for Cohere)
            show_progress: Log progress for large batches

        Returns:
            List of embedding vectors

        Performance:
        - Batch processing: 3-5x faster than individual requests
        - Reduces API calls: 100 texts = 1 request instead of 100
        - Cost efficient: Same price, better throughput
        """
        try:
            all_embeddings = []
            total_batches = (len(texts) + batch_size - 1) // batch_size

            logger.info(
                "batch_embedding_started",
                provider=self.provider,
                total_texts=len(texts),
                batch_size=batch_size,
                total_batches=total_batches,
            )

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_num = i // batch_size + 1

                if show_progress and batch_num % 10 == 0:
                    logger.info(
                        "batch_progress",
                        batch=batch_num,
                        total=total_batches,
                        progress_pct=int((batch_num / total_batches) * 100),
                    )

                # Embed batch using document-optimized embeddings
                batch_embeddings = await self.embeddings_document.aembed_documents(batch)
                all_embeddings.extend(batch_embeddings)

                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)

            logger.info(
                "batch_embedding_completed",
                provider=self.provider,
                total_texts=len(texts),
                total_batches=total_batches,
            )

            return all_embeddings

        except Exception as e:
            logger.error(
                "batch_embedding_failed",
                provider=self.provider,
                texts_count=len(texts),
                error=str(e),
            )
            raise

    async def embed_documents_parallel(
        self,
        texts: list[str],
        max_concurrency: int = 5,
        batch_size: int = 20,
    ) -> list[list[float]]:
        """
        Generate embeddings with parallel batch processing (even faster).

        Args:
            texts: List of texts to embed
            max_concurrency: Maximum concurrent batch requests
            batch_size: Texts per batch

        Returns:
            List of embedding vectors

        Performance:
        - 5-10x faster than sequential for large datasets
        - Optimal for 1000+ documents
        - Respects rate limits with max_concurrency
        """
        try:
            logger.info(
                "parallel_embedding_started",
                total_texts=len(texts),
                max_concurrency=max_concurrency,
                batch_size=batch_size,
            )

            # Split into batches
            batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

            # Process batches with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrency)

            async def process_batch(batch):
                async with semaphore:
                    return await self.embeddings_document.aembed_documents(batch)

            # Run all batches concurrently
            results = await asyncio.gather(*[process_batch(batch) for batch in batches])

            # Flatten results
            all_embeddings = []
            for batch_embeddings in results:
                all_embeddings.extend(batch_embeddings)

            logger.info(
                "parallel_embedding_completed",
                total_texts=len(texts),
                batches=len(batches),
            )

            return all_embeddings

        except Exception as e:
            logger.error(
                "parallel_embedding_failed",
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
