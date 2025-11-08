"""Add file storage tables for MinIO integration

Revision ID: 20251107_1300
Revises: 20251107_1200
Create Date: 2025-11-07 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '20251107_1300'
down_revision: Union[str, None] = '20251107_1200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create file storage tables."""

    # Create stored_files table
    op.create_table(
        'stored_files',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True),

        # File identification
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),

        # MinIO storage details
        sa.Column('bucket', sa.String(100), nullable=False),
        sa.Column('object_name', sa.String(500), nullable=False, unique=True),

        # File metadata
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=False),

        # Purpose/Use Case
        sa.Column('purpose', sa.String(50), nullable=True),  # rag_corpus, ticket_attachment, generated_image, user_upload, islamic_resource

        # File attributes
        sa.Column('width', sa.Integer, nullable=True),
        sa.Column('height', sa.Integer, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),

        # Audio-specific metadata (for Islamic resources)
        sa.Column('audio_category', sa.String(50), nullable=True),  # quran, hadith, dua, mafatih, ziyarat, lecture, user_voice
        sa.Column('reciter_name', sa.String(100), nullable=True),  # Name of Quran reciter or speaker
        sa.Column('audio_language', sa.String(10), nullable=True),  # ar, fa, en, etc.
        sa.Column('quran_surah', sa.Integer, nullable=True),  # Quran chapter number (1-114)
        sa.Column('quran_ayah_start', sa.Integer, nullable=True),  # Starting verse number
        sa.Column('quran_ayah_end', sa.Integer, nullable=True),  # Ending verse number
        sa.Column('transcript_text', sa.String, nullable=True),  # ASR transcribed text
        sa.Column('audio_quality', sa.String(20), nullable=True),  # low, medium, high, hd

        # Access control
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('access_url', sa.String(1000), nullable=True),

        # Processing status
        sa.Column('is_processed', sa.Boolean, default=True),
        sa.Column('processing_status', sa.String(50), nullable=True),

        # Security
        sa.Column('is_scanned', sa.Boolean, default=False),
        sa.Column('scan_result', sa.String(50), nullable=True),

        # Usage tracking
        sa.Column('download_count', sa.Integer, default=0),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),

        # Cost tracking
        sa.Column('storage_cost_usd', sa.Numeric(10, 6), nullable=True),

        # Additional metadata
        sa.Column('metadata', JSONB, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.CheckConstraint("file_type IN ('image', 'document', 'audio', 'video', 'other')", name='check_file_type'),
        sa.CheckConstraint('file_size_bytes >= 0', name='check_file_size'),
        sa.CheckConstraint('download_count >= 0', name='check_download_count'),
    )

    # Create indexes for stored_files
    op.create_index('idx_stored_files_user_id', 'stored_files', ['user_id'])
    op.create_index('idx_stored_files_conversation_id', 'stored_files', ['conversation_id'])
    op.create_index('idx_stored_files_file_type', 'stored_files', ['file_type'])
    op.create_index('idx_stored_files_bucket', 'stored_files', ['bucket'])
    op.create_index('idx_stored_files_created_at', 'stored_files', ['created_at'])

    # Create user_storage_quotas table
    op.create_table(
        'user_storage_quotas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),

        # Quota limits (in bytes)
        sa.Column('quota_limit_bytes', sa.Integer, nullable=False),

        # Current usage (in bytes)
        sa.Column('total_used_bytes', sa.Integer, default=0),

        # Usage breakdown by type
        sa.Column('images_used_bytes', sa.Integer, default=0),
        sa.Column('documents_used_bytes', sa.Integer, default=0),
        sa.Column('audio_used_bytes', sa.Integer, default=0),
        sa.Column('other_used_bytes', sa.Integer, default=0),

        # File counts
        sa.Column('total_files', sa.Integer, default=0),

        # Cost tracking
        sa.Column('total_storage_cost_usd', sa.Numeric(10, 4), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Constraints
        sa.CheckConstraint('quota_limit_bytes >= 0', name='check_quota_limit'),
        sa.CheckConstraint('total_used_bytes >= 0', name='check_total_used'),
        sa.CheckConstraint('total_files >= 0', name='check_total_files'),
    )

    # Create indexes for user_storage_quotas
    op.create_index('idx_user_storage_quotas_user_id', 'user_storage_quotas', ['user_id'])


def downgrade() -> None:
    """Drop file storage tables."""

    # Drop indexes first
    op.drop_index('idx_user_storage_quotas_user_id', table_name='user_storage_quotas')
    op.drop_index('idx_stored_files_created_at', table_name='stored_files')
    op.drop_index('idx_stored_files_bucket', table_name='stored_files')
    op.drop_index('idx_stored_files_file_type', table_name='stored_files')
    op.drop_index('idx_stored_files_conversation_id', table_name='stored_files')
    op.drop_index('idx_stored_files_user_id', table_name='stored_files')

    # Drop tables
    op.drop_table('user_storage_quotas')
    op.drop_table('stored_files')
