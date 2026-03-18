from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_basic, require_premium
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import GameDNAOut, RecommendationOut
from app.services import recommendation_service

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
    try:
        recommendation = recommendation_service.get_or_generate(current_user.id, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Eagerly load items and their games so the response serialiser can access them.
    recommendation = (
        db.query(Recommendation)
        .options(
            joinedload(Recommendation.items).joinedload("game")
        )
        .filter(Recommendation.id == recommendation.id)
        .one()
    )

    return recommendation


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
