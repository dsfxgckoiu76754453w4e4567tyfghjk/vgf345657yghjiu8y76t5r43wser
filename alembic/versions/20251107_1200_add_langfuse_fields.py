"""Add Langfuse tracing and scoring fields

Revision ID: 20251107_1200
Revises: 20251107_0000
Create Date: 2025-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251107_1200'
down_revision: Union[str, None] = '20251107_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Langfuse tracing and scoring fields to messages and feedback."""

    # Add Langfuse fields to messages table
    op.add_column('messages', sa.Column('langfuse_trace_id', sa.String(length=255), nullable=True))
    op.add_column('messages', sa.Column('langfuse_observation_id', sa.String(length=255), nullable=True))

    # Add Langfuse scoring fields to message_feedback table
    op.add_column('message_feedback', sa.Column('langfuse_trace_id', sa.String(length=255), nullable=True))
    op.add_column('message_feedback', sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('message_feedback', sa.Column('score_name', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove Langfuse tracing and scoring fields."""

    # Remove from message_feedback table
    op.drop_column('message_feedback', 'score_name')
    op.drop_column('message_feedback', 'score')
    op.drop_column('message_feedback', 'langfuse_trace_id')

    # Remove from messages table
    op.drop_column('messages', 'langfuse_observation_id')
    op.drop_column('messages', 'langfuse_trace_id')
