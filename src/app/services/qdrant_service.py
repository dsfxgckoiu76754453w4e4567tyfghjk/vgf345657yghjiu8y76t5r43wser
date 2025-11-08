"""Qdrant vector database service."""

from typing import Any, Optional
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantService:
    """
    Service for interacting with Qdrant vector database.

    Environment-aware:
    - Collections automatically prefixed with environment
    - islamic_knowledge → islamic_knowledge_dev (in dev)
    - islamic_knowledge → islamic_knowledge_prod (in prod)
    - Supports vector copying for promotions
    """

    def __init__(self):
        """Initialize Qdrant client."""
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        # Use environment-specific collection name
        self.collection_name = settings.get_collection_name(settings.qdrant_collection_name)

    async def ensure_collection_exists(
        self,
        collection_name: Optional[str] = None,
        vector_size: int = 3072,  # Gemini embedding default
        distance: Distance = Distance.COSINE,
    ) -> None:
        """
        Ensure collection exists, create if it doesn't.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
        """
        collection_name = collection_name or self.collection_name

        try:
            collections = await self.client.get_collections()
            collection_exists = any(
                col.name == collection_name for col in collections.collections
            )

            if not collection_exists:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance,
                    ),
                    # Enable binary quantization for 40x performance boost
                    quantization_config=models.BinaryQuantization(
                        binary=models.BinaryQuantizationConfig(
                            always_ram=True,
                        ),
                    ),
                    # Enable payload indexing
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=10000,
                    ),
                )

                logger.info(
                    "qdrant_collection_created",
                    collection_name=collection_name,
                    vector_size=vector_size,
                )
            else:
                logger.info(
                    "qdrant_collection_exists",
                    collection_name=collection_name,
                )

        except Exception as e:
            logger.error(
                "qdrant_collection_creation_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def add_points(
        self,
        points: list[PointStruct],
        collection_name: Optional[str] = None,
    ) -> None:
        """
        Add points to collection.

        Args:
            points: List of PointStruct objects
            collection_name: Name of the collection
        """
        collection_name = collection_name or self.collection_name

        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(
                "qdrant_points_added",
                collection_name=collection_name,
                count=len(points),
            )

        except Exception as e:
            logger.error(
                "qdrant_points_add_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> list[models.ScoredPoint]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Payload filters
            collection_name: Name of the collection

        Returns:
            List of scored points
        """
        collection_name = collection_name or self.collection_name

        # Build filter
        query_filter = None
        if filter_conditions:
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

            query_filter = Filter(must=must_conditions)

        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )

            logger.info(
                "qdrant_search_completed",
                collection_name=collection_name,
                results_count=len(results),
            )

            return results

        except Exception as e:
            logger.error(
                "qdrant_search_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def delete_points(
        self,
        point_ids: list[UUID],
        collection_name: Optional[str] = None,
    ) -> None:
        """
        Delete points from collection.

        Args:
            point_ids: List of point IDs to delete
            collection_name: Name of the collection
        """
        collection_name = collection_name or self.collection_name

        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[str(point_id) for point_id in point_ids],
                ),
            )

            logger.info(
                "qdrant_points_deleted",
                collection_name=collection_name,
                count=len(point_ids),
            )

        except Exception as e:
            logger.error(
                "qdrant_points_delete_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def get_collection_info(
        self,
        collection_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get collection information.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection information
        """
        collection_name = collection_name or self.collection_name

        try:
            info = await self.client.get_collection(collection_name=collection_name)

            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
            }

        except Exception as e:
            logger.error(
                "qdrant_get_collection_info_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def get_points_by_ids(
        self,
        point_ids: list[UUID],
        collection_name: Optional[str] = None,
    ) -> list[models.Record]:
        """
        Get specific points by their IDs.

        Args:
            point_ids: List of point IDs to retrieve
            collection_name: Name of the collection

        Returns:
            List of point records
        """
        collection_name = collection_name or self.collection_name

        try:
            results = await self.client.retrieve(
                collection_name=collection_name,
                ids=[str(point_id) for point_id in point_ids],
                with_vectors=True,
                with_payload=True,
            )

            logger.info(
                "qdrant_points_retrieved",
                collection_name=collection_name,
                count=len(results),
            )

            return results

        except Exception as e:
            logger.error(
                "qdrant_points_retrieve_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise

    async def copy_points_to_collection(
        self,
        point_ids: list[UUID],
        source_collection: str,
        target_collection: str,
    ) -> int:
        """
        Copy specific points from source to target collection.

        Used for promotion between environments.

        Args:
            point_ids: List of point IDs to copy
            source_collection: Source collection name
            target_collection: Target collection name

        Returns:
            Number of points copied
        """
        try:
            # Get points from source
            points = await self.client.retrieve(
                collection_name=source_collection,
                ids=[str(point_id) for point_id in point_ids],
                with_vectors=True,
                with_payload=True,
            )

            if not points:
                logger.warning(
                    "no_points_to_copy",
                    source_collection=source_collection,
                    target_collection=target_collection,
                    point_ids=len(point_ids),
                )
                return 0

            # Ensure target collection exists
            await self.ensure_collection_exists(collection_name=target_collection)

            # Convert to PointStruct for upsert
            points_to_insert = [
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload,
                )
                for point in points
            ]

            # Upsert into target collection
            await self.client.upsert(
                collection_name=target_collection,
                points=points_to_insert,
            )

            logger.info(
                "qdrant_points_copied",
                source_collection=source_collection,
                target_collection=target_collection,
                count=len(points_to_insert),
            )

            return len(points_to_insert)

        except Exception as e:
            logger.error(
                "qdrant_points_copy_failed",
                source_collection=source_collection,
                target_collection=target_collection,
                error=str(e),
            )
            raise

    def get_env_collection_name(
        self,
        base_collection: str,
        environment: str,
    ) -> str:
        """
        Get environment-specific collection name.

        Args:
            base_collection: Base collection name
            environment: Target environment (dev, stage, prod)

        Returns:
            Environment-specific collection name
        """
        return f"{base_collection}_{environment}"

    async def close(self) -> None:
        """Close Qdrant client connection."""
        await self.client.close()


# Global Qdrant service instance
qdrant_service = QdrantService()
