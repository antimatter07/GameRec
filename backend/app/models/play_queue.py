from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlayQueueEntry(Base):
    """Ordered play queue entry linking a user, library entry, and game."""
    __tablename__ = "play_queue_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_id", name="uq_queue_user_entry"),
        UniqueConstraint("user_id", "position", name="uq_queue_user_position"),
    )

    id:       Mapped[int]      = mapped_column(primary_key=True)
    user_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_id: Mapped[int]      = mapped_column(Integer, ForeignKey("library_entries.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int]      = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user  = relationship("User",         back_populates="play_queue_entries")
    entry = relationship("LibraryEntry", back_populates="play_queue_entry")

    def __repr__(self) -> str:
        """Repr.

        Delegates the request to the appropriate service layer and returns the serialized response.

        Returns:
            String value produced by the operation."""
        return f"<PlayQueueEntry user={self.user_id} entry={self.entry_id} pos={self.position}>"
