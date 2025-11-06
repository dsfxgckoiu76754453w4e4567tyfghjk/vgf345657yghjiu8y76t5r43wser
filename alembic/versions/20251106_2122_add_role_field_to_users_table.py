"""Add role field to users table

Revision ID: e43c24cf81ef
Revises: a7ae2d0de4ba
Create Date: 2025-11-06 21:22:35.558087+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e43c24cf81ef'
down_revision: Union[str, None] = 'a7ae2d0de4ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users table with default value 'user'
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
    # Remove server_default after adding the column (keeps it as a model-level default)
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    # Remove role column from users table
    op.drop_column('users', 'role')
