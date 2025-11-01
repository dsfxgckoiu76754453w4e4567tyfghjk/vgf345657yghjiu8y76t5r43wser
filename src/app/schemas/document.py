"""Pydantic schemas for document management."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """Document upload request."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    document_type: str = Field(
        ...,
        pattern="^(hadith|quran|tafsir|fiqh|book|article|fatwa|doubts_response|rejal|other)$",
    )
    primary_category: str = Field(
        ...,
        pattern="^(aqidah|fiqh|akhlaq|tafsir|history|doubts|rejal|general)$",
    )
    language: str = Field(default="fa", pattern="^(fa|ar|en|ur)$")
    author: Optional[str] = Field(None, max_length=255)
    source_reference: Optional[str] = Field(None, max_length=500)
    chunking_strategy: str = Field(
        default="semantic",
        pattern="^(semantic|token|sentence|adaptive)$",
    )
    chunk_size: int = Field(default=768, ge=100, le=2000)
    chunk_overlap: int = Field(default=150, ge=0, le=500)


class DocumentUploadResponse(BaseModel):
    """Document upload response."""

    code: str = "DOCUMENT_UPLOAD_SUCCESS"
    message: str
    document: "DocumentResponse"


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: UUID
    title: str
    document_type: str
    primary_category: str
    language: str
    author: Optional[str]
    source_reference: Optional[str]
    total_characters: Optional[int]
    chunk_count: int
    processing_status: str
    chunking_method: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    """Document chunk response."""

    id: UUID
    document_id: UUID
    chunk_text: str
    chunk_index: int
    char_count: int
    word_count: Optional[int]
    chunking_method: Optional[str]

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    """Semantic search request."""

    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    document_type: Optional[str] = None
    language: Optional[str] = None


class SearchResult(BaseModel):
    """Search result item."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    index: int


class SearchResponse(BaseModel):
    """Search response."""

    code: str = "SEARCH_SUCCESS"
    message: str
    query: str
    results: list[SearchResult]
    count: int


class EmbeddingsGenerationRequest(BaseModel):
    """Request to generate embeddings for a document."""

    document_id: UUID


class EmbeddingsGenerationResponse(BaseModel):
    """Embeddings generation response."""

    code: str = "EMBEDDINGS_GENERATION_SUCCESS"
    message: str
    document_id: UUID
    embeddings_count: int


# Forward references
DocumentUploadResponse.model_rebuild()
