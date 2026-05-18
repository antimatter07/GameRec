"""add rawg sync state

Revision ID: 1f2a3b4c5d6e
Revises: 68717b6d59da
Create Date: 2026-05-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1f2a3b4c5d6e"
down_revision: Union[str, None] = "68717b6d59da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rawg_sync_state",
        sa.Column("pass_name", sa.String(length=64), nullable=False),
        sa.Column("next_page", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("requests_used_this_run", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("pass_name"),
    )
    op.create_table(
        "rawg_seen_games",
        sa.Column("rawg_id", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source_pass", sa.String(length=64), nullable=True),
        sa.Column("times_seen", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recheck_after", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("rawg_id"),
    )
    op.create_index(op.f("ix_rawg_seen_games_recheck_after"), "rawg_seen_games", ["recheck_after"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rawg_seen_games_recheck_after"), table_name="rawg_seen_games")
    op.drop_table("rawg_seen_games")
    op.drop_table("rawg_sync_state")
