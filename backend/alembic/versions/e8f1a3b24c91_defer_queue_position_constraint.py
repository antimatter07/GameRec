"""make uq_queue_user_position deferrable

Revision ID: e8f1a3b24c91
Revises: c7d2e4f1a8b3
Create Date: 2026-04-21 00:00:00.000000

The non-deferred unique constraint on (user_id, position) causes intermittent
500 errors when dequeuing a game. PostgreSQL checks the constraint per-row as
the UPDATE runs — if it processes row N+1 before row N during the compact-shift,
the new value for N+1 collides with the still-existing value at N. Making the
constraint DEFERRABLE INITIALLY DEFERRED moves the check to commit time, where
all writes are already complete.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'e8f1a3b24c91'
down_revision: Union[str, None] = 'c7d2e4f1a8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE play_queue_entries DROP CONSTRAINT uq_queue_user_position")
    op.execute(
        "ALTER TABLE play_queue_entries "
        "ADD CONSTRAINT uq_queue_user_position "
        "UNIQUE (user_id, position) "
        "DEFERRABLE INITIALLY DEFERRED"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE play_queue_entries DROP CONSTRAINT uq_queue_user_position")
    op.execute(
        "ALTER TABLE play_queue_entries "
        "ADD CONSTRAINT uq_queue_user_position "
        "UNIQUE (user_id, position)"
    )
