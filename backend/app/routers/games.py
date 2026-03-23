from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.game import GameOut, PaginatedGames
from app.services import game_service

router = APIRouter()


# TODO: Re-add `current_user after auth is implemented: (User = Depends(require_basic))
@router.get("/", response_model=PaginatedGames)
def list_games(
    page:       int        = Query(1,   ge=1),
    page_size:  int        = Query(20,  ge=1, le=100),
    search:     str | None = Query(None),
    genre:      str | None = Query(None),
    platform:   str | None = Query(None),
    year:       int | None = Query(None),
    min_rating: float | None = Query(None, ge=0, le=5),
    db: Session = Depends(get_db),
):
    return game_service.list_games(db, page, page_size, search, genre, platform, year, min_rating)


# TODO: Re-add `current_user after auth is implemented: (User = Depends(require_basic))
@router.get("/{game_id}", response_model=GameOut)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
):
    return game_service.get_game_by_id(db, game_id)
