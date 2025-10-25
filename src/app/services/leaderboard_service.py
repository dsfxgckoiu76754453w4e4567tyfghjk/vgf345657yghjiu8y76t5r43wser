"""Leaderboard service for tracking user contributions."""

from datetime import datetime, timedelta
from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.chat import Conversation, Message
from app.models.document import Document
from app.models.user import User

logger = get_logger(__name__)


class LeaderboardService:
    """Service for generating user leaderboards."""

    def __init__(self, db: AsyncSession):
        """Initialize leaderboard service.

        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # Document Upload Leaderboard
    # ========================================================================

    async def get_document_upload_leaderboard(
        self,
        timeframe: Literal["all_time", "month", "week"] = "all_time",
        limit: int = 10,
    ) -> list[dict]:
        """
        Get leaderboard for document uploads.

        Args:
            timeframe: Time period to consider
            limit: Number of top users to return

        Returns:
            Ranked list of users by document uploads
        """
        query = select(
            Document.uploaded_by_user_id,
            func.count(Document.id).label("upload_count"),
        ).where(Document.uploaded_by_user_id.is_not(None))

        # Apply timeframe filter
        if timeframe == "month":
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.where(Document.created_at >= one_month_ago)
        elif timeframe == "week":
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.where(Document.created_at >= one_week_ago)

        query = (
            query.group_by(Document.uploaded_by_user_id)
            .order_by(func.count(Document.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        upload_counts = result.all()

        # Fetch user details
        leaderboard = []
        for rank, (user_id, count) in enumerate(upload_counts, start=1):
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": str(user_id),
                    "display_name": user.display_name or "Anonymous",
                    "email": user.email,
                    "upload_count": count,
                })

        logger.info(
            "document_upload_leaderboard_generated",
            timeframe=timeframe,
            count=len(leaderboard),
        )

        return leaderboard

    # ========================================================================
    # Chat Activity Leaderboard
    # ========================================================================

    async def get_chat_activity_leaderboard(
        self,
        timeframe: Literal["all_time", "month", "week"] = "all_time",
        limit: int = 10,
    ) -> list[dict]:
        """
        Get leaderboard for chat activity (number of messages sent).

        Args:
            timeframe: Time period to consider
            limit: Number of top users to return

        Returns:
            Ranked list of users by chat activity
        """
        query = select(
            Message.sender_user_id,
            func.count(Message.id).label("message_count"),
        ).where(
            and_(
                Message.sender_user_id.is_not(None),
                Message.sender_type == "user",
            )
        )

        # Apply timeframe filter
        if timeframe == "month":
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.where(Message.created_at >= one_month_ago)
        elif timeframe == "week":
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.where(Message.created_at >= one_week_ago)

        query = (
            query.group_by(Message.sender_user_id)
            .order_by(func.count(Message.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        message_counts = result.all()

        # Fetch user details
        leaderboard = []
        for rank, (user_id, count) in enumerate(message_counts, start=1):
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": str(user_id),
                    "display_name": user.display_name or "Anonymous",
                    "email": user.email,
                    "message_count": count,
                })

        logger.info(
            "chat_activity_leaderboard_generated",
            timeframe=timeframe,
            count=len(leaderboard),
        )

        return leaderboard

    # ========================================================================
    # Conversation Leaderboard
    # ========================================================================

    async def get_conversation_leaderboard(
        self,
        timeframe: Literal["all_time", "month", "week"] = "all_time",
        limit: int = 10,
    ) -> list[dict]:
        """
        Get leaderboard for number of conversations started.

        Args:
            timeframe: Time period to consider
            limit: Number of top users to return

        Returns:
            Ranked list of users by conversation count
        """
        query = select(
            Conversation.user_id,
            func.count(Conversation.id).label("conversation_count"),
        )

        # Apply timeframe filter
        if timeframe == "month":
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.where(Conversation.created_at >= one_month_ago)
        elif timeframe == "week":
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.where(Conversation.created_at >= one_week_ago)

        query = (
            query.group_by(Conversation.user_id)
            .order_by(func.count(Conversation.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        conversation_counts = result.all()

        # Fetch user details
        leaderboard = []
        for rank, (user_id, count) in enumerate(conversation_counts, start=1):
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": str(user_id),
                    "display_name": user.display_name or "Anonymous",
                    "email": user.email,
                    "conversation_count": count,
                })

        logger.info(
            "conversation_leaderboard_generated",
            timeframe=timeframe,
            count=len(leaderboard),
        )

        return leaderboard

    # ========================================================================
    # Combined Overall Leaderboard
    # ========================================================================

    async def get_overall_leaderboard(
        self,
        timeframe: Literal["all_time", "month", "week"] = "all_time",
        limit: int = 10,
    ) -> list[dict]:
        """
        Get overall leaderboard combining multiple metrics.

        Scoring:
        - Document upload: 10 points
        - Conversation: 2 points
        - Message: 1 point

        Args:
            timeframe: Time period to consider
            limit: Number of top users to return

        Returns:
            Ranked list of users by overall contribution score
        """
        # Calculate scores for each user
        user_scores: dict[UUID, dict] = {}

        # Get document uploads
        doc_leaderboard = await self.get_document_upload_leaderboard(timeframe, limit=100)
        for entry in doc_leaderboard:
            user_id = UUID(entry["user_id"])
            if user_id not in user_scores:
                user_scores[user_id] = {
                    "user_id": entry["user_id"],
                    "display_name": entry["display_name"],
                    "email": entry["email"],
                    "score": 0,
                    "document_uploads": 0,
                    "conversations": 0,
                    "messages": 0,
                }
            user_scores[user_id]["document_uploads"] = entry["upload_count"]
            user_scores[user_id]["score"] += entry["upload_count"] * 10

        # Get conversations
        conv_leaderboard = await self.get_conversation_leaderboard(timeframe, limit=100)
        for entry in conv_leaderboard:
            user_id = UUID(entry["user_id"])
            if user_id not in user_scores:
                user_result = await self.db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                user_scores[user_id] = {
                    "user_id": str(user_id),
                    "display_name": user.display_name if user else "Anonymous",
                    "email": user.email if user else "",
                    "score": 0,
                    "document_uploads": 0,
                    "conversations": 0,
                    "messages": 0,
                }
            user_scores[user_id]["conversations"] = entry["conversation_count"]
            user_scores[user_id]["score"] += entry["conversation_count"] * 2

        # Get messages
        chat_leaderboard = await self.get_chat_activity_leaderboard(timeframe, limit=100)
        for entry in chat_leaderboard:
            user_id = UUID(entry["user_id"])
            if user_id not in user_scores:
                user_result = await self.db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                user_scores[user_id] = {
                    "user_id": str(user_id),
                    "display_name": user.display_name if user else "Anonymous",
                    "email": user.email if user else "",
                    "score": 0,
                    "document_uploads": 0,
                    "conversations": 0,
                    "messages": 0,
                }
            user_scores[user_id]["messages"] = entry["message_count"]
            user_scores[user_id]["score"] += entry["message_count"] * 1

        # Sort by score and assign ranks
        sorted_users = sorted(
            user_scores.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        leaderboard = []
        for rank, user_data in enumerate(sorted_users[:limit], start=1):
            leaderboard.append({
                "rank": rank,
                "user_id": user_data["user_id"],
                "display_name": user_data["display_name"],
                "email": user_data["email"],
                "total_score": user_data["score"],
                "breakdown": {
                    "document_uploads": user_data["document_uploads"],
                    "conversations": user_data["conversations"],
                    "messages": user_data["messages"],
                },
            })

        logger.info(
            "overall_leaderboard_generated",
            timeframe=timeframe,
            count=len(leaderboard),
        )

        return leaderboard

    # ========================================================================
    # User Statistics
    # ========================================================================

    async def get_user_statistics(self, user_id: UUID) -> dict:
        """
        Get detailed statistics for a specific user.

        Args:
            user_id: ID of user

        Returns:
            User statistics and rank
        """
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Document uploads
        doc_count_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.uploaded_by_user_id == user_id)
        )
        doc_count = doc_count_result.scalar()

        # Conversations
        conv_count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        conv_count = conv_count_result.scalar()

        # Messages
        msg_count_result = await self.db.execute(
            select(func.count(Message.id)).where(
                and_(Message.sender_user_id == user_id, Message.sender_type == "user")
            )
        )
        msg_count = msg_count_result.scalar()

        # Calculate overall score
        overall_score = (doc_count * 10) + (conv_count * 2) + (msg_count * 1)

        # Get rank in overall leaderboard
        overall_leaderboard = await self.get_overall_leaderboard(timeframe="all_time", limit=1000)
        rank = None
        for entry in overall_leaderboard:
            if entry["user_id"] == str(user_id):
                rank = entry["rank"]
                break

        return {
            "user_id": str(user_id),
            "display_name": user.display_name or "Anonymous",
            "email": user.email,
            "statistics": {
                "document_uploads": doc_count,
                "conversations": conv_count,
                "messages": msg_count,
                "overall_score": overall_score,
            },
            "rank": rank,
            "member_since": user.created_at.isoformat(),
        }
