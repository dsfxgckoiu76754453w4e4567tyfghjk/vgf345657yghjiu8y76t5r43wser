"""Document and knowledge base models."""

from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Document(Base):
    """Documents for the knowledge base."""

    __tablename__ = "documents"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Document identification
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # hadith, quran, tafsir, fiqh, book, article, fatwa, doubts_response, rejal, other

    # Source information
    source_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="fa")  # fa, ar, en, ur

    # Religious context
    fiqh_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Document classification
    primary_category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # aqidah, fiqh, akhlaq, tafsir, history, doubts, rejal, general
    secondary_categories: Mapped[dict] = mapped_column(JSONB, default=list)
    tags: Mapped[dict] = mapped_column(JSONB, default=list)

    # File type classification
    file_type_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requires_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_asr: Mapped[bool] = mapped_column(Boolean, default=False)

    # Processing status
    processing_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, processing, completed, failed, awaiting_chunk_approval
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_characters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Chunking configuration
    chunking_mode: Mapped[str] = mapped_column(String(20), default="auto")  # auto, manual
    chunking_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chunk_size: Mapped[int] = mapped_column(Integer, default=768)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=150)

    # Quality and verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)

    # Chunking approval
    requires_chunk_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    chunk_approval_status: Mapped[str] = mapped_column(String(50), default="pending")
    chunk_approved_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    chunk_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Usage tracking
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    additional_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Admin tracking
    uploaded_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"


class DocumentChunk(Base):
    """Chunks of documents for RAG retrieval."""

    __tablename__ = "document_chunks"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Chunk content
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Chunk metadata
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_count_estimated: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context preservation
    previous_chunk_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    next_chunk_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Chunking strategy info
    chunking_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overlap_with_previous: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(
        "DocumentEmbedding", back_populates="chunk", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk"),)

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class DocumentEmbedding(Base):
    """Vector embeddings for document chunks (abstracted for multiple vector DBs)."""

    __tablename__ = "document_embeddings"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    chunk_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Embedding identification
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)

    # Vector DB integration (dynamic - not tied to Qdrant only)
    vector_db_type: Mapped[str] = mapped_column(String(50), default="qdrant", nullable=False)
    vector_db_collection_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vector_db_point_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    vector_db_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Embedding metadata
    embedding_generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    embedding_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    chunk: Mapped["DocumentChunk"] = relationship("DocumentChunk", back_populates="embeddings")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "chunk_id",
            "embedding_model",
            "vector_db_collection_name",
            name="uq_chunk_embedding",
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentEmbedding(chunk_id={self.chunk_id}, model={self.embedding_model})>"
