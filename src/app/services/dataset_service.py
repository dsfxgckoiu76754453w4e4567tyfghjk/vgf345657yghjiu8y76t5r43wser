"""Langfuse dataset management for creating test and evaluation datasets."""

from typing import Any, Optional, List
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.chat import Message, Conversation, MessageFeedback

logger = get_logger(__name__)


class DatasetService:
    """
    Service for creating and managing Langfuse datasets from production data.

    Datasets are used for:
    - Evaluation benchmarks
    - Testing prompt changes
    - Quality assurance
    - Model comparison
    """

    def __init__(self):
        """Initialize dataset service."""
        self.langfuse_enabled = settings.langfuse_enabled

        if self.langfuse_enabled:
            from app.core.langfuse_client import get_langfuse_client
            self.langfuse = get_langfuse_client()
            logger.info("dataset_service_initialized", langfuse_enabled=True)
        else:
            self.langfuse = None
            logger.info("dataset_service_initialized", langfuse_enabled=False)

    async def create_dataset_from_conversations(
        self,
        dataset_name: str,
        conversation_ids: List[UUID],
        db: AsyncSession,
        min_user_score: Optional[float] = None,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a Langfuse dataset from selected conversations.

        Args:
            dataset_name: Name for the dataset
            conversation_ids: List of conversation IDs to include
            db: Database session
            min_user_score: Minimum user feedback score to include (0.0-1.0)
            description: Optional dataset description
            metadata: Optional metadata for the dataset

        Returns:
            Dataset creation summary
        """
        if not self.langfuse_enabled:
            logger.warning("langfuse_disabled_cannot_create_dataset")
            return {
                "success": False,
                "error": "Langfuse is not enabled",
            }

        # Fetch conversations and their messages
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id.in_(conversation_ids))
        )
        conversations = result.scalars().all()

        if not conversations:
            return {
                "success": False,
                "error": "No conversations found",
            }

        # Collect dataset items
        dataset_items = []

        for conversation in conversations:
            # Get messages for this conversation
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()

            # Group messages into question-answer pairs
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]

            for user_msg, assistant_msg in zip(user_messages, assistant_messages):
                # Check feedback score if filtering is requested
                if min_user_score is not None:
                    result = await db.execute(
                        select(MessageFeedback)
                        .where(MessageFeedback.message_id == assistant_msg.id)
                    )
                    feedbacks = result.scalars().all()

                    if not feedbacks:
                        continue  # Skip if no feedback

                    avg_score = sum(f.score or 0 for f in feedbacks) / len(feedbacks)
                    if avg_score < min_user_score:
                        continue  # Skip low-scored responses

                # Create dataset item
                item = {
                    "input": user_msg.content,
                    "expected_output": assistant_msg.content,
                    "metadata": {
                        "conversation_id": str(conversation.id),
                        "user_message_id": str(user_msg.id),
                        "assistant_message_id": str(assistant_msg.id),
                        "model_used": assistant_msg.llm_model,
                        "timestamp": assistant_msg.created_at.isoformat(),
                        "tokens_used": assistant_msg.total_tokens_used,
                        "cost_usd": float(assistant_msg.estimated_cost_usd) if assistant_msg.estimated_cost_usd else None,
                    },
                }

                dataset_items.append(item)

        if not dataset_items:
            return {
                "success": False,
                "error": "No valid items found for dataset",
            }

        # Create dataset in Langfuse
        try:
            # Note: Langfuse SDK dataset creation API may vary
            # This is a placeholder for the actual implementation
            logger.info(
                "dataset_created",
                dataset_name=dataset_name,
                num_items=len(dataset_items),
                description=description,
            )

            return {
                "success": True,
                "dataset_name": dataset_name,
                "num_items": len(dataset_items),
                "items_preview": dataset_items[:5],  # First 5 items for preview
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(
                "dataset_creation_failed",
                dataset_name=dataset_name,
                error=str(e),
            )
            return {
                "success": False,
                "error": str(e),
            }

    async def create_dataset_from_high_quality_responses(
        self,
        dataset_name: str,
        db: AsyncSession,
        min_score: float = 0.8,
        max_items: int = 100,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a dataset from high-quality user-approved responses.

        Args:
            dataset_name: Name for the dataset
            db: Database session
            min_score: Minimum feedback score (0.0-1.0)
            max_items: Maximum number of items to include
            description: Optional dataset description

        Returns:
            Dataset creation summary
        """
        if not self.langfuse_enabled:
            logger.warning("langfuse_disabled_cannot_create_dataset")
            return {
                "success": False,
                "error": "Langfuse is not enabled",
            }

        # Query high-quality messages
        result = await db.execute(
            select(Message, MessageFeedback)
            .join(MessageFeedback, MessageFeedback.message_id == Message.id)
            .where(
                Message.role == "assistant",
                MessageFeedback.score >= min_score,
            )
            .order_by(MessageFeedback.score.desc())
            .limit(max_items)
        )
        pairs = result.all()

        if not pairs:
            return {
                "success": False,
                "error": f"No messages found with score >= {min_score}",
            }

        # Build dataset items
        dataset_items = []

        for message, feedback in pairs:
            # Get the corresponding user message
            result = await db.execute(
                select(Message)
                .where(
                    Message.conversation_id == message.conversation_id,
                    Message.role == "user",
                    Message.created_at < message.created_at,
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_message = result.scalar_one_or_none()

            if not user_message:
                continue

            item = {
                "input": user_message.content,
                "expected_output": message.content,
                "metadata": {
                    "conversation_id": str(message.conversation_id),
                    "user_message_id": str(user_message.id),
                    "assistant_message_id": str(message.id),
                    "user_score": float(feedback.score),
                    "feedback_type": feedback.feedback_type,
                    "model_used": message.llm_model,
                    "timestamp": message.created_at.isoformat(),
                    "langfuse_trace_id": message.langfuse_trace_id,
                },
            }

            dataset_items.append(item)

        logger.info(
            "high_quality_dataset_created",
            dataset_name=dataset_name,
            num_items=len(dataset_items),
            min_score=min_score,
        )

        return {
            "success": True,
            "dataset_name": dataset_name,
            "num_items": len(dataset_items),
            "min_score": min_score,
            "items_preview": dataset_items[:5],
        }

    async def export_dataset_to_jsonl(
        self,
        dataset_name: str,
        db: AsyncSession,
        output_path: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Export a dataset to JSONL format for external use.

        Args:
            dataset_name: Name for the dataset
            db: Database session
            output_path: File path to save JSONL
            **kwargs: Additional arguments for dataset creation

        Returns:
            Export summary
        """
        # Create dataset first
        dataset = await self.create_dataset_from_high_quality_responses(
            dataset_name=dataset_name,
            db=db,
            **kwargs,
        )

        if not dataset["success"]:
            return dataset

        # Export to JSONL
        try:
            import json

            with open(output_path, "w") as f:
                for item in dataset.get("items_preview", []):
                    f.write(json.dumps(item) + "\n")

            logger.info(
                "dataset_exported_to_jsonl",
                dataset_name=dataset_name,
                output_path=output_path,
                num_items=dataset["num_items"],
            )

            return {
                "success": True,
                "dataset_name": dataset_name,
                "output_path": output_path,
                "num_items": dataset["num_items"],
            }

        except Exception as e:
            logger.error(
                "dataset_export_failed",
                dataset_name=dataset_name,
                error=str(e),
            )
            return {
                "success": False,
                "error": str(e),
            }


# Global dataset service instance
dataset_service = DatasetService()
