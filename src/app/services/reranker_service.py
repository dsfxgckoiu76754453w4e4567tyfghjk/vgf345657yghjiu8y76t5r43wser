"""Reranker service for improving retrieval quality with 2-stage search."""

from typing import Literal, Optional

from cohere import AsyncClient as CohereAsyncClient

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RerankerService:
    """
    Service for reranking search results to improve relevance.

    Implements 2-stage retrieval:
    - Stage 1: Vector search retrieves top N candidates (50-100)
    - Stage 2: Reranker refines to top K results (5-10) with cross-encoder

    Supports:
    - Cohere Rerank (rerank-3.5, rerank-multilingual-v3.0)
    - Optimized for Persian/Arabic content
    """

    def __init__(
        self,
        provider: Optional[Literal["cohere"]] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize reranker service.

        Args:
            provider: Reranker provider (currently only cohere)
            model: Model name (e.g., rerank-3.5)
        """
        self.provider = provider or settings.reranker_provider
        self.model = model or settings.reranker_model
        self.enabled = getattr(settings, "reranker_enabled", True)

        if not self.enabled:
            logger.warning("reranker_disabled", message="Reranker is disabled in configuration")
            return

        # Initialize the appropriate reranker client
        if self.provider == "cohere":
            if not settings.cohere_api_key:
                logger.error("cohere_api_key_missing", message="Cohere API key not configured")
                raise ValueError("Cohere API key is required for reranker")

            self.client = CohereAsyncClient(api_key=settings.cohere_api_key)
            logger.info(
                "reranker_service_initialized",
                provider="cohere",
                model=self.model,
            )

        else:
            raise ValueError(f"Unsupported reranker provider: {self.provider}")

    async def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 10,
        return_documents: bool = True,
    ) -> list[dict]:
        """
        Rerank documents based on query relevance.

        Args:
            query: Search query
            documents: List of document dicts with 'text' or 'chunk_text' field
            top_k: Number of top results to return after reranking
            return_documents: Whether to return full documents or just scores

        Returns:
            List of reranked documents with relevance scores

        Example:
            documents = [
                {"chunk_text": "Islam is...", "chunk_id": "123"},
                {"chunk_text": "Prayer in Islam...", "chunk_id": "456"}
            ]
            reranked = await reranker_service.rerank(
                query="What is prayer?",
                documents=documents,
                top_k=5
            )
        """
        if not self.enabled:
            logger.warning("reranker_disabled_skipping")
            return documents[:top_k]

        if not documents:
            return []

        try:
            # Extract texts from documents
            texts = []
            for doc in documents:
                # Support both 'text' and 'chunk_text' fields
                text = doc.get("chunk_text") or doc.get("text") or doc.get("content", "")
                texts.append(text)

            logger.info(
                "reranking_started",
                query_length=len(query),
                documents_count=len(documents),
                top_k=top_k,
            )

            # Call Cohere Rerank API
            response = await self.client.rerank(
                model=self.model,
                query=query,
                documents=texts,
                top_n=top_k,
                return_documents=return_documents,
            )

            # Format results
            reranked_results = []
            for result in response.results:
                original_doc = documents[result.index]
                reranked_doc = {
                    **original_doc,
                    "rerank_score": result.relevance_score,
                    "original_index": result.index,
                }
                reranked_results.append(reranked_doc)

            logger.info(
                "reranking_completed",
                original_count=len(documents),
                reranked_count=len(reranked_results),
                top_score=reranked_results[0]["rerank_score"] if reranked_results else 0,
            )

            return reranked_results

        except Exception as e:
            logger.error(
                "reranking_failed",
                error=str(e),
                query_length=len(query),
                documents_count=len(documents),
            )
            # Fallback: return original documents
            logger.warning("reranking_fallback", message="Returning original documents")
            return documents[:top_k]

    async def rerank_with_metadata(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> tuple[list[dict], dict]:
        """
        Rerank documents and return metadata about the reranking process.

        Args:
            query: Search query
            documents: List of documents
            top_k: Number of top results
            score_threshold: Minimum rerank score to include

        Returns:
            Tuple of (reranked_documents, metadata)
        """
        reranked = await self.rerank(query, documents, top_k=top_k)

        # Filter by score threshold
        filtered = [doc for doc in reranked if doc.get("rerank_score", 0) >= score_threshold]

        metadata = {
            "original_count": len(documents),
            "reranked_count": len(reranked),
            "filtered_count": len(filtered),
            "top_score": filtered[0]["rerank_score"] if filtered else 0,
            "min_score": filtered[-1]["rerank_score"] if filtered else 0,
            "avg_score": (
                sum(doc["rerank_score"] for doc in filtered) / len(filtered) if filtered else 0
            ),
        }

        logger.info("reranking_with_metadata", **metadata)

        return filtered, metadata

    def estimate_cost(self, num_documents: int, num_queries: int = 1) -> float:
        """
        Estimate reranking cost in USD.

        Cohere Rerank pricing (as of 2025):
        - rerank-3.5: $0.002 per 1K searches (per document)
        - rerank-multilingual-v3.0: $0.002 per 1K searches

        Args:
            num_documents: Number of documents to rerank
            num_queries: Number of queries

        Returns:
            Estimated cost in USD
        """
        if self.provider == "cohere":
            # Cohere charges per search per document
            # 1 query with 50 documents = 50 search units
            search_units = num_documents * num_queries
            cost_per_1k_units = 0.002
            return (search_units / 1000) * cost_per_1k_units

        return 0.0


# Global reranker service instance
try:
    reranker_service = RerankerService()
except Exception as e:
    logger.warning(
        "reranker_service_initialization_failed",
        error=str(e),
        message="Reranker service will not be available",
    )
    # Create a disabled service
    class DisabledRerankerService:
        """Fallback service when reranker is not available."""

        enabled = False

        async def rerank(self, query, documents, top_k=10, **kwargs):
            logger.warning("reranker_disabled_returning_original")
            return documents[:top_k]

        async def rerank_with_metadata(self, query, documents, top_k=10, **kwargs):
            return documents[:top_k], {"original_count": len(documents), "reranked_count": top_k}

        def estimate_cost(self, *args, **kwargs):
            return 0.0

    reranker_service = DisabledRerankerService()
