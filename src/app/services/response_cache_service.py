"""
Response caching service for semantic query matching.

This service dramatically reduces LLM costs by caching responses and
retrieving them using semantic similarity search. Common questions like
"What is Salat?" are answered instantly from cache without calling the LLM.

Expected savings: 50-80% reduction in LLM API costs for repeated queries.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings_service import embeddings_service
from app.services.qdrant_service import qdrant_service

logger = get_logger(__name__)


class CachedResponse:
    """Cached response with metadata."""

    def __init__(
        self,
        response: str,
        query: str,
        intent: str,
        sources: list[dict],
        tokens_saved: int,
        similarity_score: float,
        cached_at: datetime,
        hit_count: int = 1,
    ):
        self.response = response
        self.query = query
        self.intent = intent
        self.sources = sources
        self.tokens_saved = tokens_saved
        self.similarity_score = similarity_score
        self.cached_at = cached_at
        self.hit_count = hit_count


class ResponseCacheService:
    """
    Semantic response caching service using Qdrant.

    Features:
    - Semantic similarity matching (not exact text match)
    - Environment-aware cache collections
    - TTL-based expiration
    - Hit count tracking
    - Cost savings metrics

    Architecture:
    - Uses Qdrant for vector similarity search
    - Each cache entry is a point with query embedding
    - Payload contains response, metadata, timestamps
    - Automatic cleanup of expired entries
    """

    def __init__(self):
        """Initialize response cache service."""
        self.collection_name = self._get_collection_name()
        self.similarity_threshold = 0.92  # Very high threshold for cache hits
        self.ttl_hours = 24 * 7  # 1 week default TTL

        logger.info(
            "response_cache_initialized",
            collection=self.collection_name,
            similarity_threshold=self.similarity_threshold,
            ttl_hours=self.ttl_hours,
        )

    def _get_collection_name(self) -> str:
        """Get environment-specific collection name."""
        return settings.get_collection_name("response_cache")

    async def initialize_collection(self):
        """
        Initialize Qdrant collection for response caching.

        Creates collection if it doesn't exist with proper vector configuration.
        """
        try:
            # Check if collection exists
            collections = await qdrant_service.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection
                await qdrant_service.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.embedding_dimension,  # 3072 for Gemini, 1024 for Cohere
                        distance=Distance.COSINE,
                    ),
                )

                logger.info(
                    "response_cache_collection_created",
                    collection=self.collection_name,
                    vector_size=settings.embedding_dimension,
                )
            else:
                logger.info(
                    "response_cache_collection_exists",
                    collection=self.collection_name,
                )

        except Exception as e:
            logger.error(
                "response_cache_initialization_failed",
                collection=self.collection_name,
                error=str(e),
            )
            raise

    async def get_cached_response(
        self,
        query: str,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[CachedResponse]:
        """
        Find semantically similar cached response.

        Args:
            query: User query
            conversation_id: Optional conversation context
            user_id: Optional user context

        Returns:
            CachedResponse if similar query found, None otherwise
        """
        try:
            # Generate query embedding
            query_embedding = await embeddings_service.generate_embedding(query)

            # Search cache collection
            search_results = await qdrant_service.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=1,
                score_threshold=self.similarity_threshold,
            )

            if not search_results:
                logger.info(
                    "cache_miss",
                    query=query[:50],
                    threshold=self.similarity_threshold,
                )
                return None

            # Check if result is expired
            result = search_results[0]
            payload = result.payload
            cached_at = datetime.fromisoformat(payload["cached_at"])

            # Check TTL
            if datetime.now(timezone.utc) - cached_at > timedelta(hours=self.ttl_hours):
                logger.info(
                    "cache_expired",
                    query=query[:50],
                    cached_at=cached_at,
                    age_hours=(datetime.now(timezone.utc) - cached_at).total_seconds() / 3600,
                )
                # Delete expired entry
                await qdrant_service.client.delete(
                    collection_name=self.collection_name,
                    points_selector=[result.id],
                )
                return None

            # Cache hit! Increment hit count
            new_hit_count = payload.get("hit_count", 1) + 1
            await qdrant_service.client.set_payload(
                collection_name=self.collection_name,
                payload={"hit_count": new_hit_count},
                points=[result.id],
            )

            logger.info(
                "cache_hit",
                query=query[:50],
                similarity=result.score,
                cached_query=payload["query"][:50],
                hit_count=new_hit_count,
                tokens_saved=payload.get("tokens_saved", 0),
            )

            return CachedResponse(
                response=payload["response"],
                query=payload["query"],
                intent=payload.get("intent", "question_answer"),
                sources=payload.get("sources", []),
                tokens_saved=payload.get("tokens_saved", 0),
                similarity_score=result.score,
                cached_at=cached_at,
                hit_count=new_hit_count,
            )

        except Exception as e:
            logger.error(
                "cache_lookup_failed",
                query=query[:50],
                error=str(e),
            )
            # On error, return None (fail open - continue without cache)
            return None

    async def cache_response(
        self,
        query: str,
        response: str,
        intent: str = "question_answer",
        sources: Optional[list[dict]] = None,
        tokens_used: int = 0,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Cache a response with semantic indexing.

        Args:
            query: Original query
            response: LLM response to cache
            intent: Detected intent
            sources: RAG sources used
            tokens_used: Tokens used for this response
            conversation_id: Optional conversation context
            user_id: Optional user context

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            # Generate query embedding
            query_embedding = await embeddings_service.generate_embedding(query)

            # Create point ID from query hash
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
            point_id = str(uuid4())  # Use UUID for point ID

            # Prepare payload
            payload = {
                "query": query,
                "response": response,
                "intent": intent,
                "sources": sources or [],
                "tokens_saved": tokens_used,  # Tokens this cache entry saves
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "hit_count": 0,
                "query_hash": query_hash,
            }

            # Optional context
            if conversation_id:
                payload["conversation_id"] = str(conversation_id)
            if user_id:
                payload["user_id"] = str(user_id)

            # Store in Qdrant
            await qdrant_service.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=query_embedding,
                        payload=payload,
                    )
                ],
            )

            logger.info(
                "response_cached",
                query=query[:50],
                intent=intent,
                tokens_saved=tokens_used,
                point_id=point_id,
            )

            return True

        except Exception as e:
            logger.error(
                "response_caching_failed",
                query=query[:50],
                error=str(e),
            )
            return False

    async def clear_expired_entries(self) -> int:
        """
        Clear expired cache entries (older than TTL).

        Returns:
            Number of entries deleted
        """
        try:
            # Get all points (with scroll)
            deleted_count = 0
            offset = None

            while True:
                results, offset = await qdrant_service.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )

                if not results:
                    break

                # Check expiration
                expired_ids = []
                for point in results:
                    cached_at = datetime.fromisoformat(point.payload["cached_at"])
                    if datetime.now(timezone.utc) - cached_at > timedelta(hours=self.ttl_hours):
                        expired_ids.append(point.id)

                # Delete expired entries
                if expired_ids:
                    await qdrant_service.client.delete(
                        collection_name=self.collection_name,
                        points_selector=expired_ids,
                    )
                    deleted_count += len(expired_ids)

                if offset is None:
                    break

            logger.info(
                "expired_cache_entries_cleared",
                deleted_count=deleted_count,
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "cache_cleanup_failed",
                error=str(e),
            )
            return 0

    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        try:
            # Get collection info
            collection_info = await qdrant_service.client.get_collection(
                collection_name=self.collection_name
            )

            # Calculate stats from points
            total_entries = collection_info.points_count
            total_hits = 0
            total_tokens_saved = 0

            # Sample some entries to get stats (limit to 1000 for performance)
            results, _ = await qdrant_service.client.scroll(
                collection_name=self.collection_name,
                limit=min(1000, total_entries),
                with_payload=True,
                with_vectors=False,
            )

            for point in results:
                total_hits += point.payload.get("hit_count", 0)
                total_tokens_saved += point.payload.get("tokens_saved", 0)

            # Estimate total tokens saved (extrapolate if sampled)
            if len(results) < total_entries:
                total_tokens_saved = int(total_tokens_saved * (total_entries / len(results)))

            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "total_tokens_saved": total_tokens_saved,
                "similarity_threshold": self.similarity_threshold,
                "ttl_hours": self.ttl_hours,
                "cost_savings_usd": total_tokens_saved * 0.000001 * 2,  # Rough estimate
            }

        except Exception as e:
            logger.error(
                "cache_stats_failed",
                error=str(e),
            )
            return {}


# Global response cache service instance
response_cache_service = ResponseCacheService()
