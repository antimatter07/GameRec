from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Recommendation(Base):
    """A batch of recommendations generated for a user at a point in time."""
    __tablename__ = "recommendations"

    id:               Mapped[int]      = mapped_column(primary_key=True)
    user_id:          Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at:     Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # TODO: Snapshot the taste profile used for this batch so history stays
    #       meaningful even if the user's library changes later
    profile_snapshot: Mapped[dict]     = mapped_column(JSON, nullable=True)

    user  = relationship("User",               back_populates="recommendations")
    items = relationship("RecommendationItem", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationItem(Base):
    """A single game within a recommendation batch."""
    __tablename__ = "recommendation_items"

    id:                Mapped[int]   = mapped_column(primary_key=True)
    recommendation_id: Mapped[int]   = mapped_column(Integer, ForeignKey("recommendations.id"), nullable=False)
    game_id:           Mapped[int]   = mapped_column(Integer, ForeignKey("games.id"),           nullable=False)
    rank:              Mapped[int]   = mapped_column(Integer, nullable=False)
    score:             Mapped[float] = mapped_column(Float,   nullable=False)  # cosine similarity 0–1

    # Premium only — populated by ai_service.generate_explanations()
    # TODO: For basic users leave these null; populate for premium via Celery task
    explanation: Mapped[str]   = mapped_column(Text,  nullable=True)
    confidence:  Mapped[float] = mapped_column(Float, nullable=True)  # LLM confidence 0–1

    recommendation = relationship("Recommendation",        back_populates="items")
    game           = relationship("Game",                  back_populates="recommendation_items")
    feedback       = relationship("RecommendationFeedback", back_populates="item", uselist=False)


class RecommendationFeedback(Base):
    """User thumbs-up / thumbs-down on a recommendation item."""
    __tablename__ = "recommendation_feedback"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    item_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("recommendation_items.id"), nullable=False)
    is_helpful: Mapped[bool]     = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    item = relationship("RecommendationItem", back_populates="feedback")

    # TODO: Add user_id FK here if you want to cross-reference which user submitted feedback
    #       (currently implied through item -> recommendation -> user)
