"""Create performance indexes.

Revision ID: create_indexes
Revises:
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create indexes for performance optimization."""

    # User indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_is_verified', 'users', ['is_verified'])
    op.create_index('idx_users_is_banned', 'users', ['is_banned'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # OTP Code indexes
    op.create_index('idx_otp_codes_user_id', 'otp_codes', ['user_id'])
    op.create_index('idx_otp_codes_expires_at', 'otp_codes', ['expires_at'])

    # User Session indexes
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])

    # Document indexes
    op.create_index('idx_documents_document_type', 'documents', ['document_type'])
    op.create_index('idx_documents_uploaded_by', 'documents', ['uploaded_by_user_id'])
    op.create_index('idx_documents_moderation_status', 'documents', ['moderation_status'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])

    # Document Chunk indexes
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_chunks_vector_db_type', 'document_chunks', ['vector_db_type'])

    # Conversation indexes
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])

    # Message indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_sender_user_id', 'messages', ['sender_user_id'])
    op.create_index('idx_messages_sender_type', 'messages', ['sender_type'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])

    # Support Ticket indexes
    op.create_index('idx_support_tickets_user_id', 'support_tickets', ['user_id'])
    op.create_index('idx_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('idx_support_tickets_category', 'support_tickets', ['category'])
    op.create_index('idx_support_tickets_priority', 'support_tickets', ['priority'])
    op.create_index('idx_support_tickets_assigned_to', 'support_tickets', ['assigned_to_admin_id'])
    op.create_index('idx_support_tickets_created_at', 'support_tickets', ['created_at'])

    # Support Ticket Response indexes
    op.create_index('idx_ticket_responses_ticket_id', 'support_ticket_responses', ['ticket_id'])
    op.create_index('idx_ticket_responses_responder', 'support_ticket_responses', ['responder_user_id'])

    # External API Client indexes
    op.create_index('idx_external_api_clients_owner', 'external_api_clients', ['owner_user_id'])
    op.create_index('idx_external_api_clients_is_active', 'external_api_clients', ['is_active'])

    # External API Usage Log indexes
    op.create_index('idx_api_usage_client_id', 'external_api_usage_logs', ['client_id'])
    op.create_index('idx_api_usage_timestamp', 'external_api_usage_logs', ['timestamp'])
    op.create_index('idx_api_usage_status_code', 'external_api_usage_logs', ['status_code'])

    # Marja indexes
    op.create_index('idx_marja_is_active', 'marja', ['is_active'])

    # Admin Activity Log indexes
    op.create_index('idx_admin_activity_admin_id', 'admin_activity_logs', ['admin_user_id'])
    op.create_index('idx_admin_activity_timestamp', 'admin_activity_logs', ['timestamp'])
    op.create_index('idx_admin_activity_action', 'admin_activity_logs', ['action'])

    # Content Moderation Log indexes
    op.create_index('idx_content_mod_moderator', 'content_moderation_logs', ['moderator_user_id'])
    op.create_index('idx_content_mod_content_type', 'content_moderation_logs', ['content_type'])
    op.create_index('idx_content_mod_timestamp', 'content_moderation_logs', ['timestamp'])

    # Composite indexes for common queries
    op.create_index('idx_documents_type_status', 'documents', ['document_type', 'moderation_status'])
    op.create_index('idx_messages_conv_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('idx_tickets_status_priority', 'support_tickets', ['status', 'priority'])


def downgrade() -> None:
    """Drop indexes."""

    # User indexes
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_is_verified')
    op.drop_index('idx_users_is_banned')
    op.drop_index('idx_users_role')
    op.drop_index('idx_users_created_at')

    # OTP Code indexes
    op.drop_index('idx_otp_codes_user_id')
    op.drop_index('idx_otp_codes_expires_at')

    # User Session indexes
    op.drop_index('idx_user_sessions_user_id')
    op.drop_index('idx_user_sessions_expires_at')

    # Document indexes
    op.drop_index('idx_documents_document_type')
    op.drop_index('idx_documents_uploaded_by')
    op.drop_index('idx_documents_moderation_status')
    op.drop_index('idx_documents_created_at')

    # Document Chunk indexes
    op.drop_index('idx_document_chunks_document_id')
    op.drop_index('idx_document_chunks_vector_db_type')

    # Conversation indexes
    op.drop_index('idx_conversations_user_id')
    op.drop_index('idx_conversations_created_at')

    # Message indexes
    op.drop_index('idx_messages_conversation_id')
    op.drop_index('idx_messages_sender_user_id')
    op.drop_index('idx_messages_sender_type')
    op.drop_index('idx_messages_created_at')

    # Support Ticket indexes
    op.drop_index('idx_support_tickets_user_id')
    op.drop_index('idx_support_tickets_status')
    op.drop_index('idx_support_tickets_category')
    op.drop_index('idx_support_tickets_priority')
    op.drop_index('idx_support_tickets_assigned_to')
    op.drop_index('idx_support_tickets_created_at')

    # Support Ticket Response indexes
    op.drop_index('idx_ticket_responses_ticket_id')
    op.drop_index('idx_ticket_responses_responder')

    # External API Client indexes
    op.drop_index('idx_external_api_clients_owner')
    op.drop_index('idx_external_api_clients_is_active')

    # External API Usage Log indexes
    op.drop_index('idx_api_usage_client_id')
    op.drop_index('idx_api_usage_timestamp')
    op.drop_index('idx_api_usage_status_code')

    # Marja indexes
    op.drop_index('idx_marja_is_active')

    # Admin Activity Log indexes
    op.drop_index('idx_admin_activity_admin_id')
    op.drop_index('idx_admin_activity_timestamp')
    op.drop_index('idx_admin_activity_action')

    # Content Moderation Log indexes
    op.drop_index('idx_content_mod_moderator')
    op.drop_index('idx_content_mod_content_type')
    op.drop_index('idx_content_mod_timestamp')

    # Composite indexes
    op.drop_index('idx_documents_type_status')
    op.drop_index('idx_messages_conv_created')
    op.drop_index('idx_tickets_status_priority')
