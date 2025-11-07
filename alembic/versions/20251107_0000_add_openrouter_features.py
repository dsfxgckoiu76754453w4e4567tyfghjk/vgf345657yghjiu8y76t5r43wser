"""Add OpenRouter advanced features

Revision ID: f9d3e5a7b2c1
Revises: e43c24cf81ef
Create Date: 2025-11-07 00:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9d3e5a7b2c1'
down_revision: Union[str, None] = 'e43c24cf81ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add OpenRouter advanced features:
    1. Prompt caching fields to messages table
    2. Model routing metadata to messages table
    3. Structured output fields to messages table
    4. Message attachments table for multimodal support
    5. Subscription management tables
    6. Image generation tracking table
    7. Model presets table
    """

    # ====================
    # Update messages table
    # ====================

    # Add prompt caching fields
    op.add_column('messages', sa.Column('cached_tokens_read', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('cached_tokens_write', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('cache_discount_usd', sa.Numeric(precision=10, scale=6), nullable=True))
    op.add_column('messages', sa.Column('cache_breakpoint_count', sa.Integer(), nullable=False, server_default='0'))

    # Add reasoning and audio tokens
    op.add_column('messages', sa.Column('reasoning_tokens', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('audio_tokens', sa.Integer(), nullable=True))

    # Add upstream cost tracking
    op.add_column('messages', sa.Column('upstream_inference_cost_usd', sa.Numeric(precision=10, scale=6), nullable=True))

    # Add model routing metadata
    op.add_column('messages', sa.Column('routing_strategy', sa.String(length=50), nullable=True))
    op.add_column('messages', sa.Column('fallback_used', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('messages', sa.Column('models_attempted', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('messages', sa.Column('final_model_used', sa.String(length=100), nullable=True))

    # Add structured output fields
    op.add_column('messages', sa.Column('response_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('messages', sa.Column('structured_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('messages', sa.Column('schema_validation_passed', sa.Boolean(), nullable=False, server_default='true'))

    # Remove server defaults after adding columns
    op.alter_column('messages', 'cache_breakpoint_count', server_default=None)
    op.alter_column('messages', 'fallback_used', server_default=None)
    op.alter_column('messages', 'schema_validation_passed', server_default=None)

    # ====================
    # Create message_attachments table
    # ====================
    op.create_table(
        'message_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attachment_type', sa.String(length=20), nullable=False),
        sa.Column('file_url', sa.String(length=1000), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('processing_cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("attachment_type IN ('image', 'pdf', 'audio')", name='check_attachment_type'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ====================
    # Create subscriptions table
    # ====================
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('billing_cycle', sa.String(length=20), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("plan_type IN ('free', 'premium', 'unlimited', 'enterprise')", name='check_plan_type'),
        sa.CheckConstraint("status IN ('active', 'cancelled', 'expired', 'trial')", name='check_status'),
        sa.CheckConstraint("billing_cycle IN ('monthly', 'yearly')", name='check_billing_cycle'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='unique_user_subscription')
    )
    op.alter_column('subscriptions', 'cancel_at_period_end', server_default=None)

    # ====================
    # Create plan_limits table
    # ====================
    op.create_table(
        'plan_limits',
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('max_messages_per_month', sa.Integer(), nullable=False),
        sa.Column('max_tokens_per_month', sa.Integer(), nullable=False),
        sa.Column('max_images_per_month', sa.Integer(), nullable=False),
        sa.Column('max_documents_per_month', sa.Integer(), nullable=False),
        sa.Column('max_audio_minutes_per_month', sa.Integer(), nullable=False),
        sa.Column('web_search_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('image_generation_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('pdf_processing_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('audio_processing_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('prompt_caching_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('advanced_models_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('presets_limit', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_context_length', sa.Integer(), nullable=True, server_default='4096'),
        sa.Column('priority_support', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('monthly_price_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('yearly_price_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('plan_type')
    )
    op.alter_column('plan_limits', 'web_search_enabled', server_default=None)
    op.alter_column('plan_limits', 'image_generation_enabled', server_default=None)
    op.alter_column('plan_limits', 'pdf_processing_enabled', server_default=None)
    op.alter_column('plan_limits', 'audio_processing_enabled', server_default=None)
    op.alter_column('plan_limits', 'prompt_caching_enabled', server_default=None)
    op.alter_column('plan_limits', 'advanced_models_enabled', server_default=None)
    op.alter_column('plan_limits', 'presets_limit', server_default=None)
    op.alter_column('plan_limits', 'max_context_length', server_default=None)
    op.alter_column('plan_limits', 'priority_support', server_default=None)

    # ====================
    # Create monthly_usage_quotas table
    # ====================
    op.create_table(
        'monthly_usage_quotas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('month_year', sa.String(length=10), nullable=False),
        sa.Column('messages_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('tokens_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('images_generated', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('documents_processed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('audio_minutes_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_cost_usd', sa.Numeric(precision=10, scale=6), nullable=True, server_default='0.0'),
        sa.Column('cache_savings_usd', sa.Numeric(precision=10, scale=6), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'month_year', name='unique_user_month_quota')
    )
    op.alter_column('monthly_usage_quotas', 'messages_used', server_default=None)
    op.alter_column('monthly_usage_quotas', 'tokens_used', server_default=None)
    op.alter_column('monthly_usage_quotas', 'images_generated', server_default=None)
    op.alter_column('monthly_usage_quotas', 'documents_processed', server_default=None)
    op.alter_column('monthly_usage_quotas', 'audio_minutes_used', server_default=None)
    op.alter_column('monthly_usage_quotas', 'total_cost_usd', server_default=None)
    op.alter_column('monthly_usage_quotas', 'cache_savings_usd', server_default=None)

    # ====================
    # Create generated_images table
    # ====================
    op.create_table(
        'generated_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prompt', sa.String(length=2000), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('image_data_url', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=10), nullable=True),
        sa.Column('modalities', sa.String(length=100), nullable=True),
        sa.Column('generation_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ====================
    # Create model_presets table
    # ====================
    op.create_table(
        'model_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('system_prompt', sa.String(), nullable=True),
        sa.Column('temperature', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('top_p', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('model_config', sa.String(), nullable=True),
        sa.Column('provider_preferences', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'slug', name='unique_user_preset_slug')
    )
    op.alter_column('model_presets', 'is_public', server_default=None)
    op.alter_column('model_presets', 'version', server_default=None)


def downgrade() -> None:
    """
    Remove OpenRouter advanced features.
    """

    # Drop new tables
    op.drop_table('model_presets')
    op.drop_table('generated_images')
    op.drop_table('monthly_usage_quotas')
    op.drop_table('plan_limits')
    op.drop_table('subscriptions')
    op.drop_table('message_attachments')

    # Remove columns from messages table
    op.drop_column('messages', 'schema_validation_passed')
    op.drop_column('messages', 'structured_data')
    op.drop_column('messages', 'response_schema')
    op.drop_column('messages', 'final_model_used')
    op.drop_column('messages', 'models_attempted')
    op.drop_column('messages', 'fallback_used')
    op.drop_column('messages', 'routing_strategy')
    op.drop_column('messages', 'upstream_inference_cost_usd')
    op.drop_column('messages', 'audio_tokens')
    op.drop_column('messages', 'reasoning_tokens')
    op.drop_column('messages', 'cache_breakpoint_count')
    op.drop_column('messages', 'cache_discount_usd')
    op.drop_column('messages', 'cached_tokens_write')
    op.drop_column('messages', 'cached_tokens_read')
