"""Document management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    EmbeddingsGenerationRequest,
    EmbeddingsGenerationResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.document_service import DocumentService
from app.services.qdrant_service import qdrant_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request_data: DocumentUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Upload and process a new document.

    - **title**: Document title
    - **content**: Full text content
    - **document_type**: Type (hadith, quran, tafsir, fiqh, etc.)
    - **primary_category**: Category (aqidah, fiqh, etc.)
    - **language**: Language code (fa, ar, en, ur)
    - **chunking_strategy**: Chunking method (semantic, token, sentence, adaptive)

    Document will be chunked using Chonkie and prepared for embedding generation.
    """
    document_service = DocumentService(db)

    try:
        document = await document_service.create_document(
            title=request_data.title,
            content=request_data.content,
            document_type=request_data.document_type,
            primary_category=request_data.primary_category,
            language=request_data.language,
            author=request_data.author,
            source_reference=request_data.source_reference,
            uploaded_by=current_user.id,
            chunking_strategy=request_data.chunking_strategy,
            chunk_size=request_data.chunk_size,
            chunk_overlap=request_data.chunk_overlap,
        )

        logger.info(
            "document_uploaded_via_api",
            document_id=str(document.id),
            user_id=str(current_user.id),
        )

        return DocumentUploadResponse(
            message=f"Document uploaded successfully. {document.chunk_count} chunks created.",
            document=DocumentResponse.model_validate(document),
        )

    except Exception as e:
        logger.error(
            "document_upload_failed",
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DOCUMENT_UPLOAD_FAILED: {str(e)}",
        )


@router.post("/embeddings/generate", response_model=EmbeddingsGenerationResponse)
async def generate_embeddings(
    request_data: EmbeddingsGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmbeddingsGenerationResponse:
    """
    Generate embeddings for a document's chunks.

    - **document_id**: Document ID

    Generates vector embeddings using configured provider (Gemini/Cohere)
    and stores them in Qdrant.
    """
    document_service = DocumentService(db)

    try:
        # Ensure Qdrant collection exists
        await qdrant_service.ensure_collection_exists()

        # Generate embeddings
        count = await document_service.generate_embeddings_for_document(
            document_id=request_data.document_id,
        )

        logger.info(
            "embeddings_generated_via_api",
            document_id=str(request_data.document_id),
            count=count,
            user_id=str(current_user.id),
        )

        return EmbeddingsGenerationResponse(
            message=f"Generated {count} embeddings for document",
            document_id=request_data.document_id,
            embeddings_count=count,
        )

    except Exception as e:
        logger.error(
            "embeddings_generation_failed",
            error=str(e),
            document_id=str(request_data.document_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EMBEDDINGS_GENERATION_FAILED: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request_data: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Search documents using semantic similarity.

    - **query**: Search query
    - **limit**: Maximum results (default: 10)
    - **score_threshold**: Minimum similarity score (default: 0.7)
    - **document_type**: Filter by document type (optional)
    - **language**: Filter by language (optional)

    Returns chunks ranked by semantic similarity.
    """
    document_service = DocumentService(db)

    try:
        results = await document_service.search_similar_chunks(
            query=request_data.query,
            limit=request_data.limit,
            score_threshold=request_data.score_threshold,
            document_type=request_data.document_type,
            language=request_data.language,
        )

        # Convert to response format
        search_results = [
            SearchResult(
                chunk_id=result["chunk_id"],
                document_id=result["document_id"],
                text=result["text"],
                score=result["score"],
                index=result["index"],
            )
            for result in results
        ]

        logger.info(
            "document_search_completed",
            query=request_data.query,
            results_count=len(search_results),
        )

        return SearchResponse(
            message="Search completed successfully",
            query=request_data.query,
            results=search_results,
            count=len(search_results),
        )

    except Exception as e:
        logger.error(
            "document_search_failed",
            error=str(e),
            query=request_data.query,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SEARCH_FAILED: {str(e)}",
        )


@router.get("/qdrant/status")
async def get_qdrant_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get Qdrant collection status.

    Requires authentication.
    """
    try:
        info = await qdrant_service.get_collection_info()

        logger.info(
            "qdrant_status_checked",
            user_id=str(current_user.id),
        )

        return {
            "code": "QDRANT_STATUS_SUCCESS",
            "message": "Qdrant status retrieved",
            "collection": info,
        }

    except Exception as e:
        logger.error(
            "qdrant_status_failed",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QDRANT_STATUS_FAILED: {str(e)}",
        )
