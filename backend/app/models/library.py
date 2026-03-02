import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LibraryStatus(str, enum.Enum):
    PLAYING   = "playing"
    COMPLETED = "completed"
    BACKLOG   = "backlog"
    DROPPED   = "dropped"


class LibraryEntry(Base):
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
    added_at:   Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime]      = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="library_entries")
    game = relationship("Game", back_populates="library_entries")

    def __repr__(self) -> str:
        return f"<LibraryEntry user={self.user_id} game={self.game_id} status={self.status}>"
