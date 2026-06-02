import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LibraryStatus(str, enum.Enum):
    """Allowed lifecycle states for a user library entry."""
    PLAYING   = "playing"
    COMPLETED = "completed"
    BACKLOG   = "backlog"
    DROPPED   = "dropped"
    WISHLIST  = "wishlist"
    REPLAYING = "replaying"


class LibraryEntry(Base):
    """Join model connecting a user to a game with status, rating, and tracking metadata."""
    __tablename__ = "library_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game"),
    )

    id:         Mapped[int]           = mapped_column(primary_key=True)
    user_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    game_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("games.id"), nullable=False)
    status:     Mapped[LibraryStatus] = mapped_column(Enum(LibraryStatus), default=LibraryStatus.BACKLOG)
    rating:     Mapped[float]         = mapped_column(Float, nullable=True)   # 1–5 stars
    review:     Mapped[str]           = mapped_column(Text,  nullable=True)
    steam_app_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    steam_playtime_forever_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steam_playtime_2weeks_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steam_last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    steam_imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    steam_import_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    steam_match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    added_at:   Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime]      = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="library_entries")
    game = relationship("Game", back_populates="library_entries")
    play_queue_entry = relationship("PlayQueueEntry", back_populates="entry", uselist=False, cascade="all, delete-orphan")
    queue_suggestion_items = relationship("QueueSuggestionItem", back_populates="entry", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Repr.

        Delegates the request to the appropriate service layer and returns the serialized response.

        Returns:
            String value produced by the operation."""
        return f"<LibraryEntry user={self.user_id} game={self.game_id} status={self.status}>"
