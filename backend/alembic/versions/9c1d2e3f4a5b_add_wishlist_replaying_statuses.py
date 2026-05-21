"""add wishlist and replaying library statuses

Revision ID: 9c1d2e3f4a5b
Revises: 4f7d3a1b9c22
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "9c1d2e3f4a5b"
down_revision: Union[str, None] = "4f7d3a1b9c22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE librarystatus ADD VALUE IF NOT EXISTS 'WISHLIST'")
    op.execute("ALTER TYPE librarystatus ADD VALUE IF NOT EXISTS 'REPLAYING'")

    # Existing queue rows should stay actionable. Completed/dropped/playing rows
    # no longer belong in Play Next after the gamer-native status cleanup.
    op.execute(
        """
        DELETE FROM play_queue_entries pq
        USING library_entries le
        WHERE pq.entry_id = le.id
          AND le.status::text NOT IN ('BACKLOG', 'REPLAYING')
        """
    )


def downgrade() -> None:
    # PostgreSQL cannot drop enum values safely without recreating the type.
    # Leave the enum values in place on downgrade; older app code simply won't
    # emit them.
    pass
