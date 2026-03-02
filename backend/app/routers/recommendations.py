from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic, require_premium
from app.models.user import User
from app.schemas.recommendation import GameDNAOut, RecommendationOut

router = APIRouter()


@router.get("/", response_model=RecommendationOut)
def get_recommendations(
    # Premium advanced filters — ignored for basic users
    genre:        str | None = Query(None),
    platform:     str | None = Query(None),
    release_year: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Call recommendation_service.get_or_generate(db, current_user)
    # TODO: For basic users: return items with explanation=None, confidence=None
    # TODO: For premium users: apply genre/platform/release_year filters AND include
    #       LLM explanations (call ai_service.generate_explanations if not cached)
    raise NotImplementedError


@router.get("/history", response_model=list[RecommendationOut])
def get_recommendation_history(
    page:      int = Query(1,  ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Return paginated past Recommendation batches for current_user
    # TODO: Order by generated_at descending
    raise NotImplementedError


@router.get("/game-dna", response_model=GameDNAOut)
def get_game_dna(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    # TODO: Call ai_service.generate_game_dna(current_user)
    # TODO: Cache result in Redis (keyed by user_id) — invalidate on library update
    raise NotImplementedError
