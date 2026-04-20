"""session started_at server default

Revision ID: c7d2e4f1a8b3
Revises: 5207c7732487
Create Date: 2026-04-20 00:00:00.000000

started_at is now server-generated at log time; add DB-level default as a safety net.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7d2e4f1a8b3'
down_revision = '5207c7732487'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'session_logs',
        'started_at',
        server_default=sa.text('now()'),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'session_logs',
        'started_at',
        server_default=None,
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
