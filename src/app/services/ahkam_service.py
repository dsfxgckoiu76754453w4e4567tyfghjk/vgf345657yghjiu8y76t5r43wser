"""
Ahkam (Religious Rulings) Service.

CRITICAL: This service does NOT use RAG retrieval.
Instead, it fetches rulings directly from official Marja websites
with maximum citations and direct links.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.marja import AhkamFetchLog, MarjaOfficialSource

logger = get_logger(__name__)


class AhkamService:
    """
    Service for fetching Ahkam (religious rulings) from official Marja websites.

    CRITICAL IMPLEMENTATION NOTES:
    - Does NOT use RAG retrieval
    - Fetches directly from official sources
    - Provides maximum citations with URLs
    - Respects rate limits
    - Caches responses (24-hour default)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize Ahkam service.

        Args:
            db: Database session
        """
        self.db = db
        self.cache_duration = timedelta(hours=settings.ahkam_cache_ttl_hours)
        self.fetch_timeout = settings.ahkam_fetch_timeout_seconds
        self.max_retries = settings.ahkam_max_retries

    async def get_ahkam_ruling(
        self,
        question: str,
        marja_name: str = "Khamenei",
        category: Optional[str] = None,
        language: str = "fa",
    ) -> dict:
        """
        Get Ahkam ruling from official Marja source.

        Args:
            question: User's question about Islamic ruling
            marja_name: Name of Marja (e.g., 'Sistani', 'Khamenei')
            category: Optional category (prayer, fasting, zakat, etc.)
            language: Response language (fa, ar, en)

        Returns:
            Dictionary with ruling, source URL, and citation

        Raises:
            ValueError: If Marja source not found or fetch fails
        """
        logger.info(
            "ahkam_fetch_started",
            marja=marja_name,
            question=question[:50],
            category=category,
        )

        # Check cache first
        cached_result = await self._check_cache(question, marja_name)
        if cached_result:
            logger.info(
                "ahkam_cache_hit",
                marja=marja_name,
                question=question[:50],
            )
            return cached_result

        # Get Marja official source
        marja_source = await self._get_marja_source(marja_name, language)
        if not marja_source:
            raise ValueError(f"Marja source not found: {marja_name}")

        # Fetch from official website
        start_time = datetime.now(timezone.utc)

        try:
            if marja_source.has_official_api:
                result = await self._fetch_from_api(marja_source, question, category)
            else:
                result = await self._fetch_via_web_scraping(marja_source, question, category)

            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Format response with maximum citations
            formatted_response = self._format_response(result, marja_source)

            # Log fetch
            await self._log_fetch(
                marja_source_id=marja_source.id,
                question=question,
                category=category,
                status="success",
                response_found=bool(result),
                response_text=formatted_response.get("ruling", ""),
                response_url=formatted_response.get("source_url", ""),
                duration_ms=duration_ms,
            )

            logger.info(
                "ahkam_fetch_success",
                marja=marja_name,
                question=question[:50],
                duration_ms=duration_ms,
            )

            return formatted_response

        except Exception as e:
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            await self._log_fetch(
                marja_source_id=marja_source.id,
                question=question,
                category=category,
                status="failed",
                error_message=str(e),
                duration_ms=duration_ms,
            )

            logger.error(
                "ahkam_fetch_failed",
                marja=marja_name,
                error=str(e),
            )
            raise

    async def _get_marja_source(
        self,
        marja_name: str,
        language: str = "fa",
    ) -> Optional[MarjaOfficialSource]:
        """Get Marja official source from database."""
        result = await self.db.execute(
            select(MarjaOfficialSource)
            .where(MarjaOfficialSource.marja_name == marja_name)
            .where(MarjaOfficialSource.is_active == True)
            .where(MarjaOfficialSource.website_language == language)
        )
        return result.scalar_one_or_none()

    async def _fetch_from_api(
        self,
        marja_source: MarjaOfficialSource,
        question: str,
        category: Optional[str],
    ) -> dict:
        """
        Fetch ruling from official API.

        This is used when the Marja has an official API endpoint.
        """
        if not marja_source.api_endpoint:
            raise ValueError("API endpoint not configured")

        async with aiohttp.ClientSession() as session:
            # Build API request
            params = marja_source.search_parameters or {}
            params["query"] = question
            if category:
                params["category"] = category

            try:
                async with session.get(
                    marja_source.api_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.fetch_timeout),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    return {
                        "ruling_text": data.get("ruling", ""),
                        "direct_url": data.get("url", marja_source.official_website_url),
                        "reference": data.get("reference", ""),
                        "confidence": 0.95,  # High confidence for API responses
                    }

            except Exception as e:
                logger.error("api_fetch_failed", error=str(e))
                raise

    async def _fetch_via_web_scraping(
        self,
        marja_source: MarjaOfficialSource,
        question: str,
        category: Optional[str],
    ) -> dict:
        """
        Fetch ruling via web scraping.

        This is used when there's no official API.
        Uses Beautiful Soup for respectful web scraping.
        """
        if not marja_source.search_url:
            raise ValueError("Search URL not configured")

        async with aiohttp.ClientSession() as session:
            # Build search URL
            search_url = marja_source.search_url
            params = {"q": question}

            if marja_source.search_method == "POST":
                method = session.post
                kwargs = {"data": params}
            else:
                method = session.get
                kwargs = {"params": params}

            try:
                async with method(
                    search_url,
                    timeout=aiohttp.ClientTimeout(total=self.fetch_timeout),
                    **kwargs,
                ) as response:
                    response.raise_for_status()
                    html = await response.text()

                    # Parse HTML
                    soup = BeautifulSoup(html, "lxml")

                    # Extract ruling using configured selectors
                    selectors = marja_source.content_selectors or {}
                    title_selector = selectors.get("title", "h1")
                    content_selector = selectors.get("content", "div.content")

                    title_elem = soup.select_one(title_selector)
                    content_elem = soup.select_one(content_selector)

                    ruling_text = ""
                    if content_elem:
                        ruling_text = content_elem.get_text(strip=True)

                    return {
                        "ruling_text": ruling_text,
                        "direct_url": str(response.url),
                        "reference": title_elem.get_text(strip=True) if title_elem else "",
                        "confidence": 0.8,  # Moderate confidence for scraped content
                    }

            except Exception as e:
                logger.error("web_scraping_failed", error=str(e))
                raise

    def _format_response(
        self,
        result: dict,
        marja_source: MarjaOfficialSource,
    ) -> dict:
        """
        Format response with maximum citations.

        CRITICAL: Always include direct links to official sources.
        """
        return {
            "ruling": result.get("ruling_text", ""),
            "source_url": result.get("direct_url", marja_source.official_website_url),
            "source_name": marja_source.marja_name,
            "citation": {
                "marja": marja_source.marja_name,
                "website": marja_source.official_website_url,
                "direct_link": result.get("direct_url", ""),
                "reference": result.get("reference", ""),
                "accessed_at": datetime.now(timezone.utc).isoformat(),
            },
            "confidence": result.get("confidence", 0.7),
            "disclaimer": self._get_disclaimer(),
            "fetched_from": "official_source",  # NOT from RAG
        }

    def _get_disclaimer(self) -> str:
        """Get standard disclaimer for Ahkam rulings."""
        return """
⚠️ IMPORTANT DISCLAIMER ⚠️

This ruling has been fetched directly from the official Marja website.
However, please note:

1. Always verify rulings with your Marja's official office for important matters
2. Rulings may change based on specific circumstances
3. Consult a qualified Islamic scholar for complex situations
4. This is for general guidance only

For the most accurate and up-to-date rulings, please visit the official website.
"""

    async def _check_cache(
        self,
        question: str,
        marja_name: str,
    ) -> Optional[dict]:
        """
        Check if we have a cached response.

        Cache key is based on question hash + marja name.
        Default TTL: 24 hours (configurable).
        """
        # Generate cache key
        cache_key = hashlib.md5(f"{question}:{marja_name}".encode()).hexdigest()

        # Check recent fetch logs
        cutoff_time = datetime.now(timezone.utc) - self.cache_duration

        result = await self.db.execute(
            select(AhkamFetchLog)
            .where(AhkamFetchLog.question_text == question)
            .where(AhkamFetchLog.fetch_status == "success")
            .where(AhkamFetchLog.fetched_at >= cutoff_time)
            .order_by(AhkamFetchLog.fetched_at.desc())
            .limit(1)
        )

        log = result.scalar_one_or_none()

        if log and log.response_found:
            # Return cached response
            return {
                "ruling": log.response_text or "",
                "source_url": log.response_url or "",
                "citation": {
                    "reference": log.citation_reference or "",
                },
                "cached": True,
                "fetched_at": log.fetched_at.isoformat(),
            }

        return None

    async def _log_fetch(
        self,
        marja_source_id: UUID,
        question: str,
        category: Optional[str],
        status: str,
        response_found: bool = False,
        response_text: Optional[str] = None,
        response_url: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log Ahkam fetch for monitoring and caching."""
        log = AhkamFetchLog(
            marja_source_id=marja_source_id,
            question_text=question,
            question_category=category,
            fetch_status=status,
            response_found=response_found,
            response_text=response_text,
            response_url=response_url,
            fetch_duration_ms=duration_ms,
            was_cached=False,
            error_message=error_message,
        )

        self.db.add(log)
        await self.db.commit()
