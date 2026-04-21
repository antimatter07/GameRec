"""queue position constraint: DEFERRABLE INITIALLY IMMEDIATE

Revision ID: f3c9d2e7a841
Revises: e8f1a3b24c91
Create Date: 2026-04-21 00:00:00.000000

Replaces the INITIALLY DEFERRED constraint added in e8f1a3b24c91 with
INITIALLY IMMEDIATE so per-statement constraint checking is the default for
all operations. Only dequeue and advance_queue_after_completion explicitly
defer the constraint within their transaction via SET CONSTRAINTS, keeping
the compact-shift UPDATE safe without silencing early checks everywhere else.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'f3c9d2e7a841'
down_revision: Union[str, None] = 'e8f1a3b24c91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE play_queue_entries DROP CONSTRAINT uq_queue_user_position")
    op.execute(
        "ALTER TABLE play_queue_entries "
        "ADD CONSTRAINT uq_queue_user_position "
        "UNIQUE (user_id, position) DEFERRABLE INITIALLY IMMEDIATE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE play_queue_entries DROP CONSTRAINT uq_queue_user_position")
    op.execute(
        "ALTER TABLE play_queue_entries "
        "ADD CONSTRAINT uq_queue_user_position "
        "UNIQUE (user_id, position) DEFERRABLE INITIALLY DEFERRED"
    )
