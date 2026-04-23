"""add emotions to session_logs and create game_ratings table

Revision ID: a8b9c0d1e2f3
Revises: f3c9d2e7a841
Create Date: 2026-04-23 00:00:00.000000

Adds JSONB emotions column to session_logs so each session can store up to 5
emotion tags. Also creates the game_ratings table for per-axis game ratings
(story/gameplay/visuals/soundtrack/overall).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a8b9c0d1e2f3'
down_revision: Union[str, None] = 'f3c9d2e7a841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('session_logs', sa.Column('emotions', postgresql.JSONB(), nullable=True))

    op.create_table(
        'game_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('library_entry_id', sa.Integer(), nullable=True),
        sa.Column('story',     sa.Float(), nullable=True),
        sa.Column('gameplay',  sa.Float(), nullable=True),
        sa.Column('visuals',   sa.Float(), nullable=True),
        sa.Column('soundtrack', sa.Float(), nullable=True),
        sa.Column('overall',   sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'],          ['games.id'],           ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['library_entry_id'], ['library_entries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'],          ['users.id'],           ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'game_id', name='uq_game_ratings_user_game'),
    )
    op.create_index('ix_game_ratings_user_id', 'game_ratings', ['user_id'])
    op.create_index('ix_game_ratings_game_id', 'game_ratings', ['game_id'])


def downgrade() -> None:
    op.drop_index('ix_game_ratings_game_id', table_name='game_ratings')
    op.drop_index('ix_game_ratings_user_id', table_name='game_ratings')
    op.drop_table('game_ratings')
    op.drop_column('session_logs', 'emotions')
