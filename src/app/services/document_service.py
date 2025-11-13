"""Document processing service for uploading and processing documents."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from qdrant_client.http.models import PointStruct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.services.chonkie_service import chonkie_service
from app.services.embeddings_service import embeddings_service
from app.services.qdrant_service import qdrant_service
from app.services.reranker_service import reranker_service

logger = get_logger(__name__)


class DocumentService:
    """Service for document upload, processing, and chunking."""

    def __init__(self, db: AsyncSession):
        """
        Initialize document service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_document(
        self,
        title: str,
        content: str,
        document_type: str,
        primary_category: str,
        language: str = "fa",
        author: Optional[str] = None,
        source_reference: Optional[str] = None,
        uploaded_by: Optional[UUID] = None,
        chunking_strategy: str = "semantic",
        chunk_size: int = 768,
        chunk_overlap: int = 150,
    ) -> Document:
        """
        Create a new document and process it.

        Args:
            title: Document title
            content: Document text content
            document_type: Type of document (hadith, quran, tafsir, etc.)
            primary_category: Primary category (aqidah, fiqh, etc.)
            language: Document language
            author: Document author
            source_reference: Source reference
            uploaded_by: Admin who uploaded (UUID)
            chunking_strategy: Chonkie strategy (semantic, token, sentence)
            chunk_size: Target chunk size
            chunk_overlap: Chunk overlap

        Returns:
            Created document
        """
        logger.info(
            "document_creation_started",
            title=title,
            type=document_type,
            category=primary_category,
        )

        # Create document record
        document = Document(
            title=title,
            document_type=document_type,
            primary_category=primary_category,
            language=language,
            author=author,
            source_reference=source_reference,
            total_characters=len(content),
            chunking_mode="auto",
            chunking_method=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            processing_status="processing",
            uploaded_by=uploaded_by,
        )

        self.db.add(document)
        await self.db.flush()  # Get document ID

        try:
            # Chunk the document using Chonkie
            chunks = chonkie_service.chunk_text(
                text=content,
                strategy=chunking_strategy,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                language=language,
            )

            # Create chunk records
            chunk_records = []
            for chunk_data in chunks:
                chunk_record = DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk_data["text"],
                    chunk_index=chunk_data["index"],
                    char_count=chunk_data["char_count"],
                    word_count=chunk_data["word_count"],
                    token_count_estimated=chonkie_service.estimate_token_count(
                        chunk_data["text"]
                    ),
                    chunking_method=chunk_data["method"],
                    chunk_metadata=chunk_data["metadata"],
                )
                chunk_records.append(chunk_record)

            self.db.add_all(chunk_records)
            await self.db.flush()

            # Update document
            document.chunk_count = len(chunk_records)
            document.processing_status = "awaiting_chunk_approval"
            document.processed_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(document)

            logger.info(
                "document_created",
                document_id=str(document.id),
                chunks_count=len(chunk_records),
            )

            return document

        except Exception as e:
            document.processing_status = "failed"
            await self.db.commit()

            logger.error(
                "document_processing_failed",
                document_id=str(document.id),
                error=str(e),
            )
            raise

    async def generate_embeddings_for_document(
        self,
        document_id: UUID,
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Generate embeddings for all chunks in a document.

        Args:
            document_id: Document ID
            collection_name: Qdrant collection name

        Returns:
            Number of embeddings generated
        """
        logger.info(
            "embeddings_generation_started",
            document_id=str(document_id),
        )

        # Fetch document chunks
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = result.scalars().all()

        if not chunks:
            logger.warning("no_chunks_found", document_id=str(document_id))
            return 0

        # Extract texts
        chunk_texts = [chunk.chunk_text for chunk in chunks]

        # Generate embeddings (batch)
        embeddings = await embeddings_service.embed_documents(chunk_texts)

        # Prepare Qdrant points
        qdrant_points = []
        embedding_records = []

        for chunk, embedding in zip(chunks, embeddings):
            point_id = uuid4()

            # Create Qdrant point
            qdrant_point = PointStruct(
                id=str(point_id),
                vector=embedding,
                payload={
                    "chunk_id": str(chunk.id),
                    "document_id": str(document_id),
                    "chunk_text": chunk.chunk_text[:500],  # First 500 chars for preview
                    "chunk_index": chunk.chunk_index,
                },
            )
            qdrant_points.append(qdrant_point)

            # Create embedding record
            embedding_record = DocumentEmbedding(
                chunk_id=chunk.id,
                embedding_model=embeddings_service.model,
                vector_dimension=len(embedding),
                vector_db_type="qdrant",
                vector_db_collection_name=collection_name or qdrant_service.collection_name,
                vector_db_point_id=point_id,
                embedding_cost_usd=embeddings_service.estimate_cost(len(chunk.chunk_text)),
            )
            embedding_records.append(embedding_record)

        # Add to Qdrant
        await qdrant_service.add_points(qdrant_points, collection_name)

        # Save embedding records to database
        self.db.add_all(embedding_records)
        await self.db.commit()

        logger.info(
            "embeddings_generated",
            document_id=str(document_id),
            count=len(embedding_records),
        )

        return len(embedding_records)

    async def search_similar_chunks(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        use_reranker: bool = True,
        rerank_multiplier: int = 5,
    ) -> list[dict]:
        """
        Search for similar chunks using 2-stage retrieval (vector search + reranking).

        2-Stage Retrieval Process:
        - Stage 1: Vector search retrieves top N candidates (limit * rerank_multiplier)
        - Stage 2: Reranker refines to top K results (limit) using cross-encoder

        Args:
            query: Search query
            limit: Maximum number of final results
            score_threshold: Minimum similarity score for vector search
            document_type: Filter by document type
            language: Filter by language
            use_reranker: Enable 2-stage retrieval with reranking
            rerank_multiplier: How many candidates to retrieve before reranking (e.g., 5x limit)

        Returns:
            List of similar chunks with metadata and rerank scores

        Example:
            # Get top 10 results with 2-stage retrieval
            results = await document_service.search_similar_chunks(
                query="What is prayer in Islam?",
                limit=10,
                use_reranker=True,
                rerank_multiplier=5  # Retrieves 50 candidates, reranks to 10
            )
        """
        logger.info(
            "semantic_search_started",
            query_length=len(query),
            limit=limit,
            use_reranker=use_reranker,
            two_stage_retrieval=use_reranker,
        )

        # Stage 1: Vector Search (with query-optimized embeddings)
        # Retrieve more candidates if reranking is enabled
        vector_search_limit = limit * rerank_multiplier if use_reranker else limit

        # Generate query embedding (optimized for RETRIEVAL_QUERY)
        query_embedding = await embeddings_service.embed_text(query, is_query=True)

        # Build filters
        filters = {}
        if document_type:
            filters["document_type"] = document_type
        if language:
            filters["language"] = language

        # Search in Qdrant
        results = await qdrant_service.search(
            query_vector=query_embedding,
            limit=vector_search_limit,
            score_threshold=score_threshold,
            filter_conditions=filters,
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "chunk_id": result.payload.get("chunk_id"),
                    "document_id": result.payload.get("document_id"),
                    "chunk_text": result.payload.get("chunk_text"),
                    "text": result.payload.get("chunk_text"),  # Alias for compatibility
                    "vector_score": result.score,
                    "score": result.score,  # Will be updated with rerank_score if reranking
                    "chunk_index": result.payload.get("chunk_index"),
                }
            )

        logger.info(
            "stage1_vector_search_completed",
            candidates_count=len(formatted_results),
        )

        # Stage 2: Reranking (if enabled)
        if use_reranker and reranker_service.enabled and len(formatted_results) > limit:
            logger.info(
                "stage2_reranking_started",
                candidates=len(formatted_results),
                target_limit=limit,
            )

            reranked_results = await reranker_service.rerank(
                query=query,
                documents=formatted_results,
                top_k=limit,
                return_documents=True,
            )

            # Update scores to rerank scores
            for doc in reranked_results:
                doc["score"] = doc["rerank_score"]

            logger.info(
                "stage2_reranking_completed",
                final_count=len(reranked_results),
                top_rerank_score=reranked_results[0].get("rerank_score", 0) if reranked_results else 0,
            )

            return reranked_results

        # If reranker is disabled or not enough results, return vector search results
        logger.info(
            "semantic_search_completed",
            results_count=len(formatted_results[:limit]),
            reranking_skipped=not use_reranker or not reranker_service.enabled,
        )

        return formatted_results[:limit]

    async def search_with_reranking_metadata(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        rerank_multiplier: int = 5,
    ) -> tuple[list[dict], dict]:
        """
        Search with 2-stage retrieval and return detailed metadata.

        Returns:
            Tuple of (results, metadata) where metadata contains:
            - vector_search_count: Number of candidates from stage 1
            - rerank_count: Number of results after stage 2
            - top_vector_score: Highest vector similarity score
            - top_rerank_score: Highest reranking score
            - cost_estimate: Estimated cost in USD
        """
        logger.info(
            "search_with_metadata_started",
            query=query[:50],
            limit=limit,
        )

        # Perform 2-stage retrieval
        results = await self.search_similar_chunks(
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            document_type=document_type,
            language=language,
            use_reranker=True,
            rerank_multiplier=rerank_multiplier,
        )

        # Calculate metadata
        vector_search_count = limit * rerank_multiplier
        metadata = {
            "query_length": len(query),
            "vector_search_limit": vector_search_count,
            "final_limit": limit,
            "results_count": len(results),
            "top_vector_score": results[0].get("vector_score", 0) if results else 0,
            "top_rerank_score": results[0].get("rerank_score", 0) if results else 0,
            "top_final_score": results[0].get("score", 0) if results else 0,
            "reranking_used": reranker_service.enabled,
            "embedding_cost": embeddings_service.estimate_cost(len(query)),
            "rerank_cost": reranker_service.estimate_cost(vector_search_count, 1),
            "total_cost": (
                embeddings_service.estimate_cost(len(query))
                + reranker_service.estimate_cost(vector_search_count, 1)
            ),
        }

        logger.info("search_with_metadata_completed", **metadata)

        return results, metadata
