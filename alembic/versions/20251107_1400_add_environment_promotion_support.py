"""Add environment promotion support to all tables

Revision ID: 20251107_1400
Revises: 20251107_1300
Create Date: 2025-11-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision: str = '20251107_1400'
down_revision: Union[str, None] = '20251107_1300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add environment promotion support."""

    # ========================================================================
    # Step 1: Add EnvironmentPromotionMixin fields to stored_files
    # ========================================================================

    # Environment tracking
    op.add_column(
        'stored_files',
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            server_default='prod',
            comment='Environment: dev, stage, prod',
        )
    )
    op.create_index('idx_stored_files_environment', 'stored_files', ['environment'])

    # Test data detection
    op.add_column(
        'stored_files',
        sa.Column(
            'is_test_data',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='True if this is test/dummy data (auto-detected or manually marked)',
        )
    )
    op.create_index('idx_stored_files_is_test_data', 'stored_files', ['is_test_data'])

    op.add_column(
        'stored_files',
        sa.Column(
            'test_data_reason',
            sa.String(200),
            nullable=True,
            comment="Why marked as test data (e.g., 'matches pattern: John Doe')",
        )
    )

    # Promotion support
    op.add_column(
        'stored_files',
        sa.Column(
            'is_promotable',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Can this item be promoted between environments?',
        )
    )
    op.create_index('idx_stored_files_is_promotable', 'stored_files', ['is_promotable'])

    op.add_column(
        'stored_files',
        sa.Column(
            'promotion_status',
            sa.String(20),
            nullable=True,
            server_default='draft',
            comment='draft, approved, promoted, deprecated',
        )
    )
    op.create_index('idx_stored_files_promotion_status', 'stored_files', ['promotion_status'])

    op.add_column(
        'stored_files',
        sa.Column(
            'promoted_from_environment',
            sa.String(10),
            nullable=True,
            comment='Original environment where this was created',
        )
    )

    op.add_column(
        'stored_files',
        sa.Column(
            'promoted_to_environments',
            ARRAY(sa.String),
            nullable=True,
            server_default='{}',
            comment="Promotion history: ['dev', 'stage', 'prod']",
        )
    )

    op.add_column(
        'stored_files',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When this item was promoted',
        )
    )

    op.add_column(
        'stored_files',
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
            comment='User who approved the promotion',
        )
    )

    # Source tracking
    op.add_column(
        'stored_files',
        sa.Column(
            'source_id',
            UUID(as_uuid=True),
            nullable=True,
            comment='ID in source environment (for linking promoted items)',
        )
    )
    op.create_index('idx_stored_files_source_id', 'stored_files', ['source_id'])

    op.add_column(
        'stored_files',
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=True,
            comment='Where this was promoted from',
        )
    )

    # Add is_deleted for SoftDeleteMixin (deleted_at already exists)
    op.add_column(
        'stored_files',
        sa.Column(
            'is_deleted',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Soft delete flag',
        )
    )
    op.create_index('idx_stored_files_is_deleted', 'stored_files', ['is_deleted'])

    # ========================================================================
    # Step 2: Add EnvironmentPromotionMixin fields to user_storage_quotas
    # ========================================================================

    # Environment tracking
    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            server_default='prod',
            comment='Environment: dev, stage, prod',
        )
    )
    op.create_index('idx_user_storage_quotas_environment', 'user_storage_quotas', ['environment'])

    # Test data detection
    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'is_test_data',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='True if this is test/dummy data',
        )
    )
    op.create_index('idx_user_storage_quotas_is_test_data', 'user_storage_quotas', ['is_test_data'])

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'test_data_reason',
            sa.String(200),
            nullable=True,
            comment='Why marked as test data',
        )
    )

    # Promotion support
    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'is_promotable',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Can this item be promoted between environments?',
        )
    )
    op.create_index('idx_user_storage_quotas_is_promotable', 'user_storage_quotas', ['is_promotable'])

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'promotion_status',
            sa.String(20),
            nullable=True,
            server_default='draft',
            comment='draft, approved, promoted, deprecated',
        )
    )
    op.create_index('idx_user_storage_quotas_promotion_status', 'user_storage_quotas', ['promotion_status'])

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'promoted_from_environment',
            sa.String(10),
            nullable=True,
        )
    )

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'promoted_to_environments',
            ARRAY(sa.String),
            nullable=True,
            server_default='{}',
        )
    )

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        )
    )

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )

    # Source tracking
    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'source_id',
            UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_index('idx_user_storage_quotas_source_id', 'user_storage_quotas', ['source_id'])

    op.add_column(
        'user_storage_quotas',
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=True,
        )
    )

    # ========================================================================
    # Step 3: Create environment_promotions table
    # ========================================================================

    op.create_table(
        'environment_promotions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Promotion metadata
        sa.Column(
            'promotion_type',
            sa.String(50),
            nullable=False,
            comment='Type: rag_documents, audio_files, config, multi',
        ),
        sa.Column(
            'source_environment',
            sa.String(10),
            nullable=False,
            comment='Source: dev, stage, prod',
        ),
        sa.Column(
            'target_environment',
            sa.String(10),
            nullable=False,
            comment='Target: dev, stage, prod',
        ),

        # What was promoted
        sa.Column(
            'items_promoted',
            JSONB,
            nullable=False,
            comment='Details of promoted items with IDs and counts',
        ),

        # Execution details
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='Status: pending, in_progress, success, failed, rolled_back',
        ),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            'duration_seconds',
            sa.Integer,
            nullable=True,
            comment='Promotion execution time',
        ),

        # Results
        sa.Column(
            'success_count',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='Number of items successfully promoted',
        ),
        sa.Column(
            'error_count',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='Number of items that failed',
        ),
        sa.Column(
            'errors',
            JSONB,
            nullable=True,
            comment='Error details for failed items',
        ),

        # Audit
        sa.Column(
            'promoted_by_user_id',
            UUID(as_uuid=True),
            nullable=False,
            comment='User who executed the promotion',
        ),
        sa.Column(
            'reason',
            sa.String(500),
            nullable=True,
            comment='Reason for promotion',
        ),

        # Rollback support
        sa.Column(
            'can_rollback',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='Whether this promotion can be rolled back',
        ),
        sa.Column(
            'rollback_data',
            JSONB,
            nullable=True,
            comment='Data needed for rollback (IDs created in target)',
        ),
        sa.Column(
            'rolled_back_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            'rolled_back_by_user_id',
            UUID(as_uuid=True),
            nullable=True,
        ),

        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create indexes for environment_promotions
    op.create_index('idx_environment_promotions_promotion_type', 'environment_promotions', ['promotion_type'])
    op.create_index('idx_environment_promotions_source_environment', 'environment_promotions', ['source_environment'])
    op.create_index('idx_environment_promotions_target_environment', 'environment_promotions', ['target_environment'])
    op.create_index('idx_environment_promotions_status', 'environment_promotions', ['status'])
    op.create_index('idx_environment_promotions_promoted_by_user_id', 'environment_promotions', ['promoted_by_user_id'])

    # ========================================================================
    # Step 4: Create environment_access_logs table
    # ========================================================================

    op.create_table(
        'environment_access_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # User and environment
        sa.Column(
            'user_id',
            UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            comment='Environment accessed: dev, stage, prod',
        ),

        # Access details
        sa.Column(
            'access_type',
            sa.String(50),
            nullable=False,
            comment='Type: login, test_account_create, data_access, api_call',
        ),
        sa.Column(
            'access_time',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        # Context
        sa.Column(
            'ip_address',
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            'user_agent',
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            'reason',
            sa.String(500),
            nullable=True,
            comment='Why accessing this environment (required for prod)',
        ),

        # Additional context
        sa.Column(
            'metadata',
            JSONB,
            nullable=True,
            comment='Additional access context',
        ),
    )

    # Create indexes for environment_access_logs
    op.create_index('idx_environment_access_logs_user_id', 'environment_access_logs', ['user_id'])
    op.create_index('idx_environment_access_logs_environment', 'environment_access_logs', ['environment'])
    op.create_index('idx_environment_access_logs_access_time', 'environment_access_logs', ['access_time'])

    # ========================================================================
    # Step 5: Create developer_actions table
    # ========================================================================

    op.create_table(
        'developer_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Developer and environment
        sa.Column(
            'developer_id',
            UUID(as_uuid=True),
            nullable=False,
            comment='Developer who performed the action',
        ),
        sa.Column(
            'environment',
            sa.String(10),
            nullable=False,
            comment='Environment: dev, stage, prod',
        ),

        # Action details
        sa.Column(
            'action',
            sa.String(100),
            nullable=False,
            comment='Action: create_test_account, delete_test_account, access_user_data, etc.',
        ),
        sa.Column(
            'reason',
            sa.String(500),
            nullable=False,
            comment='Justification for the action (required)',
        ),
        sa.Column(
            'details',
            JSONB,
            nullable=True,
            comment='Additional action details',
        ),

        # Audit context
        sa.Column(
            'ip_address',
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            'user_agent',
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        # Result
        sa.Column(
            'success',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='Whether action succeeded',
        ),
        sa.Column(
            'error_message',
            sa.String(1000),
            nullable=True,
            comment='Error message if action failed',
        ),
    )

    # Create indexes for developer_actions
    op.create_index('idx_developer_actions_developer_id', 'developer_actions', ['developer_id'])
    op.create_index('idx_developer_actions_environment', 'developer_actions', ['environment'])
    op.create_index('idx_developer_actions_action', 'developer_actions', ['action'])
    op.create_index('idx_developer_actions_timestamp', 'developer_actions', ['timestamp'])


def downgrade() -> None:
    """Remove environment promotion support."""

    # Drop developer_actions table
    op.drop_index('idx_developer_actions_timestamp', table_name='developer_actions')
    op.drop_index('idx_developer_actions_action', table_name='developer_actions')
    op.drop_index('idx_developer_actions_environment', table_name='developer_actions')
    op.drop_index('idx_developer_actions_developer_id', table_name='developer_actions')
    op.drop_table('developer_actions')

    # Drop environment_access_logs table
    op.drop_index('idx_environment_access_logs_access_time', table_name='environment_access_logs')
    op.drop_index('idx_environment_access_logs_environment', table_name='environment_access_logs')
    op.drop_index('idx_environment_access_logs_user_id', table_name='environment_access_logs')
    op.drop_table('environment_access_logs')

    # Drop environment_promotions table
    op.drop_index('idx_environment_promotions_promoted_by_user_id', table_name='environment_promotions')
    op.drop_index('idx_environment_promotions_status', table_name='environment_promotions')
    op.drop_index('idx_environment_promotions_target_environment', table_name='environment_promotions')
    op.drop_index('idx_environment_promotions_source_environment', table_name='environment_promotions')
    op.drop_index('idx_environment_promotions_promotion_type', table_name='environment_promotions')
    op.drop_table('environment_promotions')

    # Remove fields from user_storage_quotas
    op.drop_index('idx_user_storage_quotas_source_id', table_name='user_storage_quotas')
    op.drop_column('user_storage_quotas', 'source_environment')
    op.drop_column('user_storage_quotas', 'source_id')
    op.drop_column('user_storage_quotas', 'promoted_by_user_id')
    op.drop_column('user_storage_quotas', 'promoted_at')
    op.drop_column('user_storage_quotas', 'promoted_to_environments')
    op.drop_column('user_storage_quotas', 'promoted_from_environment')
    op.drop_index('idx_user_storage_quotas_promotion_status', table_name='user_storage_quotas')
    op.drop_column('user_storage_quotas', 'promotion_status')
    op.drop_index('idx_user_storage_quotas_is_promotable', table_name='user_storage_quotas')
    op.drop_column('user_storage_quotas', 'is_promotable')
    op.drop_column('user_storage_quotas', 'test_data_reason')
    op.drop_index('idx_user_storage_quotas_is_test_data', table_name='user_storage_quotas')
    op.drop_column('user_storage_quotas', 'is_test_data')
    op.drop_index('idx_user_storage_quotas_environment', table_name='user_storage_quotas')
    op.drop_column('user_storage_quotas', 'environment')

    # Remove fields from stored_files
    op.drop_index('idx_stored_files_is_deleted', table_name='stored_files')
    op.drop_column('stored_files', 'is_deleted')
    op.drop_column('stored_files', 'source_environment')
    op.drop_index('idx_stored_files_source_id', table_name='stored_files')
    op.drop_column('stored_files', 'source_id')
    op.drop_column('stored_files', 'promoted_by_user_id')
    op.drop_column('stored_files', 'promoted_at')
    op.drop_column('stored_files', 'promoted_to_environments')
    op.drop_column('stored_files', 'promoted_from_environment')
    op.drop_index('idx_stored_files_promotion_status', table_name='stored_files')
    op.drop_column('stored_files', 'promotion_status')
    op.drop_index('idx_stored_files_is_promotable', table_name='stored_files')
    op.drop_column('stored_files', 'is_promotable')
    op.drop_column('stored_files', 'test_data_reason')
    op.drop_index('idx_stored_files_is_test_data', table_name='stored_files')
    op.drop_column('stored_files', 'is_test_data')
    op.drop_index('idx_stored_files_environment', table_name='stored_files')
    op.drop_column('stored_files', 'environment')
