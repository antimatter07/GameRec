from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GameExternalId(Base):
    """External provider identifier associated with a local game record."""
    __tablename__ = "game_external_ids"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_game_external_provider_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    game = relationship("Game", back_populates="external_ids")
