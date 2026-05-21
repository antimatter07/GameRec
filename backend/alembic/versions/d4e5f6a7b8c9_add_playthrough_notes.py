"""add playthrough notes

Revision ID: d4e5f6a7b8c9
Revises: b2c4d6e8f901
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "b2c4d6e8f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playthrough_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("library_entry_id", sa.Integer(), nullable=True),
        sa.Column("session_log_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remind_next_session", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["library_entry_id"], ["library_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_playthrough_notes_game_id"), "playthrough_notes", ["game_id"], unique=False)
    op.create_index(op.f("ix_playthrough_notes_remind_next_session"), "playthrough_notes", ["remind_next_session"], unique=False)
    op.create_index(op.f("ix_playthrough_notes_session_log_id"), "playthrough_notes", ["session_log_id"], unique=False)
    op.create_index(op.f("ix_playthrough_notes_status"), "playthrough_notes", ["status"], unique=False)
    op.create_index(op.f("ix_playthrough_notes_user_id"), "playthrough_notes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_playthrough_notes_user_id"), table_name="playthrough_notes")
    op.drop_index(op.f("ix_playthrough_notes_status"), table_name="playthrough_notes")
    op.drop_index(op.f("ix_playthrough_notes_session_log_id"), table_name="playthrough_notes")
    op.drop_index(op.f("ix_playthrough_notes_remind_next_session"), table_name="playthrough_notes")
    op.drop_index(op.f("ix_playthrough_notes_game_id"), table_name="playthrough_notes")
    op.drop_table("playthrough_notes")
