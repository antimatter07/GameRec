from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QueueSuggestion(Base):
    __tablename__ = "queue_suggestions"

    id:                  Mapped[int] = mapped_column(primary_key=True)
    user_id:             Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    queue_fingerprint:   Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status:              Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    trigger_source:      Mapped[str] = mapped_column(String(64), nullable=False, default="queue_tab")
    requested_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_at:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    model_name:          Mapped[str | None] = mapped_column(String(120), nullable=True)
    overall_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail:        Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="queue_suggestions")
    items = relationship("QueueSuggestionItem", back_populates="suggestion", cascade="all, delete-orphan")


class QueueSuggestionItem(Base):
    __tablename__ = "queue_suggestion_items"

    id:                 Mapped[int] = mapped_column(primary_key=True)
    suggestion_id:      Mapped[int] = mapped_column(Integer, ForeignKey("queue_suggestions.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_id:           Mapped[int] = mapped_column(Integer, ForeignKey("library_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    original_position:  Mapped[int] = mapped_column(Integer, nullable=False)
    suggested_position: Mapped[int] = mapped_column(Integer, nullable=False)
    reason:             Mapped[str] = mapped_column(Text, nullable=False)

    suggestion = relationship("QueueSuggestion", back_populates="items")
    entry = relationship("LibraryEntry", back_populates="queue_suggestion_items")
