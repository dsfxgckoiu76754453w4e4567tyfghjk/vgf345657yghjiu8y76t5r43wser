"""Conversation management API endpoints."""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.services.openrouter_service import OpenRouterService

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class ConversationCreateRequest(BaseModel):
    """Conversation creation request."""

    title: str | None = Field(None, max_length=200, description="Optional conversation title")
    mode: str = Field("standard", description="Conversation mode (standard, fast, scholarly, etc.)")
    is_anonymous: bool = Field(False, description="Anonymous conversation")


class ConversationUpdateRequest(BaseModel):
    """Conversation update request."""

    title: str | None = Field(None, max_length=200, description="Conversation title")
    mode: str | None = Field(None, description="Conversation mode")
    is_active: bool | None = Field(None, description="Active status")


class ConversationResponse(BaseModel):
    """Conversation response."""

    id: UUID
    user_id: UUID | None
    title: str | None
    is_title_auto_generated: bool
    mode: str
    is_anonymous: bool
    is_active: bool
    message_count: int
    total_tokens_used: int
    created_at: str
    updated_at: str
    last_message_at: str | None


class ConversationListResponse(BaseModel):
    """List of conversations."""

    conversations: List[ConversationResponse]
    total: int


class MessageResponse(BaseModel):
    """Message response."""

    id: UUID
    role: str
    content: str
    model_used: str | None
    tokens_used: int | None
    cached_tokens_read: int | None
    cache_discount_usd: float | None
    created_at: str


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with messages."""

    id: UUID
    user_id: UUID | None
    title: str | None
    is_title_auto_generated: bool
    mode: str
    is_anonymous: bool
    is_active: bool
    message_count: int
    total_tokens_used: int
    created_at: str
    updated_at: str
    last_message_at: str | None
    messages: List[MessageResponse]


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request_data: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """
    Create a new conversation.

    - **title**: Optional conversation title
    - **mode**: Conversation mode (standard, fast, scholarly, deep_search, filtered)
    - **is_anonymous**: Create anonymous conversation

    Returns created conversation.
    """
    try:
        conversation = Conversation(
            user_id=current_user.id if not request_data.is_anonymous else None,
            title=request_data.title,
            is_title_auto_generated=request_data.title is None,
            mode=request_data.mode,
            is_anonymous=request_data.is_anonymous,
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.info(
            "conversation_created",
            user_id=str(current_user.id),
            conversation_id=str(conversation.id),
            mode=conversation.mode,
        )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_title_auto_generated=conversation.is_title_auto_generated,
            mode=conversation.mode,
            is_anonymous=conversation.is_anonymous,
            is_active=conversation.is_active,
            message_count=conversation.message_count,
            total_tokens_used=conversation.total_tokens_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        )

    except Exception as e:
        logger.error("conversation_creation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    List user's conversations.

    - **limit**: Maximum conversations to return (default: 50)
    - **offset**: Number of conversations to skip (default: 0)
    - **include_inactive**: Include inactive conversations

    Returns list of conversations sorted by last activity.
    """
    try:
        query = select(Conversation).where(Conversation.user_id == current_user.id)

        if not include_inactive:
            query = query.where(Conversation.is_active == True)

        query = query.order_by(desc(Conversation.last_message_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        conversations = result.scalars().all()

        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=conv.id,
                    user_id=conv.user_id,
                    title=conv.title,
                    is_title_auto_generated=conv.is_title_auto_generated,
                    mode=conv.mode,
                    is_anonymous=conv.is_anonymous,
                    is_active=conv.is_active,
                    message_count=conv.message_count,
                    total_tokens_used=conv.total_tokens_used,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                    last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
                )
                for conv in conversations
            ],
            total=len(conversations),
        )

    except Exception as e:
        logger.error("list_conversations_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    """
    Get a conversation with all messages.

    - **conversation_id**: Conversation ID

    Returns conversation details with message history.
    """
    try:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Load messages
        messages_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = messages_result.scalars().all()

        return ConversationDetailResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_title_auto_generated=conversation.is_title_auto_generated,
            mode=conversation.mode,
            is_anonymous=conversation.is_anonymous,
            is_active=conversation.is_active,
            message_count=conversation.message_count,
            total_tokens_used=conversation.total_tokens_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    model_used=msg.model_used,
                    tokens_used=msg.tokens_used,
                    cached_tokens_read=msg.cached_tokens_read,
                    cache_discount_usd=float(msg.cache_discount_usd) if msg.cache_discount_usd else None,
                    created_at=msg.created_at.isoformat(),
                )
                for msg in messages
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request_data: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """
    Update a conversation.

    - **conversation_id**: Conversation ID
    - **title**: Update title
    - **mode**: Update mode
    - **is_active**: Update active status

    Returns updated conversation.
    """
    try:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Update fields
        if request_data.title is not None:
            conversation.title = request_data.title
            conversation.is_title_auto_generated = False

        if request_data.mode is not None:
            conversation.mode = request_data.mode

        if request_data.is_active is not None:
            conversation.is_active = request_data.is_active

        await db.commit()
        await db.refresh(conversation)

        logger.info(
            "conversation_updated",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
        )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_title_auto_generated=conversation.is_title_auto_generated,
            mode=conversation.mode,
            is_anonymous=conversation.is_anonymous,
            is_active=conversation.is_active,
            message_count=conversation.message_count,
            total_tokens_used=conversation.total_tokens_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_conversation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a conversation and all its messages.

    - **conversation_id**: Conversation ID

    Permanently deletes the conversation and all associated messages.
    """
    try:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        await db.delete(conversation)
        await db.commit()

        logger.info(
            "conversation_deleted",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_conversation_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


@router.post("/{conversation_id}/generate-title", response_model=ConversationResponse)
async def generate_conversation_title(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """
    Auto-generate a title for the conversation based on messages.

    - **conversation_id**: Conversation ID

    Analyzes the first few messages and generates a descriptive title.
    Returns updated conversation with new title.
    """
    try:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Get first few messages
        messages_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(4)
        )
        messages = messages_result.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation has no messages",
            )

        # Build context from messages
        context = "\n".join([f"{msg.role}: {msg.content[:200]}" for msg in messages])

        # Use OpenRouter to generate title
        openrouter = OpenRouterService()
        result = await openrouter.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Generate a short, descriptive title (max 50 characters) for this conversation. Return only the title, nothing else.",
                },
                {
                    "role": "user",
                    "content": f"Conversation:\n{context}",
                },
            ],
            model="openai/gpt-4o-mini",  # Use fast, cheap model
            max_tokens=50,
            temperature=0.7,
        )

        generated_title = result["choices"][0]["message"]["content"].strip().strip('"')

        # Update conversation
        conversation.title = generated_title[:200]  # Ensure max length
        conversation.is_title_auto_generated = True

        await db.commit()
        await db.refresh(conversation)

        logger.info(
            "conversation_title_generated",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
            title=generated_title,
        )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_title_auto_generated=conversation.is_title_auto_generated,
            mode=conversation.mode,
            is_anonymous=conversation.is_anonymous,
            is_active=conversation.is_active,
            message_count=conversation.message_count,
            total_tokens_used=conversation.total_tokens_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_title_error", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate title",
        )
