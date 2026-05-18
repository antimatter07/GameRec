from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RawgSyncState(Base):
    __tablename__ = "rawg_sync_state"

    pass_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    next_page: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requests_used_this_run: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RawgSeenGame(Base):
    __tablename__ = "rawg_seen_games"

    rawg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_pass: Mapped[str | None] = mapped_column(String(64), nullable=True)
    times_seen: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    recheck_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
