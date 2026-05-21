from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionLog(Base):
    __tablename__ = "session_logs"

    id:               Mapped[int]            = mapped_column(primary_key=True)
    user_id:          Mapped[int]            = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    game_id:          Mapped[int]            = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    library_entry_id: Mapped[int | None]     = mapped_column(
        Integer, ForeignKey("library_entries.id", ondelete="SET NULL"), nullable=True
    )
    started_at:       Mapped[datetime]       = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ended_at:         Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[int | None]     = mapped_column(Integer, nullable=True)
    notes:            Mapped[str | None]     = mapped_column(Text, nullable=True)
    is_milestone:     Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    milestone_label:  Mapped[str | None]     = mapped_column(String(255), nullable=True)
    emotions:         Mapped[list | None]    = mapped_column(JSONB, nullable=True)
    created_at:       Mapped[datetime]       = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at:       Mapped[datetime]       = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user          = relationship("User", back_populates="session_logs")
    game          = relationship("Game")
    library_entry = relationship("LibraryEntry")

    def __repr__(self) -> str:
        return f"<SessionLog id={self.id} user={self.user_id} game={self.game_id}>"


class GameRating(Base):
    __tablename__ = "game_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_game_ratings_user_game"),
    )

    id:               Mapped[int]         = mapped_column(primary_key=True)
    user_id:          Mapped[int]         = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    game_id:          Mapped[int]         = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    library_entry_id: Mapped[int | None]  = mapped_column(
        Integer, ForeignKey("library_entries.id", ondelete="SET NULL"), nullable=True
    )
    story:            Mapped[float | None] = mapped_column(Float, nullable=True)
    gameplay:         Mapped[float | None] = mapped_column(Float, nullable=True)
    visuals:          Mapped[float | None] = mapped_column(Float, nullable=True)
    soundtrack:       Mapped[float | None] = mapped_column(Float, nullable=True)
    overall:          Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at:       Mapped[datetime]    = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at:       Mapped[datetime]    = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    game = relationship("Game")

    def __repr__(self) -> str:
        return f"<GameRating id={self.id} user={self.user_id} game={self.game_id}>"
