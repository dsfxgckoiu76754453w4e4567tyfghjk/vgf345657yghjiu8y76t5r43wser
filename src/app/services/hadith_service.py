"""Hadith lookup service for searching and retrieving hadith."""

from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk

logger = get_logger(__name__)


class HadithService:
    """
    Service for Hadith lookup and retrieval.

    Supports:
    - Search by reference (e.g., "Sahih al-Kafi 1:23")
    - Search by text content
    - Search by narrator
    - Narrator chain (sanad) display
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize Hadith service.

        Args:
            db: Database session
        """
        self.db = db

    async def search_hadith(
        self,
        query: str,
        search_type: Literal["reference", "text", "narrator"] = "text",
        collection: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for hadith.

        Args:
            query: Search query
            search_type: Type of search (reference, text, or narrator)
            collection: Hadith collection name (e.g., "Sahih al-Kafi")
            limit: Maximum results

        Returns:
            List of hadith results with metadata
        """
        logger.info(
            "hadith_search_started",
            query=query[:50],
            search_type=search_type,
            collection=collection,
        )

        if search_type == "reference":
            results = await self._search_by_reference(query, collection, limit)
        elif search_type == "narrator":
            results = await self._search_by_narrator(query, limit)
        else:  # text
            results = await self._search_by_text(query, collection, limit)

        logger.info(
            "hadith_search_completed",
            query=query[:50],
            results_count=len(results),
        )

        return results

    async def _search_by_reference(
        self,
        reference: str,
        collection: Optional[str],
        limit: int,
    ) -> list[dict]:
        """
        Search hadith by reference.

        Example: "Sahih al-Kafi 1:23"
        """
        query = select(Document).where(Document.document_type == "hadith")

        if collection:
            query = query.where(Document.source_reference.ilike(f"%{collection}%"))

        # Parse reference (simplified - in production, use more robust parsing)
        query = query.where(Document.source_reference.ilike(f"%{reference}%"))

        query = query.limit(limit)

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [
            {
                "hadith_id": str(doc.id),
                "collection": doc.source_reference,
                "reference": doc.source_reference,
                "text": doc.title,  # Or fetch from chunks
                "narrator_chain": [],  # TODO: Link to hadith_chains table
                "reliability": "sahih",  # TODO: Calculate from chain
            }
            for doc in documents
        ]

    async def _search_by_text(
        self,
        text: str,
        collection: Optional[str],
        limit: int,
    ) -> list[dict]:
        """
        Search hadith by text content.

        Uses document chunks for better matching.
        """
        query = (
            select(DocumentChunk)
            .join(Document)
            .where(Document.document_type == "hadith")
            .where(DocumentChunk.chunk_text.ilike(f"%{text}%"))
        )

        if collection:
            query = query.where(Document.source_reference.ilike(f"%{collection}%"))

        query = query.limit(limit)

        result = await self.db.execute(query)
        chunks = result.scalars().all()

        return [
            {
                "hadith_id": str(chunk.document_id),
                "text": chunk.chunk_text,
                "collection": "Unknown",  # TODO: Join with document
                "reference": "",
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]

    async def _search_by_narrator(
        self,
        narrator_name: str,
        limit: int,
    ) -> list[dict]:
        """
        Search hadith by narrator name.

        TODO: Integrate with rejal_persons and hadith_chains tables.
        """
        # For now, search in document metadata
        query = (
            select(Document)
            .where(Document.document_type == "hadith")
            .where(
                or_(
                    Document.author.ilike(f"%{narrator_name}%"),
                    Document.additional_metadata["narrators"]
                    .astext.ilike(f"%{narrator_name}%"),
                )
            )
            .limit(limit)
        )

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [
            {
                "hadith_id": str(doc.id),
                "collection": doc.source_reference,
                "narrator": narrator_name,
                "text": doc.title,
                "narrator_chain": [],  # TODO: Link to hadith_chains
            }
            for doc in documents
        ]

    async def get_hadith_by_id(self, hadith_id: UUID) -> Optional[dict]:
        """
        Get complete hadith information by ID.

        Args:
            hadith_id: Hadith document ID

        Returns:
            Complete hadith information with narrator chain
        """
        result = await self.db.execute(
            select(Document).where(Document.id == hadith_id).where(Document.document_type == "hadith")
        )

        document = result.scalar_one_or_none()

        if not document:
            return None

        # Get all chunks for full text
        chunks_result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == hadith_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()

        full_text = " ".join(chunk.chunk_text for chunk in chunks)

        return {
            "hadith_id": str(document.id),
            "collection": document.source_reference,
            "reference": document.source_reference,
            "full_text": full_text,
            "narrator_chain": [],  # TODO: Fetch from hadith_chains
            "reliability_rating": "sahih",  # TODO: Calculate
            "source_book": document.source_reference,
            "language": document.language,
        }
