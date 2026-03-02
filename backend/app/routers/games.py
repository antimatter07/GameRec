from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.game import GameOut, PaginatedGames

router = APIRouter()


@router.get("/", response_model=PaginatedGames)
def list_games(
    request: Request,
    page:       int        = Query(1,    ge=1),
    page_size:  int        = Query(20,   ge=1, le=100),
    search:     str | None = Query(None, description="Full-text search on game name"),
    genre:      str | None = Query(None, description="Filter by genre name"),
    platform:   str | None = Query(None, description="Filter by platform name"),
    year:       int | None = Query(None, description="Filter by release year"),
    min_rating: float | None = Query(None, ge=0, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Apply per-role rate limit via @limiter.limit(get_rate_limit(current_user.role))
    #       SlowAPI decorator can't access current_user easily; consider middleware or
    #       a manual check using core.rate_limiter.get_rate_limit()
    # TODO: Call game_service.list_games(db, page, page_size, search, genre, platform, year, min_rating)
    raise NotImplementedError


@router.get("/{game_id}", response_model=GameOut)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Call game_service.get_game_by_id(db, game_id)
    # TODO: Raise HTTP 404 if not found
    raise NotImplementedError
