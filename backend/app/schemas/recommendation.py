from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.game import GameListOut


class RecommendationItemOut(BaseModel):
    """Response schema for one ranked recommendation item."""
    id:          int
    rank:        int
    score:       float        # cosine similarity 0–1, shown as match %
    game:        GameListOut
    explanation: str | None   # None for basic users, LLM text for premium
    confidence:  float | None # None for basic users
    because_you_liked: list[str] | None = None

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    """Response schema for a recommendation batch with ranked items."""
    id:           int
    generated_at: datetime
    kind:         str
    status:       str
    summary:      str | None = None
    model_name:   str | None = None
    items:        list[RecommendationItemOut]

    model_config = {"from_attributes": True}


class AIPicksStateOut(BaseModel):
    """Response schema for the current AI Picks lifecycle state."""
    recommendation: RecommendationOut | None
    is_stale: bool
    can_refresh: bool
    cache_hours: int
    detail: str | None = None


class FeedbackCreate(BaseModel):
    """Request schema for recommendation helpfulness feedback."""
    item_id:    int
    is_helpful: bool


# --- Premium-only schemas ---

class GameDNAOut(BaseModel):
    """Response schema for premium Game DNA summary data."""
    top_genres:  list[dict]  # [{"name": "RPG", "weight": 0.42}, ...]
    top_tags:    list[dict]  # [{"name": "Open World", "weight": 0.38}, ...]
    preferred_era: str | None  # e.g. "2000s – early 2010s"
    description: str           # LLM-generated "gaming identity" paragraph
    confidence:  float | None  # LLM confidence in the analysis
