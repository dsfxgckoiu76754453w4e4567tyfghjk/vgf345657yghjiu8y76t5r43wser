"""API endpoints for specialized tools."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.tools import (
    AhkamRequest,
    AhkamResponse,
    DateConversionRequest,
    DateConversionResponse,
    HadithSearchRequest,
    HadithSearchResponse,
    KhumsRequest,
    KhumsResponse,
    MultiToolQueryRequest,
    MultiToolQueryResponse,
    PrayerTimesRequest,
    PrayerTimesResponse,
    ZakatRequest,
    ZakatResponse,
)
from app.services.ahkam_service import AhkamService
from app.services.datetime_service import DateTimeService
from app.services.hadith_service import HadithService
from app.services.math_service import MathService
from app.services.tool_orchestration_service import ToolOrchestrationService

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Ahkam Endpoints
# ============================================================================


@router.post(
    "/ahkam",
    response_model=AhkamResponse,
    summary="Get Ahkam Ruling",
    description="""
    Get Islamic ruling from official Marja source.

    **CRITICAL**: This endpoint fetches rulings directly from official Marja websites,
    NOT from RAG or stored documents. This ensures authenticity and up-to-date information.

    Supported Maraji:
    - Khamenei (default)
    - Sistani
    - Makarem Shirazi
    - Saafi Golpaygani
    - Nouri Hamadani
    """,
)
async def get_ahkam_ruling(
    request: AhkamRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AhkamResponse:
    """
    Get Ahkam ruling from official Marja source.

    This endpoint:
    1. Checks cache for recent queries
    2. Fetches from official Marja website (API or web scraping)
    3. Logs the query and response
    4. Returns authenticated ruling

    Args:
        request: Ahkam request with question and marja
        db: Database session

    Returns:
        Ahkam response with ruling and source
    """
    try:
        ahkam_service = AhkamService(db)

        result = await ahkam_service.get_ahkam_ruling(
            question=request.question,
            marja_name=request.marja_name,
            user_id=request.user_id,
        )

        return AhkamResponse(**result)

    except ValueError as e:
        logger.error("ahkam_request_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("ahkam_request_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Ahkam ruling. Please try again later.",
        )


# ============================================================================
# Hadith Endpoints
# ============================================================================


@router.post(
    "/hadith/search",
    response_model=HadithSearchResponse,
    summary="Search Hadith",
    description="""
    Search for hadith by reference, text, or narrator.

    Search types:
    - **reference**: Search by hadith reference (e.g., "Sahih al-Kafi 1:23")
    - **text**: Search by text content
    - **narrator**: Search by narrator name

    Supported collections:
    - Sahih al-Kafi
    - Al-Tahdhib
    - Man La Yahduruhu al-Faqih
    - Al-Istibsar
    """,
)
async def search_hadith(
    request: HadithSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HadithSearchResponse:
    """
    Search for hadith.

    Args:
        request: Hadith search request
        db: Database session

    Returns:
        Hadith search results
    """
    try:
        hadith_service = HadithService(db)

        results = await hadith_service.search_hadith(
            query=request.query,
            search_type=request.search_type,
            collection=request.collection,
            limit=request.limit,
        )

        return HadithSearchResponse(
            query=request.query,
            search_type=request.search_type,
            results=results,
            total_count=len(results),
        )

    except Exception as e:
        logger.error("hadith_search_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search hadith. Please try again later.",
        )


# ============================================================================
# DateTime Endpoints
# ============================================================================


@router.post(
    "/datetime/prayer-times",
    response_model=PrayerTimesResponse,
    summary="Get Prayer Times",
    description="""
    Get prayer times for a specific city and date.

    Calculation methods vary by region:
    - Iran: Institute of Geophysics, University of Tehran
    - Iraq: Iraqi authorities
    - Other regions: Islamic Society of North America (ISNA)
    """,
)
async def get_prayer_times(
    request: PrayerTimesRequest,
) -> PrayerTimesResponse:
    """
    Get prayer times for a city.

    Args:
        request: Prayer times request

    Returns:
        Prayer times for the specified city and date
    """
    try:
        datetime_service = DateTimeService()

        result = await datetime_service.get_prayer_times(
            city=request.city,
            country=request.country,
            date=request.date or date.today(),
        )

        return PrayerTimesResponse(**result)

    except Exception as e:
        logger.error("prayer_times_request_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get prayer times. Please try again later.",
        )


@router.post(
    "/datetime/convert",
    response_model=DateConversionResponse,
    summary="Convert Date Between Calendars",
    description="""
    Convert date between Gregorian and Hijri calendars.

    Supports:
    - Gregorian → Hijri
    - Hijri → Gregorian
    """,
)
async def convert_date(
    request: DateConversionRequest,
) -> DateConversionResponse:
    """
    Convert date between calendars.

    Args:
        request: Date conversion request

    Returns:
        Converted date
    """
    try:
        datetime_service = DateTimeService()

        result = await datetime_service.convert_date(
            date_str=request.date,
            from_calendar=request.from_calendar,
            to_calendar=request.to_calendar,
        )

        return DateConversionResponse(**result)

    except ValueError as e:
        logger.error("date_conversion_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("date_conversion_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert date. Please try again later.",
        )


# ============================================================================
# Math/Financial Endpoints
# ============================================================================


@router.post(
    "/math/zakat",
    response_model=ZakatResponse,
    summary="Calculate Zakat",
    description="""
    Calculate Zakat amount based on total wealth.

    ⚠️ **IMPORTANT WARNING**: This is an APPROXIMATE calculation.

    YOU MUST:
    1. Verify with your Marja's official office
    2. Consult a qualified Islamic financial advisor
    3. Check the latest fatwas from your Marja

    Different Maraji have different rules for:
    - Nisab threshold
    - Wealth calculation methods
    - Exemptions and deductions
    """,
)
async def calculate_zakat(
    request: ZakatRequest,
) -> ZakatResponse:
    """
    Calculate Zakat amount.

    Args:
        request: Zakat calculation request

    Returns:
        Zakat calculation with MANDATORY warning
    """
    try:
        math_service = MathService()

        result = await math_service.calculate_zakat(
            total_wealth=request.total_wealth,
            currency=request.currency,
        )

        return ZakatResponse(**result)

    except ValueError as e:
        logger.error("zakat_calculation_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("zakat_calculation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate Zakat. Please try again later.",
        )


@router.post(
    "/math/khums",
    response_model=KhumsResponse,
    summary="Calculate Khums",
    description="""
    Calculate Khums amount based on annual income and expenses.

    ⚠️ **IMPORTANT WARNING**: This is an APPROXIMATE calculation.

    YOU MUST:
    1. Verify with your Marja's official office
    2. Consult a qualified Islamic financial advisor
    3. Check the latest fatwas from your Marja

    Different Maraji have different rules for:
    - Calculation methods
    - Exemptions (first home, business inventory, etc.)
    - Payment timing
    """,
)
async def calculate_khums(
    request: KhumsRequest,
) -> KhumsResponse:
    """
    Calculate Khums amount.

    Args:
        request: Khums calculation request

    Returns:
        Khums calculation with MANDATORY warning
    """
    try:
        math_service = MathService()

        result = await math_service.calculate_khums(
            annual_income=request.annual_income,
            annual_expenses=request.annual_expenses,
            currency=request.currency,
        )

        return KhumsResponse(**result)

    except ValueError as e:
        logger.error("khums_calculation_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("khums_calculation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate Khums. Please try again later.",
        )


# ============================================================================
# Multi-Tool Orchestration Endpoint
# ============================================================================


@router.post(
    "/query",
    response_model=MultiToolQueryResponse,
    summary="Execute Multi-Tool Query",
    description="""
    Execute a query that may require multiple specialized tools.

    **CRITICAL FEATURE**: One question can trigger MULTIPLE tools simultaneously.

    Example queries:
    - "What is the ruling on Zakat and when are prayer times in Tehran?"
      → Triggers: Ahkam + DateTime tools

    - "Tell me about hadith on fasting and calculate my Khums"
      → Triggers: Hadith + Math tools

    - "What does Ayatollah Sistani say about music and what time is Maghrib?"
      → Triggers: Ahkam + DateTime tools

    The orchestration service automatically:
    1. Analyzes the query
    2. Determines which tools are needed
    3. Executes tools in parallel (for independent queries) or sequential (for dependent queries)
    4. Combines results intelligently
    """,
)
async def execute_multi_tool_query(
    request: MultiToolQueryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MultiToolQueryResponse:
    """
    Execute multi-tool query.

    Args:
        request: Multi-tool query request
        db: Database session

    Returns:
        Combined results from all required tools
    """
    try:
        orchestration_service = ToolOrchestrationService(db)

        # Analyze query to determine which tools are needed
        analysis = await orchestration_service.analyze_query(request.query)

        logger.info(
            "multi_tool_query_analysis",
            query=request.query[:50],
            tools_needed=analysis["tools_needed"],
        )

        # Execute multi-tool query
        result = await orchestration_service.execute_multi_tool(
            query=request.query,
            tools=analysis["tools_needed"],
            execution_mode=request.execution_mode,
            context=request.user_context,
        )

        return MultiToolQueryResponse(**result)

    except Exception as e:
        logger.error("multi_tool_query_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute multi-tool query. Please try again later.",
        )
