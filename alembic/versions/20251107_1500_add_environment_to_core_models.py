"""Add environment promotion support to core models (User, Conversation, Message)

Revision ID: 20251107_1500
Revises: 20251107_1400
Create Date: 2025-11-07 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# revision identifiers, used by Alembic.
revision: str = '20251107_1500'
down_revision: Union[str, None] = '20251107_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add environment promotion fields to core models."""

    # ========================================================================
    # Step 1: Add EnvironmentPromotionMixin fields to users table
    # ========================================================================

    # Environment tracking
    op.add_column(
        'users',
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            server_default='prod',
            comment='Environment: dev, stage, prod',
        )
    )
    op.create_index('idx_users_environment', 'users', ['environment'])

    # Test data detection
    op.add_column(
        'users',
        sa.Column(
            'is_test_data',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='True if this is test/dummy data',
        )
    )
    op.create_index('idx_users_is_test_data', 'users', ['is_test_data'])

    op.add_column(
        'users',
        sa.Column(
            'test_data_reason',
            sa.String(200),
            nullable=True,
            comment='Why marked as test data',
        )
    )

    # Promotion support
    op.add_column(
        'users',
        sa.Column(
            'is_promotable',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Can this item be promoted between environments?',
        )
    )
    op.create_index('idx_users_is_promotable', 'users', ['is_promotable'])

    op.add_column(
        'users',
        sa.Column(
            'promotion_status',
            sa.String(20),
            nullable=True,
            server_default='draft',
            comment='draft, approved, promoted, deprecated',
        )
    )
    op.create_index('idx_users_promotion_status', 'users', ['promotion_status'])

    op.add_column(
        'users',
        sa.Column(
            'promoted_from_environment',
            sa.String(10),
            nullable=True,
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'promoted_to_environments',
            ARRAY(sa.String),
            nullable=True,
            server_default='{}',
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )

    # Source tracking
    op.add_column(
        'users',
        sa.Column(
            'source_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_index('idx_users_source_id', 'users', ['source_id'])

    op.add_column(
        'users',
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=True,
        )
    )

    # ========================================================================
    # Step 2: Add EnvironmentPromotionMixin fields to conversations table
    # ========================================================================

    # Environment tracking
    op.add_column(
        'conversations',
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            server_default='prod',
            comment='Environment: dev, stage, prod',
        )
    )
    op.create_index('idx_conversations_environment', 'conversations', ['environment'])

    # Test data detection
    op.add_column(
        'conversations',
        sa.Column(
            'is_test_data',
            sa.Boolean,
            nullable=False,
            server_default='false',
        )
    )
    op.create_index('idx_conversations_is_test_data', 'conversations', ['is_test_data'])

    op.add_column(
        'conversations',
        sa.Column(
            'test_data_reason',
            sa.String(200),
            nullable=True,
        )
    )

    # Promotion support
    op.add_column(
        'conversations',
        sa.Column(
            'is_promotable',
            sa.Boolean,
            nullable=False,
            server_default='false',
        )
    )
    op.create_index('idx_conversations_is_promotable', 'conversations', ['is_promotable'])

    op.add_column(
        'conversations',
        sa.Column(
            'promotion_status',
            sa.String(20),
            nullable=True,
            server_default='draft',
        )
    )
    op.create_index('idx_conversations_promotion_status', 'conversations', ['promotion_status'])

    op.add_column(
        'conversations',
        sa.Column(
            'promoted_from_environment',
            sa.String(10),
            nullable=True,
        )
    )

    op.add_column(
        'conversations',
        sa.Column(
            'promoted_to_environments',
            ARRAY(sa.String),
            nullable=True,
            server_default='{}',
        )
    )

    op.add_column(
        'conversations',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        )
    )

    op.add_column(
        'conversations',
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )

    # Source tracking
    op.add_column(
        'conversations',
        sa.Column(
            'source_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_index('idx_conversations_source_id', 'conversations', ['source_id'])

    op.add_column(
        'conversations',
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=True,
        )
    )

    # ========================================================================
    # Step 3: Add EnvironmentPromotionMixin fields to messages table
    # ========================================================================

    # Environment tracking
    op.add_column(
        'messages',
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            server_default='prod',
            comment='Environment: dev, stage, prod',
        )
    )
    op.create_index('idx_messages_environment', 'messages', ['environment'])

    # Test data detection
    op.add_column(
        'messages',
        sa.Column(
            'is_test_data',
            sa.Boolean,
            nullable=False,
            server_default='false',
        )
    )
    op.create_index('idx_messages_is_test_data', 'messages', ['is_test_data'])

    op.add_column(
        'messages',
        sa.Column(
            'test_data_reason',
            sa.String(200),
            nullable=True,
        )
    )

    # Promotion support
    op.add_column(
        'messages',
        sa.Column(
            'is_promotable',
            sa.Boolean,
            nullable=False,
            server_default='false',
        )
    )
    op.create_index('idx_messages_is_promotable', 'messages', ['is_promotable'])

    op.add_column(
        'messages',
        sa.Column(
            'promotion_status',
            sa.String(20),
            nullable=True,
            server_default='draft',
        )
    )
    op.create_index('idx_messages_promotion_status', 'messages', ['promotion_status'])

    op.add_column(
        'messages',
        sa.Column(
            'promoted_from_environment',
            sa.String(10),
            nullable=True,
        )
    )

    op.add_column(
        'messages',
        sa.Column(
            'promoted_to_environments',
            ARRAY(sa.String),
            nullable=True,
            server_default='{}',
        )
    )

    op.add_column(
        'messages',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        )
    )

    op.add_column(
        'messages',
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )

    # Source tracking
    op.add_column(
        'messages',
        sa.Column(
            'source_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_index('idx_messages_source_id', 'messages', ['source_id'])

    op.add_column(
        'messages',
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=True,
        )
    )

    # Note: messages.updated_at field will be added by TimestampMixin
    # but messages table might not have it yet from original schema
    # Add it if it doesn't exist
    # This will be handled by checking column existence in a separate operation


def downgrade() -> None:
    """Remove environment promotion fields from core models."""

    # Remove from messages
    op.drop_column('messages', 'source_environment')
    op.drop_index('idx_messages_source_id', table_name='messages')
    op.drop_column('messages', 'source_id')
    op.drop_column('messages', 'promoted_by_user_id')
    op.drop_column('messages', 'promoted_at')
    op.drop_column('messages', 'promoted_to_environments')
    op.drop_column('messages', 'promoted_from_environment')
    op.drop_index('idx_messages_promotion_status', table_name='messages')
    op.drop_column('messages', 'promotion_status')
    op.drop_index('idx_messages_is_promotable', table_name='messages')
    op.drop_column('messages', 'is_promotable')
    op.drop_column('messages', 'test_data_reason')
    op.drop_index('idx_messages_is_test_data', table_name='messages')
    op.drop_column('messages', 'is_test_data')
    op.drop_index('idx_messages_environment', table_name='messages')
    op.drop_column('messages', 'environment')

    # Remove from conversations
    op.drop_column('conversations', 'source_environment')
    op.drop_index('idx_conversations_source_id', table_name='conversations')
    op.drop_column('conversations', 'source_id')
    op.drop_column('conversations', 'promoted_by_user_id')
    op.drop_column('conversations', 'promoted_at')
    op.drop_column('conversations', 'promoted_to_environments')
    op.drop_column('conversations', 'promoted_from_environment')
    op.drop_index('idx_conversations_promotion_status', table_name='conversations')
    op.drop_column('conversations', 'promotion_status')
    op.drop_index('idx_conversations_is_promotable', table_name='conversations')
    op.drop_column('conversations', 'is_promotable')
    op.drop_column('conversations', 'test_data_reason')
    op.drop_index('idx_conversations_is_test_data', table_name='conversations')
    op.drop_column('conversations', 'is_test_data')
    op.drop_index('idx_conversations_environment', table_name='conversations')
    op.drop_column('conversations', 'environment')

    # Remove from users
    op.drop_column('users', 'source_environment')
    op.drop_index('idx_users_source_id', table_name='users')
    op.drop_column('users', 'source_id')
    op.drop_column('users', 'promoted_by_user_id')
    op.drop_column('users', 'promoted_at')
    op.drop_column('users', 'promoted_to_environments')
    op.drop_column('users', 'promoted_from_environment')
    op.drop_index('idx_users_promotion_status', table_name='users')
    op.drop_column('users', 'promotion_status')
    op.drop_index('idx_users_is_promotable', table_name='users')
    op.drop_column('users', 'is_promotable')
    op.drop_column('users', 'test_data_reason')
    op.drop_index('idx_users_is_test_data', table_name='users')
    op.drop_column('users', 'is_test_data')
    op.drop_index('idx_users_environment', table_name='users')
    op.drop_column('users', 'environment')
