"""add ai picks recommendation fields

Revision ID: 8a6f9b3d2c11
Revises: 1f2a3b4c5d6e
Create Date: 2026-05-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a6f9b3d2c11"
down_revision: Union[str, None] = "1f2a3b4c5d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


recommendation_kind_enum = sa.Enum("cosine", "ai_picks", name="recommendationkind")
recommendation_status_enum = sa.Enum("pending", "ready", "failed", name="recommendationstatus")


def upgrade() -> None:
    bind = op.get_bind()
    recommendation_kind_enum.create(bind, checkfirst=True)
    recommendation_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "recommendations",
        sa.Column(
            "kind",
            recommendation_kind_enum,
            nullable=False,
            server_default="cosine",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "status",
            recommendation_status_enum,
            nullable=False,
            server_default="ready",
        ),
    )
    op.add_column("recommendations", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("recommendations", sa.Column("model_name", sa.String(length=120), nullable=True))
    op.add_column("recommendation_items", sa.Column("because_you_liked", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendation_items", "because_you_liked")
    op.drop_column("recommendations", "model_name")
    op.drop_column("recommendations", "summary")
    op.drop_column("recommendations", "status")
    op.drop_column("recommendations", "kind")

    bind = op.get_bind()
    recommendation_status_enum.drop(bind, checkfirst=True)
    recommendation_kind_enum.drop(bind, checkfirst=True)
