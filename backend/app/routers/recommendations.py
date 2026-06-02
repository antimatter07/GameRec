from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_ai_picks, require_basic, require_premium
from app.models.recommendation import Recommendation, RecommendationItem, RecommendationKind
from app.models.user import User, UserRole
from app.schemas.recommendation import AIPicksStateOut, GameDNAOut, RecommendationOut
from app.services import ai_service, recommendation_service
from app.services.ai_picks_service import get_ai_picks_state, request_ai_picks_refresh
from app.services import kv_store, task_queue

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
    """Get recommendations.

    Returns the current cosine recommendation batch and schedules premium explanations when needed.

    Args:
        genre: Optional genre filter reserved for recommendation queries. Defaults to Query(None).
        platform: Optional platform filter reserved for recommendation queries. Defaults to Query(None).
        release_year: Optional release-year filter reserved for recommendation queries. Defaults to Query(None).
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_basic).

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        HTTPException: When the request cannot be authorized, validated, or completed."""
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
        .filter(
            Recommendation.id == recommendation.id,
            Recommendation.kind == RecommendationKind.COSINE,
        )
        .one()
    )

    # For premium users: dispatch AI explanation task if items lack explanations.
    if current_user.role in (UserRole.PREMIUM, UserRole.ADMIN):
        needs_explanations = any(item.explanation is None for item in recommendation.items)
        if needs_explanations:
            try:
                task_queue.enqueue_ai_explanations(recommendation.id)
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
    """Get recommendation history.

    Returns prior cosine recommendation batches for the current user.

    Args:
        page: One-based page number to return. Defaults to 1.
        page_size: Maximum number of records to return per page. Defaults to Query(10, ge=1, le=50).
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_basic).

    Returns:
        Serialized response object or task result produced by the operation."""
    offset = (page - 1) * page_size
    recommendations = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.items).joinedload(RecommendationItem.game))
        .filter(
            Recommendation.user_id == current_user.id,
            Recommendation.kind == RecommendationKind.COSINE,
        )
        .order_by(Recommendation.generated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return recommendations


@router.get("/ai-picks", response_model=AIPicksStateOut)
def get_ai_picks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ai_picks),
):
    """Get ai picks.

    Returns the current state of the premium AI Picks feed.

    Args:
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_ai_picks).

    Returns:
        Serialized response object or task result produced by the operation."""
    return get_ai_picks_state(current_user.id, db)


@router.post("/ai-picks/refresh", response_model=AIPicksStateOut, status_code=status.HTTP_202_ACCEPTED)
def refresh_ai_picks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ai_picks),
):
    """Refresh ai picks.

    Requests a fresh AI Picks batch and enqueues generation when a pending row is created.

    Args:
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_ai_picks).

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        HTTPException: When the request cannot be authorized, validated, or completed."""
    try:
        recommendation, should_enqueue = request_ai_picks_refresh(current_user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    if should_enqueue and recommendation.status.value == "pending":
        try:
            task_queue.enqueue_ai_picks(recommendation.id, current_user.id)
        except Exception:
            pass

    return get_ai_picks_state(current_user.id, db)


@router.get("/game-dna", response_model=GameDNAOut)
def get_game_dna(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Get game DNA.

    Returns the premium Game DNA summary, using the key-value store as a short-lived cache.

    Args:
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_premium).

    Returns:
        Serialized response object or task result produced by the operation."""
    # Check Redis cache first
    cache_key = f"game_dna:{current_user.id}"
    try:
        cached = kv_store.get_json(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    dna = ai_service.generate_game_dna(current_user, db)

    # Cache for 1 hour (invalidated on library changes via precompute_for_user)
    try:
        kv_store.set_json(cache_key, dna, ttl_seconds=3600)
    except Exception:
        pass

    return dna
