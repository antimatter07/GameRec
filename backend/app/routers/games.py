from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.game import GameOut, PaginatedGames
from app.services import game_service

router = APIRouter()


@router.get("/", response_model=PaginatedGames)
def list_games(
    page:       int        = Query(1,   ge=1),
    page_size:  int        = Query(20,  ge=1, le=100),
    search:     str | None = Query(None),
    genre:      str | None = Query(None),
    platform:   str | None = Query(None),
    year:       int | None = Query(None),
    min_rating: float | None = Query(None, ge=0, le=5),
    max_hours:  int | None = Query(None, ge=1),
    library_state: Literal["all", "saved", "not_saved"] = Query("all"),
    sort: Literal["rating_desc", "released_desc", "name_asc", "playtime_asc"] = Query("rating_desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    return game_service.list_games(
        db,
        current_user.id,
        page,
        page_size,
        search,
        genre,
        platform,
        year,
        min_rating,
        max_hours,
        library_state,
        sort,
    )


@router.get("/{game_id}", response_model=GameOut)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    return game_service.get_game_by_id(db, game_id)
