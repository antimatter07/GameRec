from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id:               Mapped[int]      = mapped_column(primary_key=True)
    rawg_id:          Mapped[int]      = mapped_column(Integer, unique=True, nullable=False, index=True)
    name:             Mapped[str]      = mapped_column(String(255), nullable=False, index=True)
    slug:             Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    description:      Mapped[str]      = mapped_column(Text,    nullable=True)
    released:         Mapped[date]     = mapped_column(Date,    nullable=True)
    background_image: Mapped[str]      = mapped_column(String(500), nullable=True)
    rating:           Mapped[float]    = mapped_column(Float,   nullable=True)
    ratings_count:    Mapped[int]      = mapped_column(Integer, default=0)
    metacritic:       Mapped[int]      = mapped_column(Integer, nullable=True)

    # Stored as JSON arrays; each element is a dict e.g. {"id": 4, "name": "Action"}
    # TODO: For advanced filtering, consider normalizing these into junction tables
    #       and using PostgreSQL GIN indexes on the JSONB columns in the meantime.
    genres:      Mapped[list] = mapped_column(JSON, default=list)
    platforms:   Mapped[list] = mapped_column(JSON, default=list)
    tags:        Mapped[list] = mapped_column(JSON, default=list)
    screenshots: Mapped[list] = mapped_column(JSON, default=list)

    # Pre-computed L2-normalized feature vector for content-based filtering.
    # Concatenation of: multi-hot genres | multi-hot top-150 tags | metacritic/100 | rating/5
    feature_vector: Mapped[Optional[list[float]]] = mapped_column(JSON, nullable=True)

    playtime: Mapped[int] = mapped_column(Integer, nullable=True)

    synced_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    library_entries  = relationship("LibraryEntry",       back_populates="game")
    recommendation_items = relationship("RecommendationItem", back_populates="game")

    def __repr__(self) -> str:
        return f"<Game id={self.id} name={self.name!r}>"
