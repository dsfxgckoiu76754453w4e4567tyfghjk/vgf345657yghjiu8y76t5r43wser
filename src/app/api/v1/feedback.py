"""User feedback API endpoints with Langfuse integration."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.core.langfuse_client import score_trace
from app.db.base import get_db
from app.models.chat import Message, MessageFeedback
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class FeedbackRequest(BaseModel):
    """User feedback submission request."""

    message_id: UUID = Field(..., description="ID of the message being rated")
    feedback_type: Literal["like", "dislike"] = Field(..., description="Type of feedback")
    dislike_reason: str | None = Field(None, description="Reason for dislike")
    feedback_text: str | None = Field(None, max_length=5000, description="Detailed feedback")
    was_helpful: bool | None = Field(None, description="Was the response helpful?")


class FeedbackResponse(BaseModel):
    """Feedback submission response."""

    feedback_id: UUID
    message_id: UUID
    feedback_type: str
    score: float
    langfuse_submitted: bool


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request_data: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit user feedback on an assistant message.

    - **message_id**: ID of the message being rated
    - **feedback_type**: "like" or "dislike"
    - **dislike_reason**: Optional reason for dislike
    - **feedback_text**: Optional detailed feedback text
    - **was_helpful**: Optional boolean indicating helpfulness

    The feedback is stored in the database and automatically sent to
    Langfuse as a score if Langfuse is enabled.

    Feedback scores:
    - Like: 1.0
    - Dislike: 0.0

    Returns:
    - Feedback ID and confirmation
    """
    try:
        # Get the message
        result = await db.execute(
            select(Message).where(Message.id == request_data.message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Verify message belongs to user's conversation
        from app.models.chat import Conversation

        result = await db.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Allow access if user owns conversation OR it's truly anonymous
        if not conversation.is_truly_anonymous and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Convert feedback to score
        score = 1.0 if request_data.feedback_type == "like" else 0.0

        # Create feedback record
        feedback = MessageFeedback(
            message_id=request_data.message_id,
            user_id=current_user.id,
            feedback_type=request_data.feedback_type,
            dislike_reason=request_data.dislike_reason,
            feedback_text=request_data.feedback_text,
            was_helpful=request_data.was_helpful,
            langfuse_trace_id=message.langfuse_trace_id,
            score=score,
            score_name="user-feedback",
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        # Submit to Langfuse if enabled and trace ID exists
        langfuse_submitted = False
        if settings.langfuse_enabled and message.langfuse_trace_id:
            try:
                score_trace(
                    trace_id=message.langfuse_trace_id,
                    name="user-feedback",
                    value=score,
                    comment=request_data.feedback_text or f"User {request_data.feedback_type}",
                )
                langfuse_submitted = True
                logger.info(
                    "feedback_submitted_to_langfuse",
                    message_id=str(request_data.message_id),
                    trace_id=message.langfuse_trace_id,
                    score=score,
                )
            except Exception as e:
                logger.error(
                    "langfuse_feedback_submission_error",
                    message_id=str(request_data.message_id),
                    error=str(e),
                )

        logger.info(
            "user_feedback_submitted",
            user_id=str(current_user.id),
            message_id=str(request_data.message_id),
            feedback_type=request_data.feedback_type,
            score=score,
        )

        return FeedbackResponse(
            feedback_id=feedback.id,
            message_id=request_data.message_id,
            feedback_type=request_data.feedback_type,
            score=score,
            langfuse_submitted=langfuse_submitted,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "feedback_submission_error",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback",
        )


@router.get("/message/{message_id}")
async def get_message_feedback(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all feedback for a specific message.

    Returns list of feedback entries with user information.
    """
    try:
        # Verify access to message
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Get conversation to verify ownership
        from app.models.chat import Conversation

        result = await db.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Verify access
        if not conversation.is_truly_anonymous and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Get feedback
        result = await db.execute(
            select(MessageFeedback).where(MessageFeedback.message_id == message_id)
        )
        feedbacks = result.scalars().all()

        return {
            "message_id": message_id,
            "feedback_count": len(feedbacks),
            "feedbacks": [
                {
                    "id": f.id,
                    "feedback_type": f.feedback_type,
                    "score": f.score,
                    "was_helpful": f.was_helpful,
                    "dislike_reason": f.dislike_reason,
                    "feedback_text": f.feedback_text,
                    "created_at": f.created_at,
                }
                for f in feedbacks
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_feedback_error",
            message_id=str(message_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback",
        )


@router.get("/stats/conversation/{conversation_id}")
async def get_conversation_feedback_stats(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get feedback statistics for an entire conversation.

    Returns aggregated feedback metrics including like/dislike ratio,
    average score, and most common dislike reasons.
    """
    try:
        # Verify conversation access
        from app.models.chat import Conversation

        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Verify access
        if not conversation.is_truly_anonymous and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Get all feedback for conversation messages
        from sqlalchemy import func

        result = await db.execute(
            select(MessageFeedback)
            .join(Message, MessageFeedback.message_id == Message.id)
            .where(Message.conversation_id == conversation_id)
        )
        feedbacks = result.scalars().all()

        if not feedbacks:
            return {
                "conversation_id": conversation_id,
                "total_feedback": 0,
                "likes": 0,
                "dislikes": 0,
                "average_score": None,
                "like_ratio": None,
            }

        # Calculate statistics
        total = len(feedbacks)
        likes = sum(1 for f in feedbacks if f.feedback_type == "like")
        dislikes = total - likes
        avg_score = sum(f.score or 0 for f in feedbacks) / total if total > 0 else 0

        # Most common dislike reasons
        dislike_reasons = {}
        for f in feedbacks:
            if f.feedback_type == "dislike" and f.dislike_reason:
                dislike_reasons[f.dislike_reason] = dislike_reasons.get(f.dislike_reason, 0) + 1

        return {
            "conversation_id": conversation_id,
            "total_feedback": total,
            "likes": likes,
            "dislikes": dislikes,
            "average_score": round(avg_score, 2),
            "like_ratio": round(likes / total, 2) if total > 0 else 0,
            "most_common_dislike_reasons": dict(
                sorted(dislike_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_feedback_stats_error",
            conversation_id=str(conversation_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback statistics",
        )
