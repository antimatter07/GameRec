from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_basic, require_premium
from app.models.recommendation import Recommendation, RecommendationItem
from app.models.user import User, UserRole
from app.schemas.recommendation import GameDNAOut, RecommendationOut
from app.services import ai_service, recommendation_service

router = APIRouter()


@router.get("/", response_model=RecommendationOut)
def get_recommendations(
    # Premium advanced filters — reserved for future use
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

    # Eagerly load items and their games for response serialisation.
    recommendation = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.items).joinedload(RecommendationItem.game))
        .filter(Recommendation.id == recommendation.id)
        .one()
    )

    # For premium users: dispatch AI explanation task if items lack explanations.
    if current_user.role in (UserRole.PREMIUM, UserRole.ADMIN):
        needs_explanations = any(item.explanation is None for item in recommendation.items)
        if needs_explanations:
            try:
                from app.workers.tasks.recommendation import generate_ai_explanations
                generate_ai_explanations.delay(recommendation.id)
            except Exception:
                pass  # Celery unavailable — explanations will be null for now

    return recommendation


@router.get("/history", response_model=list[RecommendationOut])
def get_recommendation_history(
    page:      int = Query(1,  ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    offset = (page - 1) * page_size
    recommendations = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.items).joinedload(RecommendationItem.game))
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.generated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return recommendations


@router.get("/game-dna", response_model=GameDNAOut)
def get_game_dna(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    # Check Redis cache first
    cache_key = f"game_dna:{current_user.id}"
    try:
        import json as _json
        import redis as redis_lib
        from app.config import settings

        r = redis_lib.from_url(settings.REDIS_URL)
        cached = r.get(cache_key)
        if cached:
            return _json.loads(cached)
    except Exception:
        pass

    dna = ai_service.generate_game_dna(current_user, db)

    # Cache for 1 hour (invalidated on library changes via precompute_for_user)
    try:
        import json as _json
        r.setex(cache_key, 3600, _json.dumps(dna))
    except Exception:
        pass

    return dna
