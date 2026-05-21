"""add steam library import metadata

Revision ID: b2c4d6e8f901
Revises: 9c1d2e3f4a5b
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c4d6e8f901"
down_revision: Union[str, None] = "9c1d2e3f4a5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_external_ids",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_game_external_provider_id"),
    )
    op.create_index(op.f("ix_game_external_ids_game_id"), "game_external_ids", ["game_id"], unique=False)
    op.create_index(op.f("ix_game_external_ids_provider"), "game_external_ids", ["provider"], unique=False)
    op.create_index(op.f("ix_game_external_ids_external_id"), "game_external_ids", ["external_id"], unique=False)

    op.add_column("library_entries", sa.Column("steam_app_id", sa.Integer(), nullable=True))
    op.add_column("library_entries", sa.Column("steam_playtime_forever_minutes", sa.Integer(), nullable=True))
    op.add_column("library_entries", sa.Column("steam_playtime_2weeks_minutes", sa.Integer(), nullable=True))
    op.add_column("library_entries", sa.Column("steam_last_played_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("library_entries", sa.Column("steam_imported_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("library_entries", sa.Column("steam_import_name", sa.String(length=255), nullable=True))
    op.add_column("library_entries", sa.Column("steam_match_confidence", sa.Float(), nullable=True))
    op.create_index(op.f("ix_library_entries_steam_app_id"), "library_entries", ["steam_app_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_library_entries_steam_app_id"), table_name="library_entries")
    op.drop_column("library_entries", "steam_match_confidence")
    op.drop_column("library_entries", "steam_import_name")
    op.drop_column("library_entries", "steam_imported_at")
    op.drop_column("library_entries", "steam_last_played_at")
    op.drop_column("library_entries", "steam_playtime_2weeks_minutes")
    op.drop_column("library_entries", "steam_playtime_forever_minutes")
    op.drop_column("library_entries", "steam_app_id")

    op.drop_index(op.f("ix_game_external_ids_external_id"), table_name="game_external_ids")
    op.drop_index(op.f("ix_game_external_ids_provider"), table_name="game_external_ids")
    op.drop_index(op.f("ix_game_external_ids_game_id"), table_name="game_external_ids")
    op.drop_table("game_external_ids")
