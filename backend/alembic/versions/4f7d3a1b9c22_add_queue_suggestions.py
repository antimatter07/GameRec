"""add queue suggestions

Revision ID: 4f7d3a1b9c22
Revises: 8a6f9b3d2c11
Create Date: 2026-05-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f7d3a1b9c22"
down_revision: Union[str, None] = "8a6f9b3d2c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "queue_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("queue_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("trigger_source", sa.String(length=64), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("overall_explanation", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queue_suggestions_user_id"), "queue_suggestions", ["user_id"], unique=False)
    op.create_index(op.f("ix_queue_suggestions_queue_fingerprint"), "queue_suggestions", ["queue_fingerprint"], unique=False)

    op.create_table(
        "queue_suggestion_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("suggestion_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("original_position", sa.Integer(), nullable=False),
        sa.Column("suggested_position", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["library_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suggestion_id"], ["queue_suggestions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queue_suggestion_items_entry_id"), "queue_suggestion_items", ["entry_id"], unique=False)
    op.create_index(op.f("ix_queue_suggestion_items_suggestion_id"), "queue_suggestion_items", ["suggestion_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_queue_suggestion_items_suggestion_id"), table_name="queue_suggestion_items")
    op.drop_index(op.f("ix_queue_suggestion_items_entry_id"), table_name="queue_suggestion_items")
    op.drop_table("queue_suggestion_items")
    op.drop_index(op.f("ix_queue_suggestions_queue_fingerprint"), table_name="queue_suggestions")
    op.drop_index(op.f("ix_queue_suggestions_user_id"), table_name="queue_suggestions")
    op.drop_table("queue_suggestions")
