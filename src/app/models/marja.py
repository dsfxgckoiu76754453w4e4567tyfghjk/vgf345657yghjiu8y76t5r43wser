"""Marja official sources and Ahkam tool models (CRITICAL - NOT RAG-based)."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class MarjaOfficialSource(Base):
    """
    Official Marja websites for Ahkam (religious rulings) fetching.

    CRITICAL: For Ahkam queries, we DO NOT use RAG retrieval.
    Instead, we fetch directly from official Marja websites with maximum citations.
    """

    __tablename__ = "marja_official_sources"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Marja identification
    marja_name: Mapped[str] = mapped_column(String(255), nullable=False)
    marja_name_arabic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marja_name_persian: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marja_name_english: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Official website information
    official_website_url: Mapped[str] = mapped_column(String(500), nullable=False)
    website_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    website_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # API or Scraping configuration
    has_official_api: Mapped[bool] = mapped_column(Boolean, default=False)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key_required: Mapped[bool] = mapped_column(Boolean, default=False)
    api_documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Web scraping configuration
    scraping_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scraping_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Fatwa/Ahkam specific URLs
    ahkam_section_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    search_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    search_method: Mapped[str] = mapped_column(String(10), default="GET")
    search_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Content structure
    response_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    content_selectors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Reliability & Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_successful_fetch_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Rate limiting
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=10)
    requests_per_hour: Mapped[int] = mapped_column(Integer, default=100)

    # Caching policy
    cache_duration_hours: Mapped[int] = mapped_column(Integer, default=24)

    # Contact information
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Admin tracking
    added_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("system_admins.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<MarjaOfficialSource(marja_name={self.marja_name})>"


class AhkamFetchLog(Base):
    """Tracking Ahkam fetches from official Marja sources."""

    __tablename__ = "ahkam_fetch_log"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    marja_source_id: Mapped[UUID] = mapped_column(ForeignKey("marja_official_sources.id"), nullable=False)

    # Request details
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Response details
    fetch_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # success, failed, no_result, rate_limited
    response_found: Mapped[bool] = mapped_column(Boolean, default=False)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Citation information
    citation_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    citation_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Performance
    fetch_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    was_cached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AhkamFetchLog(marja_source_id={self.marja_source_id}, status={self.fetch_status})>"
