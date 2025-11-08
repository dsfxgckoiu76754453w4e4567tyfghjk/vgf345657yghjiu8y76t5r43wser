"""API endpoints for leaderboards."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.schemas.admin import LeaderboardResponse, UserStatisticsResponse
from app.services.leaderboard_service import LeaderboardService

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Document Upload Leaderboard
# ============================================================================


@router.get(
    "/documents",
    response_model=LeaderboardResponse,
    summary="Document Upload Leaderboard",
    description="""
    Get leaderboard for document uploads.

    Users are ranked by the number of documents they have uploaded.

    Timeframes:
    - all_time: All documents ever uploaded
    - month: Last 30 days
    - week: Last 7 days
    """,
)
async def get_document_upload_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    timeframe: Literal["all_time", "month", "week"] = Query(
        default="all_time", description="Time period"
    ),
    limit: int = Query(default=10, ge=1, le=100, description="Number of top users"),
) -> LeaderboardResponse:
    """
    Get document upload leaderboard.

    Args:
        timeframe: Time period to consider
        limit: Number of top users
        db: Database session

    Returns:
        Leaderboard data
    """
    try:
        leaderboard_service = LeaderboardService(db)

        leaderboard = await leaderboard_service.get_document_upload_leaderboard(
            timeframe=timeframe,
            limit=limit,
        )

        return LeaderboardResponse(
            leaderboard=leaderboard,
            timeframe=timeframe,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error("get_document_upload_leaderboard_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document upload leaderboard",
        )


# ============================================================================
# Chat Activity Leaderboard
# ============================================================================


@router.get(
    "/chat",
    response_model=LeaderboardResponse,
    summary="Chat Activity Leaderboard",
    description="""
    Get leaderboard for chat activity (number of messages sent).

    Users are ranked by the number of messages they have sent.

    Timeframes:
    - all_time: All messages ever sent
    - month: Last 30 days
    - week: Last 7 days
    """,
)
async def get_chat_activity_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    timeframe: Literal["all_time", "month", "week"] = Query(
        default="all_time", description="Time period"
    ),
    limit: int = Query(default=10, ge=1, le=100, description="Number of top users"),
) -> LeaderboardResponse:
    """
    Get chat activity leaderboard.

    Args:
        timeframe: Time period to consider
        limit: Number of top users
        db: Database session

    Returns:
        Leaderboard data
    """
    try:
        leaderboard_service = LeaderboardService(db)

        leaderboard = await leaderboard_service.get_chat_activity_leaderboard(
            timeframe=timeframe,
            limit=limit,
        )

        return LeaderboardResponse(
            leaderboard=leaderboard,
            timeframe=timeframe,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error("get_chat_activity_leaderboard_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat activity leaderboard",
        )


# ============================================================================
# Conversation Leaderboard
# ============================================================================


@router.get(
    "/conversations",
    response_model=LeaderboardResponse,
    summary="Conversation Leaderboard",
    description="""
    Get leaderboard for number of conversations started.

    Users are ranked by the number of conversations they have created.

    Timeframes:
    - all_time: All conversations ever created
    - month: Last 30 days
    - week: Last 7 days
    """,
)
async def get_conversation_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    timeframe: Literal["all_time", "month", "week"] = Query(
        default="all_time", description="Time period"
    ),
    limit: int = Query(default=10, ge=1, le=100, description="Number of top users"),
) -> LeaderboardResponse:
    """
    Get conversation leaderboard.

    Args:
        timeframe: Time period to consider
        limit: Number of top users
        db: Database session

    Returns:
        Leaderboard data
    """
    try:
        leaderboard_service = LeaderboardService(db)

        leaderboard = await leaderboard_service.get_conversation_leaderboard(
            timeframe=timeframe,
            limit=limit,
        )

        return LeaderboardResponse(
            leaderboard=leaderboard,
            timeframe=timeframe,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error("get_conversation_leaderboard_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation leaderboard",
        )


# ============================================================================
# Overall Leaderboard
# ============================================================================


@router.get(
    "/overall",
    response_model=LeaderboardResponse,
    summary="Overall Leaderboard",
    description="""
    Get overall leaderboard combining multiple metrics.

    **Scoring System:**
    - Document upload: 10 points
    - Conversation: 2 points
    - Message: 1 point

    This provides a balanced view of user contributions across different activities.

    Timeframes:
    - all_time: All time
    - month: Last 30 days
    - week: Last 7 days
    """,
)
async def get_overall_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    timeframe: Literal["all_time", "month", "week"] = Query(
        default="all_time", description="Time period"
    ),
    limit: int = Query(default=10, ge=1, le=100, description="Number of top users"),
) -> LeaderboardResponse:
    """
    Get overall leaderboard.

    Args:
        timeframe: Time period to consider
        limit: Number of top users
        db: Database session

    Returns:
        Leaderboard data with combined scoring
    """
    try:
        leaderboard_service = LeaderboardService(db)

        leaderboard = await leaderboard_service.get_overall_leaderboard(
            timeframe=timeframe,
            limit=limit,
        )

        return LeaderboardResponse(
            leaderboard=leaderboard,
            timeframe=timeframe,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error("get_overall_leaderboard_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get overall leaderboard",
        )


# ============================================================================
# User Statistics
# ============================================================================


@router.get(
    "/users/{user_id}/statistics",
    response_model=UserStatisticsResponse,
    summary="Get User Statistics",
    description="""
    Get detailed statistics for a specific user.

    Includes:
    - Document uploads
    - Conversations
    - Messages
    - Overall score
    - Global rank

    This allows users to see their own contribution metrics and ranking.
    """,
)
async def get_user_statistics(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserStatisticsResponse:
    """
    Get user statistics.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        User statistics and rank
    """
    try:
        leaderboard_service = LeaderboardService(db)

        result = await leaderboard_service.get_user_statistics(user_id=user_id)

        return UserStatisticsResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_user_statistics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics",
        )


@router.get(
    "/me/statistics",
    response_model=UserStatisticsResponse,
    summary="Get My Statistics",
    description="Get statistics for the currently authenticated user.",
)
async def get_my_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserStatisticsResponse:
    """
    Get current user's statistics.

    Args:
        db: Database session

    Returns:
        Current user's statistics and rank
    """
    # TODO: Get actual user ID from authentication
    user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        leaderboard_service = LeaderboardService(db)

        result = await leaderboard_service.get_user_statistics(user_id=user_id)

        return UserStatisticsResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_my_statistics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics",
        )
