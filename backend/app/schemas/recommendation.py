from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.game import GameListOut


class RecommendationItemOut(BaseModel):
    rank:        int
    score:       float        # cosine similarity 0–1, shown as match %
    game:        GameListOut
    explanation: str | None   # None for basic users, LLM text for premium
    confidence:  float | None # None for basic users

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    id:           int
    generated_at: datetime
    items:        list[RecommendationItemOut]

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    item_id:    int
    is_helpful: bool


# --- Premium-only schemas ---

class GameDNAOut(BaseModel):
    """
    Taste profile analysis for premium users.
    TODO: Finalize the exact shape once ai_service.generate_game_dna() is implemented.
    """
    top_genres:  list[dict]  # [{"name": "RPG", "weight": 0.42}, ...]
    top_tags:    list[dict]  # [{"name": "Open World", "weight": 0.38}, ...]
    preferred_era: str | None  # e.g. "2000s – early 2010s"
    description: str           # LLM-generated "gaming identity" paragraph
    confidence:  float | None  # LLM confidence in the analysis
