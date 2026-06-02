import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Enum values.

    Returns SQLAlchemy enum values using the enum value strings stored in the database.

    Args:
        enum_cls: enum cls value used by the operation.

    Returns:
        List of serialized response objects."""
    return [member.value for member in enum_cls]


class RecommendationKind(str, enum.Enum):
    """Recommendation feed categories supported by the backend."""
    COSINE = "cosine"
    AI_PICKS = "ai_picks"


class RecommendationStatus(str, enum.Enum):
    """Lifecycle states for asynchronous recommendation batches."""
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class Recommendation(Base):
    """Recommendation batch header for cosine and AI-generated recommendation feeds."""
    __tablename__ = "recommendations"

    id:               Mapped[int]      = mapped_column(primary_key=True)
    user_id:          Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at:     Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    kind:             Mapped[RecommendationKind] = mapped_column(
        Enum(RecommendationKind, values_callable=_enum_values),
        nullable=False,
        default=RecommendationKind.COSINE,
        server_default=RecommendationKind.COSINE.value,
    )
    status:           Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, values_callable=_enum_values),
        nullable=False,
        default=RecommendationStatus.READY,
        server_default=RecommendationStatus.READY.value,
    )
    summary:          Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name:       Mapped[str | None] = mapped_column(String(120), nullable=True)

    # TODO: Snapshot the taste profile used for this batch so history stays
    #       meaningful even if the user's library changes later
    profile_snapshot: Mapped[dict]     = mapped_column(JSON, nullable=True)

    user  = relationship("User",               back_populates="recommendations")
    items = relationship("RecommendationItem", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationItem(Base):
    """Ranked game inside a recommendation batch with score and optional explanation."""
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
    because_you_liked: Mapped[list | None] = mapped_column(JSON, nullable=True)

    recommendation = relationship("Recommendation",        back_populates="items")
    game           = relationship("Game",                  back_populates="recommendation_items")
    feedback       = relationship("RecommendationFeedback", back_populates="item", uselist=False)


class RecommendationFeedback(Base):
    """User feedback attached to a recommendation item for future scoring adjustments."""
    __tablename__ = "recommendation_feedback"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    item_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("recommendation_items.id"), nullable=False)
    is_helpful: Mapped[bool]     = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    item = relationship("RecommendationItem", back_populates="feedback")

    # TODO: Add user_id FK here if you want to cross-reference which user submitted feedback
    #       (currently implied through item -> recommendation -> user)
